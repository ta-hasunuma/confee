import type { SuggestedPrompt } from "../types";

interface Props {
  prompts: SuggestedPrompt[];
  onSelect: (prompt: string) => void;
  disabled: boolean;
}

export function SuggestedPrompts({ prompts, onSelect, disabled }: Props) {
  return (
    <div className="flex flex-wrap gap-2 px-4 py-2">
      {prompts.map((p) => (
        <button
          key={p.id}
          onClick={() => onSelect(p.prompt)}
          disabled={disabled}
          className="rounded-full border border-gray-300 bg-white px-4 py-2 text-base text-gray-700 hover:bg-gray-100 hover:border-gray-400 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {p.label}
        </button>
      ))}
    </div>
  );
}
