import { useState } from "react";
import { motion } from "framer-motion";
import { EnvelopeIcon, ArrowRightIcon } from "@heroicons/react/24/outline";
import { Button, Input } from "../ui/StyleComponents";
import { useAuth } from "./AuthContext";

export const ForgotPasswordForm = ({ onSuccess, onSwitchToLogin }) => {
  const [email, setEmail] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const { requestPasswordReset } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      await requestPasswordReset(email);
      onSuccess && onSuccess(email);
    } catch (error) {
      // Error is handled in the context
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <motion.div
      className="p-10"
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
        className="text-center mb-8"
      >
        <h2 className="text-3xl font-bold text-white mb-2">Reset Password</h2>
        <p className="text-sm text-gray-400">Enter your email to receive reset instructions</p>
      </motion.div>

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
        >
          <label className="flex items-center gap-2 text-sm font-medium text-gray-300 mb-2">
            <EnvelopeIcon className="w-4 h-4 text-cyan-400" />
            Email Address
          </label>
          <Input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="your@email.com"
            required
            aria-required="true"
            autoComplete="email"
          />
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
            Send Reset Link
          </Button>
        </motion.div>
      </motion.form>

      <motion.div
        variants={{
          hidden: { opacity: 0, y: 8 },
          visible: { opacity: 1, y: 0 },
        }}
        className="mt-8 text-center"
      >
        <button
          type="button"
          onClick={onSwitchToLogin}
          className="font-semibold text-transparent bg-gradient-to-r from-cyan-400 to-violet-400 bg-clip-text hover:from-cyan-300 hover:to-violet-300 transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900 rounded"
        >
          ← Back to sign in
        </button>
      </motion.div>
    </motion.div>
  );
};
