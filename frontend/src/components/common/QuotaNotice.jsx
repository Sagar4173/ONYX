import { useEffect, useState } from "react";
import { ClockIcon } from "@heroicons/react/24/outline";
import { Alert, Button } from "../ui/StyleComponents";

export const QuotaNotice = ({ retryAfter = null, onRetry }) => {
  const [secondsLeft, setSecondsLeft] = useState(retryAfter ?? null);

  useEffect(() => {
    setSecondsLeft(retryAfter ?? null);
    if (retryAfter == null) return undefined;
    const timer = setInterval(() => {
      setSecondsLeft((s) => (s == null ? null : Math.max(0, s - 1)));
    }, 1000);
    return () => clearInterval(timer);
  }, [retryAfter]);

  const ready = secondsLeft === 0;

  return (
    <div role="status" aria-live="polite">
      <Alert variant="warning" title="Rate limit reached" icon={<ClockIcon className="w-5 h-5" />}>
        {secondsLeft != null
          ? `AI requests are limited — retry in ${secondsLeft}s.`
          : "AI requests are limited right now. Try again shortly."}
        {onRetry && secondsLeft === 0 && (
          <Button variant="outline" size="sm" className="mt-3" onClick={onRetry}>
            Try again
          </Button>
        )}
      </Alert>
      {!ready && secondsLeft != null && <span className="sr-only">{secondsLeft}s remaining</span>}
    </div>
  );
};
