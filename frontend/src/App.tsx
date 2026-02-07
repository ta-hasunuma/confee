import { useState } from "react";
import { ChatContainer } from "./components/ChatContainer";

export default function App() {
  const [sessionKey, setSessionKey] = useState(0);

  return (
    <div className="h-screen flex flex-col bg-cafe-50">
      <header className="bg-cafe-800 px-5 py-4 flex items-center justify-between shadow-md">
        <div className="flex items-center gap-3">
          <img
            src="/image.png"
            alt="confee"
            className="w-10 h-10 rounded-lg shadow-sm"
          />
          <div>
            <h1 className="text-xl font-bold text-cafe-100">Confee</h1>
            <p className="text-base text-cafe-300">
              Your Tech Conference Partner
            </p>
          </div>
        </div>
        <button
          onClick={() => setSessionKey((k) => k + 1)}
          className="rounded-lg bg-cafe-700 border border-cafe-600 px-4 py-2 text-base text-cafe-100 hover:bg-cafe-600 transition-colors"
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
