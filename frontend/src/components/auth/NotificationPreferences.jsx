import { useState, useEffect } from "react";
import {
  BellIcon,
  EnvelopeIcon,
  DevicePhoneMobileIcon,
  ShieldExclamationIcon,
  SparklesIcon,
  BoltIcon,
  CheckCircleIcon,
  XMarkIcon,
  ArrowPathIcon,
} from "@heroicons/react/24/outline";
import { HeartIcon } from "@heroicons/react/24/solid";
import toast from "react-hot-toast";
import { authAPI } from "../../services/api";

const categories = [
  {
    key: "email",
    title: "Email Notifications",
    description: "Receive important updates and alerts via email",
    icon: EnvelopeIcon,
    gradient: "from-blue-500/20 to-cyan-500/20",
    iconColor: "text-blue-400",
  },
  {
    key: "push",
    title: "Push Notifications",
    description: "Get real-time alerts on your device",
    icon: DevicePhoneMobileIcon,
    gradient: "from-purple-500/20 to-pink-500/20",
    iconColor: "text-purple-400",
  },
  {
    key: "security",
    title: "Security Alerts",
    description: "Critical security notifications and login alerts",
    icon: ShieldExclamationIcon,
    gradient: "from-red-500/20 to-orange-500/20",
    iconColor: "text-red-400",
    recommended: true,
  },
  {
    key: "updates",
    title: "Product Updates",
    description: "New features, improvements, and platform updates",
    icon: SparklesIcon,
    gradient: "from-emerald-500/20 to-teal-500/20",
    iconColor: "text-emerald-400",
  },
  {
    key: "marketing",
    title: "Marketing & Promotions",
    description: "Special offers, tips, and educational content",
    icon: HeartIcon,
    gradient: "from-pink-500/20 to-rose-500/20",
    iconColor: "text-pink-400",
  },
];

export const NotificationPreferences = () => {
  const [notifications, setNotifications] = useState({
    email: true,
    push: true,
    security: true,
    updates: false,
    marketing: false,
  });
  const [savingNotifications, setSavingNotifications] = useState(false);
  const [loadingNotifications, setLoadingNotifications] = useState(true);

  useEffect(() => {
    const fetchNotifications = async () => {
      try {
        setLoadingNotifications(true);
        const prefs = await authAPI.getNotificationPreferences();
        setNotifications({
          email: prefs.email ?? true,
          push: prefs.push ?? true,
          security: prefs.security ?? true,
          updates: prefs.updates ?? false,
          marketing: prefs.marketing ?? false,
        });
      } catch (error) {
        console.debug("Could not fetch notification preferences:", error);
      } finally {
        setLoadingNotifications(false);
      }
    };
    fetchNotifications();
  }, []);

  const handleToggle = async (key) => {
    const newValue = !notifications[key];
    const prevNotifications = { ...notifications };

    setNotifications((prev) => ({ ...prev, [key]: newValue }));

    try {
      setSavingNotifications(true);
      await authAPI.updateNotificationPreferences({ [key]: newValue });
    } catch (error) {
      setNotifications(prevNotifications);
      toast.error("Failed to update notification preferences");
    } finally {
      setSavingNotifications(false);
    }
  };

  const setAll = async (values) => {
    setNotifications(values);
    try {
      setSavingNotifications(true);
      await authAPI.updateNotificationPreferences(values);
      const isAllOn = Object.values(values).every(Boolean);
      toast.success(isAllOn ? "All notifications enabled" : "Only security alerts enabled");
    } catch (error) {
      toast.error("Failed to update preferences");
    } finally {
      setSavingNotifications(false);
    }
  };

  return (
    <div className="space-y-5 animate-fadeIn">
      <div className="relative overflow-hidden rounded-2xl p-6 bg-gradient-to-br from-gray-800/50 to-gray-900/50 border border-gray-700/50">
        <div className="absolute inset-0 bg-gradient-to-r from-purple-500/5 via-pink-500/5 to-rose-500/5" />
        <div className="relative flex items-center gap-4">
          <div className="p-3 bg-gradient-to-br from-purple-500/20 to-pink-500/20 rounded-xl">
            <BellIcon className="h-7 w-7 text-purple-400" />
          </div>
          <div>
            <h3 className="text-white font-bold text-lg">Notification Preferences</h3>
            <p className="text-gray-400 text-sm">
              {loadingNotifications ? "Loading preferences..." : "Control how and when you receive notifications"}
            </p>
          </div>
          {savingNotifications && (
            <div className="ml-auto">
              <ArrowPathIcon className="h-5 w-5 text-indigo-400 animate-spin" />
            </div>
          )}
        </div>
      </div>

      <div className="space-y-4">
        {loadingNotifications ? (
          <div className="space-y-4">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="bg-gray-800/30 border border-gray-700/50 rounded-2xl p-5 animate-pulse">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-gray-700 rounded-xl" />
                  <div className="flex-1 space-y-2">
                    <div className="h-4 bg-gray-700 rounded w-1/4" />
                    <div className="h-3 bg-gray-700 rounded w-1/2" />
                  </div>
                  <div className="w-14 h-8 bg-gray-700 rounded-full" />
                </div>
              </div>
            ))}
          </div>
        ) : (
          categories.map((item) => (
            <div
              key={item.key}
              className="group bg-gray-800/30 border border-gray-700/50 hover:border-gray-600/50 rounded-2xl p-5 transition-all duration-300"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className={`p-3 bg-gradient-to-br ${item.gradient} rounded-xl group-hover:scale-110 transition-transform duration-300`}>
                    <item.icon className={`h-5 w-5 ${item.iconColor}`} />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h4 className="text-white font-medium">{item.title}</h4>
                      {item.recommended && (
                        <span className="px-2 py-0.5 text-[10px] bg-amber-500/20 text-amber-400 rounded-full border border-amber-500/30">
                          Recommended
                        </span>
                      )}
                    </div>
                    <p className="text-gray-400 text-sm mt-0.5">{item.description}</p>
                  </div>
                </div>
                <button
                  role="switch"
                  aria-checked={notifications[item.key]}
                  aria-label={`${item.title}: ${notifications[item.key] ? "enabled" : "disabled"}`}
                  onClick={() => handleToggle(item.key)}
                  disabled={savingNotifications}
                  className={`relative flex-shrink-0 w-14 h-8 rounded-full transition-all duration-300 disabled:opacity-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900 ${
                    notifications[item.key]
                      ? "bg-gradient-to-r from-indigo-500 to-purple-500"
                      : "bg-gray-700"
                  }`}
                >
                  <div
                    className={`absolute top-1 w-6 h-6 bg-white rounded-full shadow-lg transition-all duration-300 ${
                      notifications[item.key] ? "left-7" : "left-1"
                    }`}
                  />
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      <div className="bg-gray-800/30 border border-gray-700/50 rounded-2xl p-5">
        <h4 className="text-white font-semibold mb-4 flex items-center gap-2">
          <BoltIcon className="h-5 w-5 text-amber-400" />
          Quick Actions
        </h4>
        <div className="grid grid-cols-2 gap-3">
          <button
            onClick={() => setAll({ email: true, push: true, security: true, updates: true, marketing: true })}
            disabled={savingNotifications}
            className="py-3 px-4 bg-gradient-to-r from-emerald-500/10 to-green-500/10 hover:from-emerald-500/20 hover:to-green-500/20 border border-emerald-500/20 text-emerald-400 font-medium rounded-xl transition-all duration-300 flex items-center justify-center gap-2 disabled:opacity-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900"
          >
            <CheckCircleIcon className="h-5 w-5" />
            Enable All
          </button>
          <button
            onClick={() => setAll({ email: false, push: false, security: true, updates: false, marketing: false })}
            disabled={savingNotifications}
            className="py-3 px-4 bg-gradient-to-r from-gray-700/50 to-gray-600/50 hover:from-gray-700 hover:to-gray-600 border border-gray-600/50 text-gray-300 font-medium rounded-xl transition-all duration-300 flex items-center justify-center gap-2 disabled:opacity-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900"
          >
            <XMarkIcon className="h-5 w-5" />
            Minimal Only
          </button>
        </div>
      </div>
    </div>
  );
};
