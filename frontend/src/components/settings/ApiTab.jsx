import { useState } from "react";
import { EyeIcon, EyeSlashIcon } from "@heroicons/react/24/outline";
import toast from "react-hot-toast";
import { Button } from "../../styles/components";
import SettingCard from "./SettingCard";

const ApiTab = ({ settings, handleSettingChange }) => {
  const [showApiKey, setShowApiKey] = useState(false);

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold text-white">API & Integration</h2>

      <SettingCard
        title="API Key"
        description="Your API key for integrating with external services"
        type="warning"
      >
        <div className="space-y-3 w-full max-w-md">
          <div className="flex items-center space-x-2">
            <div className="relative flex-1">
              <input
                type={showApiKey ? "text" : "password"}
                value={settings.api.api_key}
                readOnly
                className="w-full px-3 py-2 pr-10 bg-gray-700/50 border border-gray-600/50 rounded-lg text-white font-mono text-sm"
              />
              <button
                onClick={() => setShowApiKey(!showApiKey)}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-white"
              >
                {showApiKey ? (
                  <EyeSlashIcon className="h-4 w-4" />
                ) : (
                  <EyeIcon className="h-4 w-4" />
                )}
              </button>
            </div>
            <Button
              onClick={() => toast.success("New API key generated!")}
              variant="warning"
              size="sm"
            >
              Regenerate
            </Button>
          </div>
          <p className="text-xs text-yellow-400">
            Keep your API key secure. Don't share it or expose it in client-side code.
          </p>
        </div>
      </SettingCard>

      <SettingCard
        title="Webhook URL"
        description="Receive scan results and notifications via webhook"
      >
        <input
          type="url"
          value={settings.api.webhook_url}
          onChange={(e) => handleSettingChange("api", "webhook_url", e.target.value)}
          placeholder="https://your-domain.com/webhook"
          className="w-full max-w-md px-3 py-2 bg-gray-700/50 border border-gray-600/50 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-cyan-500/50"
        />
      </SettingCard>

      <SettingCard title="Rate Limiting" description="API request limits per hour">
        <div className="flex items-center space-x-3">
          <input
            type="number"
            value={settings.api.rate_limit}
            onChange={(e) => handleSettingChange("api", "rate_limit", parseInt(e.target.value))}
            className="w-24 px-3 py-2 bg-gray-700/50 border border-gray-600/50 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-cyan-500/50"
          />
          <span className="text-gray-400">requests/hour</span>
        </div>
      </SettingCard>
    </div>
  );
};

export default ApiTab;
