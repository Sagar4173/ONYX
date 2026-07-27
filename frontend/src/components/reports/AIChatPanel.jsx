import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  SparklesIcon,
  PaperAirplaneIcon,
  ChatBubbleLeftRightIcon,
  ExclamationTriangleIcon,
  ArrowPathIcon,
  ShieldCheckIcon,
  CodeBracketIcon,
  LightBulbIcon,
} from "@heroicons/react/24/outline";
import { reportsAPI } from "../../services/api";

const SUGGESTED_QUESTIONS = [
  "What are the most critical vulnerabilities in this scan?",
  "How can I fix the SQL injection vulnerabilities found?",
  "What's the overall security posture of this project?",
  "Which compliance frameworks are impacted?",
  "Show me the riskiest finding and how to remediate it.",
];

const getIconForText = (text) => {
  const lower = text.toLowerCase();
  if (lower.includes("critical") || lower.includes("risk")) return <ExclamationTriangleIcon className="w-4 h-4 text-red-400" />;
  if (lower.includes("fix") || lower.includes("remediat") || lower.includes("secure")) return <ShieldCheckIcon className="w-4 h-4 text-green-400" />;
  if (lower.includes("code") || lower.includes("sql") || lower.includes("xss")) return <CodeBracketIcon className="w-4 h-4 text-cyan-400" />;
  if (lower.includes("compliance") || lower.includes("framework")) return <LightBulbIcon className="w-4 h-4 text-amber-400" />;
  return <SparklesIcon className="w-4 h-4 text-violet-400" />;
};

export const AIChatPanel = ({ reportId }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showSuggestions, setShowSuggestions] = useState(true);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async (text) => {
    const userMessage = text || input;
    if (!userMessage.trim() || isLoading) return;

    setShowSuggestions(false);
    setError(null);
    setInput("");

    const updatedMessages = [...messages, { role: "user", content: userMessage }];
    setMessages(updatedMessages);
    setIsLoading(true);

    try {
      const history = updatedMessages.slice(-20).map((m) => ({
        role: m.role,
        content: m.content,
      }));

      const data = await reportsAPI.aiChat(reportId, userMessage, history);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.reply, model: data.model_used },
      ]);
    } catch (err) {
      const detail = err?.response?.data?.detail || err.message || "AI chat service unavailable";
      setError(detail);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `Error: ${detail}`,
          isError: true,
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-gray-800/40 backdrop-blur-xl border border-gray-700/50 rounded-2xl overflow-hidden"
    >
      <div className="flex items-center justify-between px-6 py-4 border-b border-gray-700/50 bg-gradient-to-r from-gray-800/80 to-gray-800/40">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-gradient-to-r from-violet-500 to-cyan-500 shadow-lg">
            <ChatBubbleLeftRightIcon className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">AI Security Chat</h3>
            <p className="text-xs text-gray-400">Ask questions about your scan results</p>
          </div>
        </div>
      </div>

      <div className="h-80 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && !isLoading && (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <ChatBubbleLeftRightIcon className="w-12 h-12 text-gray-600 mb-3" />
            <p className="text-gray-400 text-sm mb-4">
              Ask anything about this security scan — vulnerabilities, fixes, compliance, or risks.
            </p>
            {showSuggestions && (
              <div className="space-y-2 w-full max-w-md">
                {SUGGESTED_QUESTIONS.map((q, i) => (
                  <button
                    key={i}
                    onClick={() => sendMessage(q)}
                    className="w-full text-left px-4 py-2.5 rounded-xl bg-gray-700/30 border border-gray-700/50 text-sm text-gray-300 hover:bg-gray-700/50 hover:border-gray-600/50 transition-all flex items-center gap-2"
                  >
                    {getIconForText(q)}
                    {q}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        <AnimatePresence>
          {messages.map((msg, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[85%] rounded-2xl px-4 py-3 ${
                  msg.role === "user"
                    ? "bg-gradient-to-r from-cyan-500 to-violet-600 text-white"
                    : msg.isError
                      ? "bg-red-900/30 border border-red-800/50 text-red-300"
                      : "bg-gray-700/50 border border-gray-600/50 text-gray-200"
                }`}
              >
                {msg.role === "assistant" && msg.model && (
                  <div className="flex items-center gap-1 mb-1">
                    <SparklesIcon className="w-3 h-3 text-violet-400" />
                    <span className="text-[10px] text-violet-400 uppercase tracking-wider font-medium">
                      {msg.model}
                    </span>
                  </div>
                )}
                <p className="text-sm whitespace-pre-wrap break-words">{msg.content}</p>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {isLoading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex justify-start"
          >
            <div className="bg-gray-700/50 border border-gray-600/50 rounded-2xl px-4 py-3 flex items-center gap-2">
              <ArrowPathIcon className="w-4 h-4 text-cyan-400 animate-spin" />
              <span className="text-sm text-gray-400">Analyzing scan data...</span>
            </div>
          </motion.div>
        )}

        {error && !isLoading && messages[messages.length - 1]?.isError && (
          <div className="text-center">
            <button
              onClick={() => sendMessage(messages[messages.length - 2]?.content || "")}
              className="text-xs text-cyan-400 hover:text-cyan-300 underline"
            >
              Retry
            </button>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="border-t border-gray-700/50 p-4">
        <div className="flex items-center gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about vulnerabilities, fixes, compliance..."
            disabled={isLoading}
            className="flex-1 bg-gray-700/50 border border-gray-600/50 rounded-xl px-4 py-2.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500/50 disabled:opacity-50"
          />
          <button
            onClick={() => sendMessage()}
            disabled={!input.trim() || isLoading}
            className="p-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-violet-600 text-white hover:from-cyan-400 hover:to-violet-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <PaperAirplaneIcon className="w-5 h-5" />
          </button>
        </div>
      </div>
    </motion.div>
  );
};
