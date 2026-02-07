import { useState, type FormEvent } from "react";

interface Props {
  onSend: (message: string) => void;
  disabled: boolean;
}

export function ChatInput({ onSend, disabled }: Props) {
  const [text, setText] = useState("");

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    const trimmed = text.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setText("");
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="border-t border-cafe-200 bg-white p-4"
    >
      <div className="flex gap-2">
        <input
          type="text"
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="カンファレンスについて質問してみましょう..."
          disabled={disabled}
          className="flex-1 rounded-full border border-cafe-300 bg-cafe-50 px-5 py-3 text-base text-cafe-900 placeholder:text-cafe-400 focus:outline-none focus:ring-2 focus:ring-cafe-500 focus:border-transparent disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={disabled || !text.trim()}
          className="rounded-full bg-cafe-700 px-6 py-3 text-base text-white font-medium hover:bg-cafe-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-sm"
        >
          送信
        </button>
      </div>
    </form>
  );
}
