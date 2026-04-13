"use client";

import type { Message } from "@/types/chat";
import { MessageBubble } from "@/components/chat/MessageBubble";
import { ChatInput } from "@/components/chat/ChatInput";

interface ChatPanelProps {
  messages: Message[];
  onSend: (message: string) => void;
  isStreaming: boolean;
}

export function ChatPanel({ messages, onSend, isStreaming }: ChatPanelProps) {
  return (
    <div className="flex flex-1 flex-col">
      <div className="border-b border-gray-200 px-6 py-4">
        <h2 className="text-lg font-semibold">Discovery Chat</h2>
      </div>
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.length === 0 && (
          <p className="text-center text-gray-400 mt-8">
            Start a conversation to discover products
          </p>
        )}
        {messages.map((message, index) => (
          <MessageBubble key={index} message={message} />
        ))}
      </div>
      <ChatInput onSend={onSend} disabled={isStreaming} />
    </div>
  );
}
