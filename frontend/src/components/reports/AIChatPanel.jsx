import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ChatBubbleLeftRightIcon,
  CodeBracketIcon,
  ExclamationTriangleIcon,
  LightBulbIcon,
  PaperAirplaneIcon,
  ShieldCheckIcon,
  SparklesIcon,
  XMarkIcon,
} from "@heroicons/react/24/outline";
import { Button, Input, Spinner } from "../ui/StyleComponents";
import { AIStateBlock } from "../common/AIStateBlock";
import { QuotaNotice } from "../common/QuotaNotice";
import { MessageContent } from "./MessageContent";
import { useConversation } from "../../hooks/useConversation";
import { useSSEStream } from "../../hooks/useSSEStream";

const SUGGESTED_QUESTIONS = [
  "What are the most critical vulnerabilities in this scan?",
  "How can I fix the SQL injection vulnerabilities found?",
  "What's the overall security posture of this project?",
  "Which compliance frameworks are impacted?",
  "Show me the riskiest finding and how to remediate it.",
];

const getIconForText = (text) => {
  const lower = text.toLowerCase();
  if (lower.includes("critical") || lower.includes("risk"))
    return <ExclamationTriangleIcon className="w-4 h-4 text-red-400" />;
  if (lower.includes("fix") || lower.includes("remediat") || lower.includes("secure"))
    return <ShieldCheckIcon className="w-4 h-4 text-green-400" />;
  if (lower.includes("code") || lower.includes("sql") || lower.includes("xss"))
    return <CodeBracketIcon className="w-4 h-4 text-cyan-400" />;
  if (lower.includes("compliance") || lower.includes("framework"))
    return <LightBulbIcon className="w-4 h-4 text-amber-400" />;
  return <SparklesIcon className="w-4 h-4 text-violet-400" />;
};

export const AIChatPanel = ({ scanId }) => {
  const [input, setInput] = useState("");
  const [streamError, setStreamError] = useState(null);
  const [rateLimit, setRateLimit] = useState(null); // number | null (null = inactive)
  const messagesEndRef = useRef(null);
  const {
    messages,
    pushUser,
    beginAssistant,
    appendDelta,
    finishAssistant,
    settleAssistant,
    failAssistant,
    removeMessage,
    getMessage,
  } = useConversation(scanId);
  const { status, send, abort } = useSSEStream();

  const active = status === "connecting" || status === "streaming";

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, status]);

  const runStream = async (userMessage, baseMessages) => {
    const prior = baseMessages || messages;
    const history = [...prior, { role: "user", content: userMessage }]
      .slice(-20)
      .map((m) => ({ role: m.role, content: m.content }));
    const id = beginAssistant();
    const outcome = await send({
      scanId,
      message: userMessage,
      history,
      onEvent: (event) => {
        if (event.type === "delta") appendDelta(id, event.text);
        if (event.type === "done") finishAssistant(id, event);
      },
    });

    if (outcome.status === "done") {
      settleAssistant(id); // no-op when finishAssistant already ran
      return;
    }
    if (outcome.status === "aborted") {
      settleAssistant(id);
      return;
    }
    const detail = outcome.error?.message || "AI chat service unavailable";
    const partial = getMessage(id)?.text;
    if (outcome.status === "rate_limited") {
      setRateLimit(outcome.error?.retryAfter ?? null);
      if (partial) settleAssistant(id);
      else failAssistant(id, detail);
      return;
    }
    if (partial) {
      settleAssistant(id);
      setStreamError(detail);
    } else {
      failAssistant(id, detail);
      setStreamError(null);
    }
  };

  const sendMessage = async (text, baseMessages) => {
    const userMessage = text || input;
    if (!userMessage.trim() || active) return;
    setStreamError(null);
    setRateLimit(null);
    setInput("");
    pushUser(userMessage);
    await runStream(userMessage, baseMessages);
  };

  const retryLast = () => {
    if (active) return;
    const list = [...messages];
    const staleIds = [];
    while (list.length > 0 && list[list.length - 1].role === "assistant") {
      staleIds.push(list.pop().id);
    }
    const lastUser = list.pop();
    if (!lastUser || lastUser.role !== "user") return;
    staleIds.push(lastUser.id);
    staleIds.forEach((id) => removeMessage(id));
    sendMessage(lastUser.content, list);
  };

  const lastCompleted = [...messages]
    .reverse()
    .find((m) => m.role === "assistant" && !m.streaming && !m.isError);

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
        {active && (
          <span className="flex items-center gap-2 text-xs text-cyan-300">
            <Spinner size="sm" />
            {status === "streaming" ? "Responding" : "Connecting"}
          </span>
        )}
      </div>

      <div className="h-80 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && !active && (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <ChatBubbleLeftRightIcon className="w-12 h-12 text-gray-600 mb-3" />
            <p className="text-gray-400 text-sm mb-4">
              Ask anything about this security scan — vulnerabilities, fixes, compliance, or risks.
            </p>
            <div className="space-y-2 w-full max-w-md">
              {SUGGESTED_QUESTIONS.map((q, i) => (
                <button
                  key={i}
                  type="button"
                  onClick={() => sendMessage(q)}
                  className="w-full text-left px-4 py-2.5 rounded-xl bg-gray-700/30 border border-gray-700/50 text-sm text-gray-300 hover:bg-gray-700/50 hover:border-gray-600/50 transition-all flex items-center gap-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-gray-900"
                >
                  {getIconForText(q)}
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        <AnimatePresence>
          {messages.map((msg) =>
            msg.role === "user" ? (
              <motion.div
                key={msg.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex justify-end"
              >
                <div className="max-w-[85%] rounded-2xl px-4 py-3 bg-gradient-to-r from-cyan-500 to-violet-600 text-white">
                  <p className="text-sm whitespace-pre-wrap break-words">{msg.content}</p>
                </div>
              </motion.div>
            ) : (
              <motion.div
                key={msg.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex justify-start"
              >
                {msg.isError ? (
                  <AIStateBlock
                    variant="error"
                    title="The assistant could not respond"
                    description={msg.content}
                    className="w-full max-w-[85%]"
                  />
                ) : (
                  <div className="max-w-[85%] rounded-2xl px-4 py-3 bg-gray-700/50 border border-gray-600/50 text-gray-200">
                    {msg.model && (
                      <div className="flex items-center gap-1 mb-1">
                        <SparklesIcon className="w-3 h-3 text-violet-400" />
                        <span className="text-[10px] text-violet-400 uppercase tracking-wider font-medium">
                          {msg.model}
                        </span>
                      </div>
                    )}
                    <MessageContent
                      text={msg.streaming ? msg.text : (msg.content ?? msg.text)}
                      streaming={msg.streaming}
                    />
                    {msg.partial && !msg.streaming && !msg.isError && (
                      <p className="mt-1 text-[10px] text-amber-300/80">
                        Partial response — connection ended early.
                      </p>
                    )}
                  </div>
                )}
              </motion.div>
            )
          )}
        </AnimatePresence>

        {status === "connecting" && (
          <div className="flex justify-start">
            <AIStateBlock
              variant="loading"
              title="Analyzing scan data..."
              className="w-full max-w-md"
            />
          </div>
        )}

        {rateLimit != null && !active && <QuotaNotice retryAfter={rateLimit} onRetry={retryLast} />}

        {streamError && rateLimit == null && !active && (
          <AIStateBlock
            variant="error"
            title="Response interrupted"
            description={streamError}
            onRetry={retryLast}
          />
        )}

        <div ref={messagesEndRef} />
        <div className="sr-only" aria-live="polite">
          {lastCompleted?.content ? `Answer: ${lastCompleted.content}` : ""}
        </div>
      </div>

      <div className="border-t border-gray-700/50 p-4">
        <div className="flex items-center gap-2">
          <Input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
              }
            }}
            placeholder="Ask about vulnerabilities, fixes, compliance..."
            disabled={active}
            aria-label="Chat message"
          />
          {active ? (
            <Button
              variant="danger"
              size="md"
              onClick={abort}
              leftIcon={<XMarkIcon className="w-5 h-5" />}
              aria-label="Stop response"
            >
              Stop
            </Button>
          ) : (
            <Button
              variant="primary"
              size="md"
              gradient
              onClick={() => sendMessage()}
              disabled={!input.trim()}
              aria-label="Send message"
              leftIcon={<PaperAirplaneIcon className="w-5 h-5" />}
            />
          )}
        </div>
      </div>
    </motion.div>
  );
};
