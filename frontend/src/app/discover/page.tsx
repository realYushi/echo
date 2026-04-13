"use client";

import { useState } from "react";
import { ChatPanel } from "@/components/chat/ChatPanel";
import { RecommendationGrid } from "@/components/recommendations/RecommendationGrid";
import { useChat } from "@/hooks/useChat";
import { useRecommendations } from "@/hooks/useRecommendations";

export default function DiscoverPage() {
  const [sessionId] = useState(() => crypto.randomUUID());
  const chat = useChat(sessionId);
  const recommendations = useRecommendations(sessionId);

  return (
    <div className="flex h-screen">
      <div className="flex w-1/2 flex-col border-r border-gray-200">
        <ChatPanel
          messages={chat.messages}
          onSend={chat.sendMessage}
          isStreaming={chat.isStreaming}
        />
      </div>
      <div className="w-1/2 overflow-y-auto p-6">
        <RecommendationGrid
          products={recommendations.products}
          onFeedback={() => {}}
          isLoading={recommendations.isLoading}
        />
      </div>
    </div>
  );
}
