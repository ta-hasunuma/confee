import { useCallback, useRef, useState } from "react";
import type { ChatMessage } from "../types";
import { ChatApiError, generateSessionId, sendMessage } from "../api/chat";
import { suggestedPrompts } from "../data/suggestedPrompts";
import { MessageList } from "./MessageList";
import { ChatInput } from "./ChatInput";
import { SuggestedPrompts } from "./SuggestedPrompts";

interface Props {
  sessionKey: number;
}

function getErrorMessage(err: unknown): string {
  // ネットワーク接続エラー（fetch失敗）
  if (err instanceof TypeError && err.message.includes("fetch")) {
    return "サーバーに接続できませんでした。ネットワーク接続を確認して、もう一度お試しください。";
  }

  // タイムアウト（AbortError）
  if (err instanceof DOMException && err.name === "AbortError") {
    return "応答がタイムアウトしました。しばらく待ってからもう一度お試しください。";
  }

  // HTTP ステータスコード別エラー
  if (err instanceof ChatApiError) {
    if (err.status === 503) {
      return "サービスが一時的に利用できません。しばらく待ってからもう一度お試しください。";
    }
    if (err.status === 408) {
      return "セッションがタイムアウトしました。新しいセッションで再接続します。もう一度お試しください。";
    }
    return `エラーが発生しました: ${err.message}\n\nもう一度お試しください。`;
  }

  // その他
  const text = err instanceof Error ? err.message : "予期しないエラーが発生しました";
  return `エラーが発生しました: ${text}\n\nもう一度お試しください。`;
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
      // セッションタイムアウト時は新しいセッションIDを生成
      if (err instanceof ChatApiError && err.status === 408) {
        sessionIdRef.current = generateSessionId();
      }

      const errorMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: getErrorMessage(err),
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const hasMessages = messages.length > 0;

  return (
    <div className="flex flex-col h-full">
      {!hasMessages && !isLoading ? (
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
        visible={!hasMessages}
      />
      <ChatInput onSend={handleSend} disabled={isLoading} />
    </div>
  );
}
