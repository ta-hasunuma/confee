export function LoadingIndicator() {
  return (
    <div className="flex justify-start">
      <div className="bg-white border border-cafe-200 rounded-2xl rounded-bl-sm px-5 py-3.5 max-w-[80%] shadow-sm">
        <div className="flex items-center gap-1.5">
          <div className="w-2.5 h-2.5 bg-cafe-400 rounded-full animate-bounce [animation-delay:0ms]" />
          <div className="w-2.5 h-2.5 bg-cafe-400 rounded-full animate-bounce [animation-delay:150ms]" />
          <div className="w-2.5 h-2.5 bg-cafe-400 rounded-full animate-bounce [animation-delay:300ms]" />
        </div>
      </div>
    </div>
  );
}
