import { useCallback, useRef, useState } from "react";
import type { ChatMessage } from "../types";
import { generateSessionId, sendMessage } from "../api/chat";
import { suggestedPrompts } from "../data/suggestedPrompts";
import { MessageList } from "./MessageList";
import { ChatInput } from "./ChatInput";
import { SuggestedPrompts } from "./SuggestedPrompts";

interface Props {
  sessionKey: number;
}

export function ChatContainer({ sessionKey }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const sessionIdRef = useRef(generateSessionId());

  // sessionKey が変わったらセッションをリセット
  const prevKeyRef = useRef(sessionKey);
  if (prevKeyRef.current !== sessionKey) {
    prevKeyRef.current = sessionKey;
    setMessages([]);
    setIsLoading(false);
    sessionIdRef.current = generateSessionId();
  }

  const handleSend = useCallback(async (text: string) => {
    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: text,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const data = await sendMessage(text, sessionIdRef.current);
      sessionIdRef.current = data.session_id;

      const assistantMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: data.response,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      const errorText =
        err instanceof Error ? err.message : "予期しないエラーが発生しました";

      const errorMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: `エラーが発生しました: ${errorText}\n\nもう一度お試しください。`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  return (
    <div className="flex flex-col h-full">
      {messages.length === 0 && !isLoading ? (
        <div className="flex-1 flex items-center justify-center p-8">
          <div className="text-center">
            <img
              src="/image.png"
              alt="confee"
              className="w-24 h-24 mx-auto mb-6 rounded-2xl shadow-lg"
            />
            <h2 className="text-2xl font-semibold text-cafe-800 mb-2">
              Confee へようこそ
            </h2>
            <p className="text-base text-cafe-500">
              技術カンファレンスについて質問してみましょう
            </p>
          </div>
        </div>
      ) : (
        <MessageList messages={messages} isLoading={isLoading} />
      )}
      <SuggestedPrompts
        prompts={suggestedPrompts}
        onSelect={handleSend}
        disabled={isLoading}
      />
      <ChatInput onSend={handleSend} disabled={isLoading} />
    </div>
  );
}
