import type { Message } from "@/types/chat";
import { cn } from "@/lib/utils";

interface MessageBubbleProps {
  message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";
  return (
    <div className={cn("flex", isUser ? "justify-end" : "justify-start")}>
      <div
        className={cn(
          "max-w-[85%] rounded-[24px] border px-4 py-3 shadow-[0_18px_32px_rgba(29,42,34,0.06)]",
          isUser
            ? "border-transparent bg-[color:var(--accent)] text-white"
            : "border-[color:var(--line)] bg-[color:var(--panel)] text-[color:var(--ink)]",
        )}
      >
        <p className="mb-2 text-[11px] tracking-[0.18em] text-current/60 uppercase">
          {isUser ? "You" : "Echo"}
        </p>
        <p className="text-sm leading-relaxed whitespace-pre-wrap">
          {message.content}
        </p>
      </div>
    </div>
  );
}
