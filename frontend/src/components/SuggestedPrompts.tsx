import type { SuggestedPrompt } from "../types";

interface Props {
  prompts: SuggestedPrompt[];
  onSelect: (prompt: string) => void;
  disabled: boolean;
  visible: boolean;
}

export function SuggestedPrompts({ prompts, onSelect, disabled, visible }: Props) {
  if (!visible) return null;

  return (
    <div className="flex flex-wrap gap-2 px-4 py-2 bg-white border-t border-cafe-100">
      {prompts.map((p) => (
        <button
          key={p.id}
          onClick={() => onSelect(p.prompt)}
          disabled={disabled}
          className="rounded-full border border-cafe-300 bg-cafe-50 px-4 py-2 text-base text-cafe-700 hover:bg-cafe-100 hover:border-cafe-400 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {p.label}
        </button>
      ))}
    </div>
  );
}
