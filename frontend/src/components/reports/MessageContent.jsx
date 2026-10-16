export const MessageContent = ({ text, streaming = false }) => (
  <p className="text-sm whitespace-pre-wrap break-words">
    {text}
    {streaming && (
      <span
        className="inline-block w-2 h-4 ml-0.5 bg-cyan-400 align-middle animate-pulse"
        aria-hidden="true"
      />
    )}
  </p>
);
