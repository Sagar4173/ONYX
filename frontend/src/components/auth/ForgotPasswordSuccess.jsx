import { PaperAirplaneIcon, EnvelopeIcon } from "@heroicons/react/24/outline";

/**
 * ForgotPasswordSuccess Component
 * Success message displayed after password reset request
 * Shows email sent confirmation with instructions
 */
export const ForgotPasswordSuccess = ({ email, onSwitchToLogin }) => {
  return (
    <div className="relative min-h-[500px] p-8">
      {/* Animated Background Blobs */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-1/2 -left-1/2 w-full h-full bg-gradient-to-br from-cyan-500/20 via-violet-500/20 to-cyan-500/20 rounded-full blur-3xl animate-pulse" />
        <div
          className="absolute -bottom-1/2 -right-1/2 w-full h-full bg-gradient-to-tl from-violet-500/20 via-cyan-500/20 to-violet-500/20 rounded-full blur-3xl animate-pulse"
          style={{ animationDelay: "1s" }}
        />
      </div>

      {/* Content */}
      <div className="relative text-center">
        {/* Success Icon */}
        <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-r from-cyan-500 to-violet-600 rounded-full mb-6 animate-bounce">
          <PaperAirplaneIcon className="h-10 w-10 text-white" />
        </div>

        {/* Title */}
        <h2 className="text-3xl font-bold text-white mb-3 bg-gradient-to-r from-cyan-400 to-violet-400 bg-clip-text text-transparent">
          Check Your Email
        </h2>

        {/* Description */}
        <p className="text-gray-300 mb-2">Password reset instructions have been sent!</p>
        <p className="text-gray-400 mb-6 text-sm">We've sent a password reset link to:</p>

        {/* Email Display */}
        <div className="flex items-center justify-center gap-2 bg-gray-800/50 border border-gray-700/50 rounded-xl px-4 py-3 mb-6">
          <EnvelopeIcon className="h-5 w-5 text-cyan-400" />
          <span className="text-white font-medium">{email}</span>
        </div>

        {/* Info Box */}
        <div className="bg-violet-500/10 border border-violet-500/30 rounded-xl p-4 mb-6">
          <p className="text-sm text-gray-300 mb-2">
            <span className="font-semibold text-violet-400">Next Steps:</span>
          </p>
          <ul className="text-xs text-gray-400 text-left space-y-1">
            <li className="flex items-start gap-2">
              <span className="text-cyan-400 mt-0.5">1.</span>
              <span>Check your email inbox for the password reset link</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-cyan-400 mt-0.5">2.</span>
              <span>Click the link to create a new password</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-cyan-400 mt-0.5">3.</span>
              <span>The link will expire in 1 hour for security reasons</span>
            </li>
          </ul>
          <p className="text-xs text-gray-400 mt-3">
            <span className="text-violet-400">Note:</span> Check your spam folder if you don't see
            the email within a few minutes.
          </p>
        </div>

        {/* Back to Login */}
        <button
          onClick={onSwitchToLogin}
          className="w-full py-3 px-4 bg-gradient-to-r from-cyan-500 to-violet-600 text-white font-medium rounded-xl hover:from-cyan-600 hover:to-violet-700 transition-all duration-300 transform hover:scale-105 shadow-lg hover:shadow-cyan-500/25"
        >
          Back to Login
        </button>
      </div>
    </div>
  );
};
