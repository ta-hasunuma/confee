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
        className={`rounded-2xl px-4 py-3 max-w-[80%] whitespace-pre-wrap break-words ${
          isUser
            ? "bg-blue-600 text-white rounded-br-sm"
            : "bg-gray-100 text-gray-900 rounded-bl-sm"
        }`}
      >
        {isUser ? (
          <p>{message.content}</p>
        ) : (
          <div className="prose prose-base max-w-none [&_a]:text-blue-600 [&_a]:underline">
            <Markdown>{message.content}</Markdown>
          </div>
        )}
      </div>
    </div>
  );
}
