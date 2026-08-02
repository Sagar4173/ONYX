/**
 * Enhanced Login Form Component
 * Modern UI with animations and glassmorphism
 * Supports Two-Factor Authentication flow
 */
import { useState, useEffect, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  EyeIcon,
  EyeSlashIcon,
  ShieldCheckIcon,
  EnvelopeIcon,
  LockClosedIcon,
  UserIcon,
  KeyIcon,
  ArrowRightIcon,
  CheckCircleIcon,
  DevicePhoneMobileIcon,
} from "@heroicons/react/24/outline";
import { ShieldCheckIcon as ShieldCheckSolid } from "@heroicons/react/24/solid";
import { Button, Input } from "../ui/StyleComponents";
import { useAuth } from "./AuthContext";
import { authAPI } from "../../services/api";
import toast from "react-hot-toast";

const GOOGLE_GSI_SRC = "https://accounts.google.com/gsi/client";

const GoogleLogo = () => (
  <svg className="w-5 h-5" viewBox="0 0 48 48" aria-hidden="true">
    <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z" />
    <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z" />
    <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z" />
    <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z" />
  </svg>
);

export const LoginForm = ({ onSuccess, onSwitchToRegister, onSwitchToForgotPassword }) => {
  const [formData, setFormData] = useState({
    username_or_email: "",
    password: "",
    remember_me: false,
    two_factor_code: "",
  });
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [requires2FA, setRequires2FA] = useState(false);
  const [twoFAEmail, setTwoFAEmail] = useState("");
  const [ssoEnabled, setSsoEnabled] = useState(false);
  const [googleReady, setGoogleReady] = useState(false);
  const [googlePendingToken, setGooglePendingToken] = useState(null);
  const [isGoogleLoading, setIsGoogleLoading] = useState(false);
  // Server-issued, single-use nonce from GET /auth/sso/google/config. Google
  // embeds it in the ID token; the backend verifies and consumes it on login,
  // so a captured token can never be replayed.
  const [ssoNonce, setSsoNonce] = useState(null);
  const googleButtonRef = useRef(null);
  // Tracks which nonce the GSI instance was initialized with, so re-renders
  // never re-initialize (Google warns on multiple initialize() calls).
  const gsiInitNonceRef = useRef(null);
  const { login, googleLogin, completeGoogleLogin } = useAuth();

  // Load Google Identity Services when SSO is configured
  useEffect(() => {
    let cancelled = false;

    const loadGoogleScript = () => {
      if (window.google?.accounts) {
        setGoogleReady(true);
        return;
      }
      const existing = document.querySelector(`script[src="${GOOGLE_GSI_SRC}"]`);
      if (existing) {
        existing.addEventListener("load", () => !cancelled && setGoogleReady(true));
        return;
      }
      const script = document.createElement("script");
      script.src = GOOGLE_GSI_SRC;
      script.async = true;
      script.defer = true;
      script.onload = () => !cancelled && setGoogleReady(true);
      document.head.appendChild(script);
    };

    authAPI
      .getGoogleSSOConfig()
      .then((config) => {
        if (cancelled) return;
        if (config?.enabled && config.client_id && config.nonce) {
          setSsoEnabled(true);
          setSsoNonce(config.nonce);
          window.__ONYX_GOOGLE_CLIENT_ID__ = config.client_id;
          loadGoogleScript();
        }
      })
      .catch(() => {
        // SSO config unavailable - silently keep the password form only
      });

    return () => {
      cancelled = true;
    };
  }, []);

  // Initialize GSI once the script is loaded and the server nonce is available.
  // Re-initializes only when the nonce changes (stale-nonce recovery).
  useEffect(() => {
    if (!googleReady || !ssoEnabled || !ssoNonce || !window.google?.accounts) return;
    if (gsiInitNonceRef.current === ssoNonce) return;
    gsiInitNonceRef.current = ssoNonce;
    window.google.accounts.id.initialize({
      client_id: window.__ONYX_GOOGLE_CLIENT_ID__,
      callback: handleGoogleCredential,
      auto_select: false,
      nonce: ssoNonce,
    });
  }, [googleReady, ssoEnabled, ssoNonce]);

  // The backend rejects nonces it never issued (e.g. a browser still running a
  // cached pre-upgrade bundle, or a Google credential minted for an earlier
  // session). Fetch a fresh nonce and re-initialize GSI so the next click
  // produces a credential bound to the current server session.
  const refreshSsoNonce = useCallback(async () => {
    try {
      const config = await authAPI.getGoogleSSOConfig();
      if (config?.enabled && config.client_id && config.nonce) {
        window.__ONYX_GOOGLE_CLIENT_ID__ = config.client_id;
        gsiInitNonceRef.current = null;
        setSsoNonce(config.nonce);
        return true;
      }
    } catch {
      // Config unavailable - keep the current state; the error toast stands.
    }
    return false;
  }, []);

  const handleGoogleCredential = useCallback(
    async (response) => {
      if (!response?.credential) {
        toast.error("Google sign-in was cancelled or failed");
        return;
      }
      setIsGoogleLoading(true);
      try {
        const result = await googleLogin(response.credential, ssoNonce);
        if (result?.requires_2fa) {
          setGooglePendingToken(response.credential);
          setTwoFAEmail(result.user_email || "your email");
          setRequires2FA(true);
          toast("Please enter your 2FA code from your authenticator app", { icon: "ℹ️" });
          return;
        }
        onSuccess && onSuccess();
      } catch (error) {
        const detail = error?.response?.data?.detail;
        if (typeof detail === "string" && /nonce|expired|session/i.test(detail)) {
          const refreshed = await refreshSsoNonce();
          if (refreshed) {
            toast("Google session expired - please click Continue with Google again");
          }
        }
      } finally {
        setIsGoogleLoading(false);
      }
    },
    [googleLogin, onSuccess, ssoNonce, refreshSsoNonce]
  );

  // Render the Google button once the container + GSI are both available
  useEffect(() => {
    if (googleReady && googleButtonRef.current && window.google?.accounts) {
      try {
        window.google.accounts.id.renderButton(googleButtonRef.current, {
          theme: "outline",
          size: "large",
          text: "continue_with",
          shape: "pill",
          click_listener: () => setIsGoogleLoading(true),
        });
      } catch (error) {
        console.error("Failed to render Google sign-in button:", error);
      }
    }
  }, [googleReady, ssoEnabled, requires2FA]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      const result = await login(formData);

      // Check if 2FA is required
      if (result?.requires_2fa) {
        setRequires2FA(true);
        setTwoFAEmail(result.user_email || "your email");
        toast("Please enter your 2FA code from your authenticator app", { icon: "ℹ️" });
        setIsLoading(false);
        return;
      }

      // Login successful
      onSuccess && onSuccess();
    } catch (error) {
      // Error is handled in the login function
    } finally {
      setIsLoading(false);
    }
  };

  const handle2FASubmit = async (e) => {
    e.preventDefault();
    if (formData.two_factor_code.length < 6) return;
    setIsLoading(true);
    try {
      if (googlePendingToken) {
        await completeGoogleLogin(googlePendingToken, formData.two_factor_code, ssoNonce);
      } else {
        await login({ ...formData, two_factor_code: formData.two_factor_code });
      }
      onSuccess && onSuccess();
    } catch (error) {
      // Error is handled in the auth context
    } finally {
      setIsLoading(false);
    }
  };

  const handleBack = () => {
    setRequires2FA(false);
    setGooglePendingToken(null);
    setFormData((prev) => ({ ...prev, two_factor_code: "" }));
  };

  // 2FA Code Entry Form
  const twoFAView = (
    <motion.div
      key="2fa"
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className="p-8 md:p-10"
    >
      <div className="mb-8 text-center">
        <div className="mx-auto w-16 h-16 bg-gradient-to-br from-violet-500/20 to-cyan-500/20 rounded-2xl flex items-center justify-center mb-4">
          <DevicePhoneMobileIcon className="w-8 h-8 text-violet-400" />
        </div>
        <h2 className="text-2xl font-bold text-white mb-2">Two-Factor Authentication</h2>
        <p className="text-gray-400 text-sm">
          Enter the 6-digit code from your authenticator app for{" "}
          <span className="text-cyan-400">{twoFAEmail}</span>
        </p>
      </div>

      <form onSubmit={handle2FASubmit} className="space-y-6">
        <div className="group">
          <label className="flex items-center gap-2 text-sm font-medium text-gray-300 mb-2">
            <ShieldCheckIcon className="w-4 h-4 text-violet-400" />
            Authentication Code
          </label>
          <Input
            type="text"
            inputMode="numeric"
            pattern="[0-9]*"
            maxLength={6}
            value={formData.two_factor_code}
            onChange={(e) => {
              const value = e.target.value.replace(/\D/g, "");
              setFormData((prev) => ({
                ...prev,
                two_factor_code: value,
              }));
            }}
            placeholder="000000"
            autoFocus
            required
            className="text-center text-2xl tracking-[0.5em] font-mono"
          />
          <p className="mt-2 text-xs text-gray-500 text-center">
            Or enter a backup code if you've lost access to your authenticator
          </p>
        </div>

        <Button
          type="submit"
          disabled={isLoading || formData.two_factor_code.length < 6}
          gradient
          leftIcon={<ShieldCheckIcon className="w-5 h-5" />}
          isLoading={isLoading}
          className="w-full"
        >
          Verify & Sign In
        </Button>

        <Button type="button" variant="ghost" onClick={handleBack} className="w-full">
          ← Back to login
        </Button>
      </form>

      <div className="mt-6 p-4 bg-violet-500/10 border border-violet-500/20 rounded-xl">
        <div className="flex items-start gap-3">
          <ShieldCheckSolid className="w-5 h-5 text-violet-400 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-gray-300">
            <p className="font-medium text-violet-300 mb-1">Your account is protected</p>
            <p className="text-gray-400 text-xs">
              Two-factor authentication adds an extra layer of security to your account by
              requiring a code from your authenticator app.
            </p>
          </div>
        </div>
      </div>
    </motion.div>
  );

  // Standard Login Form
  const standardView = (
    <motion.div
      key="login"
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className="p-8 md:p-10"
    >
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-white mb-2">Sign In</h2>
        <p className="text-gray-400">Access your ONYX security dashboard</p>
      </div>

      <motion.form
        onSubmit={handleSubmit}
        className="space-y-6"
        initial="hidden"
        animate="visible"
        variants={{
          hidden: {},
          visible: { transition: { staggerChildren: 0.04 } },
        }}
      >
        <motion.div
          variants={{
            hidden: { opacity: 0, y: 8 },
            visible: { opacity: 1, y: 0 },
          }}
          className="group"
        >
          <label className="flex items-center gap-2 text-sm font-medium text-gray-300 mb-2">
            <EnvelopeIcon className="w-4 h-4 text-cyan-400" />
            Email or Username
          </label>
          <Input
            type="text"
            value={formData.username_or_email}
            onChange={(e) =>
              setFormData((prev) => ({
                ...prev,
                username_or_email: e.target.value,
              }))
            }
            leadingIcon={<UserIcon className="w-5 h-5" />}
            placeholder="Enter your email or username"
            required
            aria-required="true"
            autoComplete="username"
          />
        </motion.div>

        <motion.div
          variants={{
            hidden: { opacity: 0, y: 8 },
            visible: { opacity: 1, y: 0 },
          }}
          className="group"
        >
          <label className="flex items-center gap-2 text-sm font-medium text-gray-300 mb-2">
            <LockClosedIcon className="w-4 h-4 text-violet-400" />
            Password
          </label>
          <div className="relative">
            <Input
              type={showPassword ? "text" : "password"}
              value={formData.password}
              onChange={(e) => setFormData((prev) => ({ ...prev, password: e.target.value }))}
              leadingIcon={<KeyIcon className="w-5 h-5" />}
              placeholder="Enter your password"
              required
              aria-required="true"
              autoComplete="current-password"
              className="pr-12"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              aria-label={showPassword ? "Hide password" : "Show password"}
              className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-white transition-colors p-1 rounded-lg hover:bg-gray-600/30 z-10 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500"
            >
              {showPassword ? (
                <EyeSlashIcon className="h-5 w-5" />
              ) : (
                <EyeIcon className="h-5 w-5" />
              )}
            </button>
          </div>
        </motion.div>

        <motion.div
          variants={{
            hidden: { opacity: 0, y: 8 },
            visible: { opacity: 1, y: 0 },
          }}
          className="flex items-center justify-between"
        >
          <label className="flex items-center group cursor-pointer">
            <input
              type="checkbox"
              checked={formData.remember_me}
              onChange={(e) =>
                setFormData((prev) => ({
                  ...prev,
                  remember_me: e.target.checked,
                }))
              }
              className="w-4 h-4 rounded border-gray-600 bg-gray-700 text-cyan-500 focus:ring-cyan-500/50 focus:ring-offset-0 transition-all cursor-pointer"
            />
            <span className="ml-2 text-sm text-gray-300 group-hover:text-white transition-colors">
              Remember me
            </span>
          </label>

          <button
            type="button"
            onClick={onSwitchToForgotPassword}
            className="text-sm text-cyan-400 hover:text-cyan-300 transition-colors font-medium hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900 rounded"
          >
            Forgot password?
          </button>
        </motion.div>

        <motion.div
          variants={{
            hidden: { opacity: 0, y: 8 },
            visible: { opacity: 1, y: 0 },
          }}
        >
          <Button
            type="submit"
            disabled={isLoading}
            gradient
            rightIcon={isLoading ? undefined : <ArrowRightIcon className="w-5 h-5" />}
            isLoading={isLoading}
            className="w-full"
          >
            Sign In
          </Button>
        </motion.div>
      </motion.form>

      {ssoEnabled && (
        <motion.div
          variants={{
            hidden: { opacity: 0, y: 8 },
            visible: { opacity: 1, y: 0 },
          }}
        >
          <div className="flex items-center gap-3 my-6">
            <div className="flex-1 h-px bg-gray-700/50" />
            <span className="text-xs text-gray-500 uppercase tracking-wider">or</span>
            <div className="flex-1 h-px bg-gray-700/50" />
          </div>

          <div className="relative">
            <div
              ref={googleButtonRef}
              className="overflow-hidden rounded-xl"
              aria-label="Sign in with Google"
            />
            {isGoogleLoading && (
              <div className="absolute inset-0 flex items-center justify-center bg-gray-900/70 rounded-xl">
                <div className="w-5 h-5 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin" />
              </div>
            )}
            {!googleReady && (
              <button
                type="button"
                onClick={() => {
                  if (window.google?.accounts) {
                    window.google.accounts.id.prompt();
                  }
                }}
                disabled={!window.google?.accounts}
                className="w-full flex items-center justify-center gap-3 py-3 px-4 rounded-xl bg-gray-800 hover:bg-gray-700 border border-gray-700/50 text-white text-sm font-medium transition-all"
              >
                <GoogleLogo />
                Continue with Google
              </button>
            )}
          </div>
        </motion.div>
      )}

      <motion.div
        variants={{
          hidden: { opacity: 0, y: 8 },
          visible: { opacity: 1, y: 0 },
        }}
        className="mt-8 text-center"
      >
        <span className="text-gray-400">Don't have an account? </span>
        <button
          type="button"
          onClick={onSwitchToRegister}
          className="font-semibold text-transparent bg-gradient-to-r from-cyan-400 to-violet-400 bg-clip-text hover:from-cyan-300 hover:to-violet-300 transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900 rounded"
        >
          Create account
        </button>
      </motion.div>

      <motion.div
        variants={{
          hidden: { opacity: 0, y: 8 },
          visible: { opacity: 1, y: 0 },
        }}
        className="mt-8 pt-6 border-t border-gray-700/50"
      >
        <div className="flex items-center justify-center gap-6 text-gray-500 text-xs">
          <div className="flex items-center gap-1">
            <ShieldCheckIcon className="w-4 h-4 text-cyan-400" />
            <span>Secure</span>
          </div>
          <div className="flex items-center gap-1">
            <LockClosedIcon className="w-4 h-4 text-violet-400" />
            <span>Encrypted</span>
          </div>
          <div className="flex items-center gap-1">
            <CheckCircleIcon className="w-4 h-4 text-cyan-300" />
            <span>Verified</span>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );

  return (
    <AnimatePresence mode="wait">
      {requires2FA ? twoFAView : standardView}
    </AnimatePresence>
  );
};
