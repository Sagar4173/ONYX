import { useState, useEffect } from "react";
import {
  UserCircleIcon,
  XCircleIcon,
  ComputerDesktopIcon,
  KeyIcon,
} from "@heroicons/react/24/outline";
import api from "../../services/api";
import { getRoleColor, getStatusColor, getStatusIcon } from "./userHelpers";

const MODAL_TABS = ["profile", "sessions", "tokens", "activity"];

const UserModal = ({ user, isOpen, onClose }) => {
  const [activeTab, setActiveTab] = useState("profile");
  const [userSessions, setUserSessions] = useState([]);
  const [userTokens, setUserTokens] = useState([]);
  const [userActivity, setUserActivity] = useState([]);

  useEffect(() => {
    if (isOpen && user) {
      Promise.all([
        api.get(`/users/${user.id}/sessions`),
        api.get(`/users/${user.id}/api-tokens`),
        api.get(`/users/${user.id}/activity`),
      ]).then(([sessions, tokens, activity]) => {
        setUserSessions(sessions.data.sessions);
        setUserTokens(tokens.data.tokens);
        setUserActivity(activity.data.activities);
      });
    }
  }, [isOpen, user]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-gray-900 border border-gray-800 rounded-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden">
        <div className="p-6 border-b border-gray-800">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="w-12 h-12 bg-gradient-to-br from-cyan-500 to-violet-600 rounded-xl flex items-center justify-center">
                <UserCircleIcon className="w-6 h-6 text-white" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-white">{user.full_name}</h2>
                <p className="text-gray-400">@{user.username}</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-800 rounded-lg transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900"
            >
              <XCircleIcon className="w-6 h-6 text-gray-400" />
            </button>
          </div>

          <div className="flex space-x-1 mt-6">
            {MODAL_TABS.map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900 ${
                  activeTab === tab
                    ? "bg-cyan-500/20 text-cyan-400 border border-cyan-500/30"
                    : "text-gray-400 hover:text-white hover:bg-gray-800"
                }`}
              >
                {tab.charAt(0).toUpperCase() + tab.slice(1)}
              </button>
            ))}
          </div>
        </div>

        <div className="p-6 overflow-y-auto max-h-[60vh]">
          {activeTab === "profile" && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-gray-400 text-sm">Email</label>
                  <p className="text-white">{user.email}</p>
                </div>
                <div>
                  <label className="text-gray-400 text-sm">Role</label>
                  <span
                    className={`inline-block px-2 py-1 rounded-lg text-xs font-medium border ${getRoleColor(user.role)}`}
                  >
                    {user.role.replace("_", " ").toUpperCase()}
                  </span>
                </div>
                <div>
                  <label className="text-gray-400 text-sm">Status</label>
                  <span
                    className={`inline-flex items-center space-x-1 px-2 py-1 rounded-lg text-xs font-medium border ${getStatusColor(user.status)}`}
                  >
                    {getStatusIcon(user.status)}
                    <span>{user.status.replace("_", " ").toUpperCase()}</span>
                  </span>
                </div>
                <div>
                  <label className="text-gray-400 text-sm">Organization</label>
                  <p className="text-white">{user.organization || "Not specified"}</p>
                </div>
              </div>
            </div>
          )}

          {activeTab === "sessions" && (
            <div className="space-y-4">
              {userSessions.map((session) => (
                <div
                  key={session.session_id}
                  className="p-4 bg-gray-800/50 rounded-lg border border-gray-700"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <ComputerDesktopIcon className="w-5 h-5 text-gray-400" />
                      <div>
                        <p className="text-white text-sm">{session.ip_address}</p>
                        <p className="text-gray-400 text-xs">{session.user_agent}</p>
                      </div>
                    </div>
                    <button className="text-red-400 hover:text-red-300 text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900">
                      Revoke
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {activeTab === "tokens" && (
            <div className="space-y-4">
              {userTokens.map((token) => (
                <div
                  key={token.token_id}
                  className="p-4 bg-gray-800/50 rounded-lg border border-gray-700"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <KeyIcon className="w-5 h-5 text-gray-400" />
                      <div>
                        <p className="text-white text-sm">{token.name}</p>
                        <p className="text-gray-400 text-xs">{token.prefix}...</p>
                      </div>
                    </div>
                    <button className="text-red-400 hover:text-red-300 text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900">
                      Revoke
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {activeTab === "activity" && (
            <div className="space-y-4">
              {userActivity.map((activity) => (
                <div
                  key={activity.id}
                  className="p-4 bg-gray-800/50 rounded-lg border border-gray-700"
                >
                  <div className="flex items-center space-x-3">
                    <div
                      className={`w-2 h-2 rounded-full ${activity.type === "login" ? "bg-green-400" : "bg-red-400"}`}
                    />
                    <div>
                      <p className="text-white text-sm">
                        {activity.type} from {activity.ip_address}
                      </p>
                      <p className="text-gray-400 text-xs">
                        {new Date(activity.timestamp).toLocaleString()}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default UserModal;
