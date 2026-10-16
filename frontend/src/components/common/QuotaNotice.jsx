import { useEffect, useState } from "react";
import { ClockIcon } from "@heroicons/react/24/outline";
import { Alert, Button } from "../ui/StyleComponents";

export const QuotaNotice = ({ retryAfter = null, onRetry }) => {
  const [secondsLeft, setSecondsLeft] = useState(retryAfter ?? null);

  useEffect(() => {
    setSecondsLeft(retryAfter ?? null);
    if (retryAfter == null || retryAfter <= 0) return undefined;
    let current = retryAfter;
    const timer = setInterval(() => {
      current = current <= 0 ? 0 : current - 1;
      setSecondsLeft(current);
      if (current === 0) clearInterval(timer);
    }, 1000);
    return () => clearInterval(timer);
  }, [retryAfter]);

  const ready = secondsLeft === 0 || secondsLeft == null;
  const visibleMessage =
    secondsLeft == null
      ? "AI requests are limited right now. Try again shortly."
      : secondsLeft === 0
        ? "AI requests are limited — you can retry now."
        : `AI requests are limited — retry in ${secondsLeft}s.`;

  return (
    <div role="status" aria-live="polite">
      <Alert variant="warning" title="Rate limit reached" icon={<ClockIcon className="w-5 h-5" />}>
        {/* Visible countdown is decorative for SR: sr-only span below is the single live announcement. */}
        <span aria-hidden="true">{visibleMessage}</span>
        {onRetry && ready && (
          <Button variant="outline" size="sm" className="mt-3" onClick={onRetry}>
            Try again
          </Button>
        )}
      </Alert>
      <span className="sr-only">
        {secondsLeft == null
          ? "Try again now."
          : secondsLeft === 0
            ? "Rate limit reached. Ready to retry."
            : `${secondsLeft}s remaining`}
      </span>
    </div>
  );
};
