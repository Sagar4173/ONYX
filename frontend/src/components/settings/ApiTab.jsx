import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  CheckCircleIcon,
  ClipboardIcon,
  ExclamationTriangleIcon,
} from "@heroicons/react/24/outline";
import toast from "react-hot-toast";
import { Button } from "../ui/StyleComponents";
import SettingCard from "./SettingCard";

const stagger = { hidden: {}, show: { transition: { staggerChildren: 0.05 } } };
const item = { hidden: { opacity: 0, y: 10 }, show: { opacity: 1, y: 0 } };

const apiBase = import.meta.env.DEV ? "http://127.0.0.1:8000" : "";

const authHeaders = () => {
  const token = localStorage.getItem("access_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
};

const ApiTab = ({ user }) => {
  const isAdmin = user?.role === "admin";

  const [webhook, setWebhook] = useState(null);
  const [loadingStatus, setLoadingStatus] = useState(false);
  const [rotating, setRotating] = useState(false);
  const [rotatedSecret, setRotatedSecret] = useState(null);

  const loadWebhookStatus = async () => {
    setLoadingStatus(true);
    try {
      const response = await fetch(`${apiBase}/api/admin/webhook/status`, {
        headers: authHeaders(),
      });
      if (response.ok) {
        setWebhook(await response.json());
      }
    } catch (error) {
      // status is informational only
    } finally {
      setLoadingStatus(false);
    }
  };

  useEffect(() => {
    if (isAdmin) {
      loadWebhookStatus();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAdmin]);

  const handleCopy = (text, label) => {
    navigator.clipboard.writeText(text);
    toast.success(`${label} copied to clipboard`);
  };

  const handleRotate = async () => {
    if (
      !window.confirm(
        "Rotating the webhook secret invalidates the current one immediately after restart. " +
          "Any GitHub webhook still using the old secret will start receiving 401 responses. Continue?"
      )
    ) {
      return;
    }

    setRotating(true);
    try {
      const response = await fetch(`${apiBase}/api/admin/webhook/rotate`, {
        method: "POST",
        headers: authHeaders(),
      });
      const body = await response.json();
      if (!response.ok) {
        throw new Error(body.detail || "Failed to rotate webhook secret");
      }
      setRotatedSecret(body.secret);
      toast.success("Webhook secret rotated!");
      loadWebhookStatus();
    } catch (error) {
      toast.error(error.message || "Failed to rotate webhook secret");
    } finally {
      setRotating(false);
    }
  };

  return (
    <motion.div className="space-y-6" variants={stagger} initial="hidden" animate="show">
      <h2 className="text-xl font-semibold text-white">API & Integration</h2>

      <motion.div variants={item}>
        <SettingCard
          title="Webhook Integration"
          description="Send repository events from GitHub to ONYX for automated security scans"
        >
          <div className="space-y-4 w-full max-w-lg">
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-400">Status:</span>
              {loadingStatus ? (
                <span className="text-sm text-gray-500">Loading...</span>
              ) : webhook?.configured ? (
                <span className="inline-flex items-center space-x-1 text-sm text-emerald-400">
                  <CheckCircleIcon className="h-4 w-4" /> Configured
                  <span className="text-gray-500 font-mono text-xs">
                    (prefix {webhook.secret_prefix}...)
                  </span>
                </span>
              ) : (
                <span className="inline-flex items-center space-x-1 text-sm text-yellow-400">
                  <ExclamationTriangleIcon className="h-4 w-4" /> Not configured
                </span>
              )}
            </div>

            {isAdmin && webhook && (
              <>
                <div>
                  <label className="block text-xs text-gray-400 mb-1">Webhook URL</label>
                  <div className="flex items-center space-x-2">
                    <input
                      type="text"
                      readOnly
                      value={webhook.url}
                      className="flex-1 px-3 py-2 bg-gray-700/50 border border-gray-600/50 rounded-lg text-white font-mono text-sm"
                    />
                    <button
                      onClick={() => handleCopy(webhook.url, "Webhook URL")}
                      className="p-2 rounded-lg bg-gray-700/50 border border-gray-600/50 text-gray-400 hover:text-white hover:bg-gray-700 transition-all"
                      title="Copy webhook URL"
                    >
                      <ClipboardIcon className="h-4 w-4" />
                    </button>
                  </div>
                </div>

                <div className="flex items-center space-x-3">
                  <Button
                    onClick={handleRotate}
                    disabled={rotating}
                    variant="warning"
                    size="sm"
                  >
                    {rotating ? "Rotating..." : "Rotate Secret"}
                  </Button>
                  {webhook.configured && (
                    <span className="text-xs text-gray-500 font-mono">
                      Header: <code className="text-gray-400">x-onyx-webhook-secret</code>
                    </span>
                  )}
                </div>
              </>
            )}

            {rotatedSecret && (
              <div className="p-3 rounded-lg bg-yellow-500/10 border border-yellow-500/30 space-y-2">
                <p className="text-xs text-yellow-300">
                  New secret (shown once): copy it now. The old secret stops working
                  immediately. Update your GitHub webhook, then restart the backend
                  service (<code>systemctl restart onyx-backend</code>) to apply it.
                </p>
                <div className="flex items-center space-x-2">
                  <input
                    type="text"
                    readOnly
                    value={rotatedSecret}
                    className="flex-1 px-3 py-2 bg-gray-800 border border-yellow-500/40 rounded-lg text-white font-mono text-sm"
                  />
                  <button
                    onClick={() => handleCopy(rotatedSecret, "Secret")}
                    className="p-2 rounded-lg bg-gray-700/50 border border-gray-600/50 text-gray-400 hover:text-white hover:bg-gray-700 transition-all"
                    title="Copy new secret"
                  >
                    <ClipboardIcon className="h-4 w-4" />
                  </button>
                </div>
              </div>
            )}

            {!isAdmin && (
              <p className="text-xs text-gray-500">
                Webhook configuration is available to administrators.
              </p>
            )}
          </div>
        </SettingCard>
      </motion.div>

      <motion.div variants={item}>
        <SettingCard title="Rate Limiting" description="API request limits per hour">
          <div className="flex items-center space-x-3">
            <input
              type="number"
              value={1000}
              readOnly
              className="w-24 px-3 py-2 bg-gray-700/50 border border-gray-600/50 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-cyan-500/50"
            />
            <span className="text-gray-400">requests/hour (platform default)</span>
          </div>
        </SettingCard>
      </motion.div>
    </motion.div>
  );
};

export default ApiTab;
