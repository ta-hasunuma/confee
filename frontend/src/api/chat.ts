const API_URL = import.meta.env.VITE_API_URL as string | undefined;

interface ChatRequest {
  message: string;
  session_id: string;
}

interface ChatResponse {
  response: string;
  session_id: string;
}

interface ChatErrorResponse {
  error: string;
}

export class ChatApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ChatApiError";
    this.status = status;
  }
}

export async function sendMessage(
  message: string,
  sessionId: string
): Promise<ChatResponse> {
  if (!API_URL) {
    throw new Error("VITE_API_URL is not configured");
  }

  const body: ChatRequest = { message, session_id: sessionId };

  const res = await fetch(`${API_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const errorBody = (await res.json().catch(() => null)) as ChatErrorResponse | null;
    const errorMessage = errorBody?.error ?? `HTTP ${res.status}`;
    throw new ChatApiError(errorMessage, res.status);
  }

  return res.json() as Promise<ChatResponse>;
}

export function generateSessionId(): string {
  return `${crypto.randomUUID()}-${crypto.randomUUID().slice(0, 8)}`;
}
