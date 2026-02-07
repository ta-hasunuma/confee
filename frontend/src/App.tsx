import { useState } from "react";
import { ChatContainer } from "./components/ChatContainer";

export default function App() {
  const [sessionKey, setSessionKey] = useState(0);

  return (
    <div className="h-screen flex flex-col bg-white">
      <header className="border-b border-gray-200 px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <img src="/image.png" alt="confee" className="w-8 h-8 rounded" />
          <div>
            <h1 className="text-xl font-bold text-gray-800">Confee</h1>
            <p className="text-base text-gray-500">
              Your Tech Conference Partner
            </p>
          </div>
        </div>
        <button
          onClick={() => setSessionKey((k) => k + 1)}
          className="rounded-lg border border-gray-300 px-4 py-2 text-base text-gray-600 hover:bg-gray-100 transition-colors"
        >
          新しい会話
        </button>
      </header>
      <main className="flex-1 min-h-0">
        <ChatContainer sessionKey={sessionKey} />
      </main>
    </div>
  );
}
