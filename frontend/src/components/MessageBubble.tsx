import Markdown from "react-markdown";
import type { ChatMessage } from "../types";

interface Props {
  message: ChatMessage;
}

export function MessageBubble({ message }: Props) {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`rounded-2xl px-5 py-3.5 max-w-[80%] whitespace-pre-wrap break-words shadow-sm ${
          isUser
            ? "bg-cafe-700 text-white rounded-br-sm"
            : "bg-white text-cafe-900 rounded-bl-sm border border-cafe-200"
        }`}
      >
        {isUser ? (
          <p className="text-base">{message.content}</p>
        ) : (
          <div className="prose prose-base max-w-none [&_a]:text-cafe-600 [&_a]:underline">
            <Markdown>{message.content}</Markdown>
          </div>
        )}
      </div>
    </div>
  );
}
