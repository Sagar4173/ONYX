import {
  ArrowPathIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  SparklesIcon,
} from "@heroicons/react/24/outline";
import { Alert, Button, EmptyState, Skeleton, Spinner } from "../ui/StyleComponents";
import { QuotaNotice } from "./QuotaNotice";

export const AIStateBlock = ({
  variant = "loading",
  title,
  description,
  detail,
  onRetry,
  retryLabel = "Retry",
  quotaRetryAfter = null,
  onQuotaRetry,
  className = "",
}) => {
  if (variant === "loading") {
    return (
      <div className={`flex items-start gap-3 p-4 ${className}`} role="status" aria-live="polite">
        <Spinner size="sm" />
        <div className="flex-1 space-y-2">
          <p className="text-sm text-gray-400">{title || "Working..."}</p>
          <Skeleton variant="text" />
          <Skeleton variant="text" className="w-3/4" />
        </div>
      </div>
    );
  }

  if (variant === "empty") {
    return (
      <div className={className}>
        <EmptyState
          icon={<SparklesIcon className="w-10 h-10 text-gray-500" />}
          title={title || "Nothing here yet"}
          description={description}
        />
      </div>
    );
  }

  if (variant === "error") {
    return (
      <div role="alert" className={className}>
        <Alert variant="danger" title={title || "Something went wrong"}>
          {description}
          {detail && <span className="block mt-1 font-mono text-xs opacity-75">{detail}</span>}
          {onRetry && (
            <Button
              variant="outline"
              size="sm"
              className="mt-3"
              onClick={onRetry}
              leftIcon={<ArrowPathIcon className="w-4 h-4" />}
            >
              {retryLabel}
            </Button>
          )}
        </Alert>
      </div>
    );
  }

  if (variant === "degraded") {
    return (
      <div className={className} role="status" aria-live="polite">
        <Alert
          variant="warning"
          title={title || "Running in degraded mode"}
          icon={<ExclamationTriangleIcon className="w-5 h-5" />}
        >
          {description || "A fallback is handling this request; results may be limited."}
        </Alert>
      </div>
    );
  }

  if (variant === "disabled") {
    return (
      <div className={className} role="status" aria-live="polite">
        <Alert
          variant="info"
          title={title || "Feature disabled"}
          icon={<InformationCircleIcon className="w-5 h-5" />}
        >
          {description || "This feature is turned off by an administrator."}
        </Alert>
      </div>
    );
  }

  // rate_limited
  return (
    <div className={className}>
      <QuotaNotice retryAfter={quotaRetryAfter} onRetry={onQuotaRetry} />
    </div>
  );
};
