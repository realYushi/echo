"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { fetchVoiceToken, postVoiceTranscript } from "@/lib/api";
import type { Message } from "@/types/chat";
import type { Persona } from "@/types/persona";
import type { Recommendation } from "@/types/product";
import type { TranscriptMessage } from "@/types/voice";

const GEMINI_WS_URL =
  "wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1alpha.GenerativeService.BidiGenerateContentConstrained";

const SYSTEM_INSTRUCTION =
  "You are Echo, a warm and curious design taste discovery assistant. Your goal is to understand the user's aesthetic preferences for interior design and home decor through natural conversation. Ask one question at a time. Be conversational and encouraging. Listen carefully to their responses and build on what they share. Focus on understanding their style preferences, color palettes, material preferences, and budget range.";

const CAPTURE_SAMPLE_RATE = 16000;
const PLAYBACK_SAMPLE_RATE = 24000;

interface UseVoiceChatOptions {
  onPersonaUpdate: (persona: Persona) => void;
  onRecommendationsUpdate: (recommendations: Recommendation[]) => void;
  onFallbackToText: (reason: string) => void;
}

interface UseVoiceChatReturn {
  connect: () => Promise<void>;
  disconnect: () => void;
  isConnected: boolean;
  isConnecting: boolean;
  error: string | null;
  transcripts: Message[];
}

function createMessage(role: Message["role"], content: string): Message {
  return {
    id: crypto.randomUUID(),
    role,
    content,
  };
}

function int16ToBase64(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer);
  let binary = "";
  for (let i = 0; i < bytes.length; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary);
}

function base64ToInt16(base64: string): Int16Array {
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  return new Int16Array(bytes.buffer);
}

function int16ToFloat32(int16: Int16Array): Float32Array {
  const float32 = new Float32Array(int16.length);
  for (let i = 0; i < int16.length; i++) {
    float32[i] = int16[i] / 0x7fff;
  }
  return float32;
}

function isAbortError(error: unknown): boolean {
  return error instanceof DOMException && error.name === "AbortError";
}

function getErrorMessage(error: unknown): string {
  if (error instanceof Error && error.message) {
    return error.message;
  }

  return "Voice connection failed. Please try again.";
}

export function useVoiceChat(
  sessionId: string | null,
  options: UseVoiceChatOptions,
): UseVoiceChatReturn {
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [transcripts, setTranscripts] = useState<Message[]>([]);

  const { onPersonaUpdate, onRecommendationsUpdate, onFallbackToText } =
    options;

  const wsRef = useRef<WebSocket | null>(null);
  const micStreamRef = useRef<MediaStream | null>(null);
  const captureContextRef = useRef<AudioContext | null>(null);
  const playbackContextRef = useRef<AudioContext | null>(null);
  const playerNodeRef = useRef<AudioWorkletNode | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const activeRef = useRef(false);

  const userTranscriptRef = useRef("");
  const assistantTranscriptRef = useRef("");
  const transcriptHistoryRef = useRef<TranscriptMessage[]>([]);

  const cleanup = useCallback(() => {
    activeRef.current = false;

    abortControllerRef.current?.abort();
    abortControllerRef.current = null;

    if (wsRef.current) {
      wsRef.current.onopen = null;
      wsRef.current.onmessage = null;
      wsRef.current.onerror = null;
      wsRef.current.onclose = null;
      wsRef.current.close();
      wsRef.current = null;
    }

    micStreamRef.current?.getTracks().forEach((track) => track.stop());
    micStreamRef.current = null;

    playerNodeRef.current = null;

    if (captureContextRef.current?.state !== "closed") {
      captureContextRef.current?.close();
    }
    captureContextRef.current = null;

    if (playbackContextRef.current?.state !== "closed") {
      playbackContextRef.current?.close();
    }
    playbackContextRef.current = null;

    userTranscriptRef.current = "";
    assistantTranscriptRef.current = "";

    setIsConnected(false);
    setIsConnecting(false);
  }, []);

  const sendTranscriptsToBackend = useCallback(
    async (signal?: AbortSignal) => {
      if (!sessionId) {
        return;
      }

      const userText = userTranscriptRef.current.trim();
      const assistantText = assistantTranscriptRef.current.trim();

      if (userText) {
        transcriptHistoryRef.current = [
          ...transcriptHistoryRef.current,
          { role: "user", content: userText },
        ];
      }
      if (assistantText) {
        transcriptHistoryRef.current = [
          ...transcriptHistoryRef.current,
          { role: "assistant", content: assistantText },
        ];
      }

      userTranscriptRef.current = "";
      assistantTranscriptRef.current = "";

      if (transcriptHistoryRef.current.length === 0) {
        return;
      }

      try {
        const response = await postVoiceTranscript(
          sessionId,
          transcriptHistoryRef.current,
          signal,
        );

        if (response.persona) {
          onPersonaUpdate(response.persona);
        }
        if (response.recommendations.length > 0) {
          onRecommendationsUpdate(response.recommendations);
        }
      } catch (nextError) {
        if (!isAbortError(nextError)) {
          setError(getErrorMessage(nextError));
        }
      }
    },
    [sessionId, onPersonaUpdate, onRecommendationsUpdate],
  );

  const handleServerMessage = useCallback(
    (event: MessageEvent) => {
      const data = JSON.parse(event.data as string);

      if (data.setupComplete) {
        setIsConnected(true);
        setIsConnecting(false);
        return;
      }

      if (data.serverContent) {
        const serverContent = data.serverContent;

        if (serverContent.inputTranscription?.text) {
          const text = serverContent.inputTranscription.text as string;
          userTranscriptRef.current += text;

          setTranscripts((prev) => {
            const lastMessage = prev.at(-1);
            if (lastMessage?.role === "user") {
              return [
                ...prev.slice(0, -1),
                { ...lastMessage, content: lastMessage.content + text },
              ];
            }
            return [...prev, createMessage("user", text)];
          });
        }

        if (serverContent.outputTranscription?.text) {
          const text = serverContent.outputTranscription.text as string;
          assistantTranscriptRef.current += text;

          setTranscripts((prev) => {
            const lastMessage = prev.at(-1);
            if (lastMessage?.role === "assistant") {
              return [
                ...prev.slice(0, -1),
                { ...lastMessage, content: lastMessage.content + text },
              ];
            }
            return [...prev, createMessage("assistant", text)];
          });
        }

        if (serverContent.modelTurn?.parts) {
          const parts = serverContent.modelTurn.parts as Array<{
            inlineData?: { data: string };
          }>;
          for (const part of parts) {
            if (part.inlineData?.data) {
              const int16 = base64ToInt16(part.inlineData.data);
              const float32 = int16ToFloat32(int16);
              playerNodeRef.current?.port.postMessage(float32.buffer, [
                float32.buffer,
              ]);
            }
          }
        }

        if (serverContent.turnComplete) {
          sendTranscriptsToBackend(abortControllerRef.current?.signal);
        }
      }
    },
    [sendTranscriptsToBackend],
  );

  const connect = useCallback(async () => {
    if (!sessionId || activeRef.current) {
      return;
    }

    activeRef.current = true;
    setIsConnecting(true);
    setError(null);

    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      const tokenResponse = await fetchVoiceToken(controller.signal);

      let micStream: MediaStream;
      try {
        micStream = await navigator.mediaDevices.getUserMedia({
          audio: {
            sampleRate: CAPTURE_SAMPLE_RATE,
            channelCount: 1,
            echoCancellation: true,
            noiseSuppression: true,
          },
        });
      } catch {
        onFallbackToText("Microphone access is required for voice mode.");
        cleanup();
        return;
      }

      if (controller.signal.aborted) {
        micStream.getTracks().forEach((track) => track.stop());
        return;
      }

      micStreamRef.current = micStream;

      const captureContext = new AudioContext({
        sampleRate: CAPTURE_SAMPLE_RATE,
      });
      captureContextRef.current = captureContext;

      const playbackContext = new AudioContext({
        sampleRate: PLAYBACK_SAMPLE_RATE,
      });
      playbackContextRef.current = playbackContext;

      await Promise.all([
        captureContext.audioWorklet.addModule("/worklets/pcm-processor.js"),
        playbackContext.audioWorklet.addModule("/worklets/pcm-processor.js"),
      ]);

      if (controller.signal.aborted) {
        cleanup();
        return;
      }

      const ws = new WebSocket(
        `${GEMINI_WS_URL}?access_token=${tokenResponse.token}`,
      );
      wsRef.current = ws;

      ws.onopen = () => {
        const setupMessage = {
          setup: {
            model: `models/${tokenResponse.model}`,
            generationConfig: {
              responseModalities: ["AUDIO"],
              speechConfig: {
                voiceConfig: {
                  prebuiltVoiceConfig: { voiceName: "Aoede" },
                },
              },
            },
            systemInstruction: {
              parts: [{ text: SYSTEM_INSTRUCTION }],
            },
            inputAudioTranscription: {},
            outputAudioTranscription: {},
          },
        };
        ws.send(JSON.stringify(setupMessage));

        const source = captureContext.createMediaStreamSource(micStream);
        const captureNode = new AudioWorkletNode(
          captureContext,
          "pcm-capture",
        );
        captureNode.port.onmessage = (msg: MessageEvent) => {
          if (ws.readyState === WebSocket.OPEN) {
            const base64 = int16ToBase64(msg.data as ArrayBuffer);
            ws.send(
              JSON.stringify({
                realtimeInput: {
                  mediaChunks: [
                    {
                      mimeType: "audio/pcm;rate=16000",
                      data: base64,
                    },
                  ],
                },
              }),
            );
          }
        };
        source.connect(captureNode);

        const playerNode = new AudioWorkletNode(
          playbackContext,
          "pcm-player",
        );
        playerNode.connect(playbackContext.destination);
        playerNodeRef.current = playerNode;
      };

      ws.onmessage = handleServerMessage;

      ws.onerror = () => {
        if (!activeRef.current) {
          return;
        }
        setError("Voice connection encountered an error.");
        onFallbackToText(
          "Voice connection was interrupted. Switching to text mode.",
        );
        cleanup();
      };

      ws.onclose = (event) => {
        if (!activeRef.current) {
          return;
        }
        if (event.code !== 1000) {
          onFallbackToText(
            "Voice connection was interrupted. Switching to text mode.",
          );
        }
        cleanup();
      };
    } catch (nextError) {
      if (isAbortError(nextError)) {
        return;
      }

      const message = getErrorMessage(nextError);
      setError(message);
      onFallbackToText(
        "Unable to start voice mode. Switching to text mode.",
      );
      cleanup();
    }
  }, [sessionId, onFallbackToText, cleanup, handleServerMessage]);

  const disconnect = useCallback(() => {
    cleanup();
    setTranscripts([]);
    transcriptHistoryRef.current = [];
  }, [cleanup]);

  useEffect(() => {
    return () => {
      cleanup();
    };
  }, [cleanup]);

  useEffect(() => {
    cleanup();
    setTranscripts([]);
    setError(null);
    transcriptHistoryRef.current = [];
  }, [sessionId, cleanup]);

  return {
    connect,
    disconnect,
    isConnected,
    isConnecting,
    error,
    transcripts,
  };
}
