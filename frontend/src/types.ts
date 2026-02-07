export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

export interface SuggestedPrompt {
  id: string;
  label: string;
  prompt: string;
  category: "keyword" | "vague";
}
