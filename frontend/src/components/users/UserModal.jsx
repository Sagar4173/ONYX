import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  UserCircleIcon,
  XCircleIcon,
  ComputerDesktopIcon,
  KeyIcon,
  EyeIcon,
} from "@heroicons/react/24/outline";
import api from "../../services/api";
import { getRoleColor, getStatusColor, getStatusIcon } from "./userHelpers";

const MODAL_TABS = ["profile", "sessions", "tokens", "activity"];

const tabAnim = { hidden: { opacity: 0, x: 5 }, show: { opacity: 1, x: 0 } };
const listAnim = {
  hidden: {},
  show: { transition: { staggerChildren: 0.04 } },
};
const listItem = { hidden: { opacity: 0, x: -5 }, show: { opacity: 1, x: 0 } };

const UserModal = ({ user, isOpen, onClose }) => {
  const [activeTab, setActiveTab] = useState("profile");
  const [userSessions, setUserSessions] = useState([]);
  const [userTokens, setUserTokens] = useState([]);
  const [userActivity, setUserActivity] = useState([]);

  useEffect(() => {
    if (isOpen && user) {
      setActiveTab("profile");
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

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 10 }}
            transition={{ duration: 0.2 }}
            className="bg-gray-900/90 backdrop-blur-xl border border-gray-700/50 rounded-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden shadow-2xl"
          >
            <div className="p-6 border-b border-gray-700/50">
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
                  <XCircleIcon className="w-6 h-6 text-gray-400 hover:text-white transition-colors" />
                </button>
              </div>

              <div className="bg-gray-800/40 backdrop-blur-sm border border-gray-700/50 rounded-xl p-1 mt-6">
                <nav className="flex space-x-1">
                  {MODAL_TABS.map((tab) => (
                    <button
                      key={tab}
                      onClick={() => setActiveTab(tab)}
                      className={`relative flex-1 py-2 rounded-lg text-sm font-medium transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900 ${
                        activeTab === tab
                          ? "text-white"
                          : "text-gray-400 hover:text-gray-300"
                      }`}
                    >
                      {activeTab === tab && (
                        <motion.div
                          layoutId="modal-tab"
                          className="absolute inset-0 bg-gradient-to-r from-cyan-500 to-violet-500 rounded-lg"
                          initial={false}
                          transition={{ type: "spring", stiffness: 500, damping: 30 }}
                        />
                      )}
                      <span className="relative z-10">
                        {tab.charAt(0).toUpperCase() + tab.slice(1)}
                      </span>
                    </button>
                  ))}
                </nav>
              </div>
            </div>

            <div className="p-6 overflow-y-auto max-h-[60vh]">
              <motion.div
                key={activeTab}
                variants={tabAnim}
                initial="hidden"
                animate="show"
                transition={{ duration: 0.15 }}
              >
                {activeTab === "profile" && (
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="bg-gray-800/30 rounded-xl p-4 border border-gray-700/30">
                        <label className="text-gray-400 text-sm flex items-center gap-2">
                          <EyeIcon className="w-3.5 h-3.5" /> Email
                        </label>
                        <p className="text-white mt-1">{user.email}</p>
                      </div>
                      <div className="bg-gray-800/30 rounded-xl p-4 border border-gray-700/30">
                        <label className="text-gray-400 text-sm">Role</label>
                        <div className="mt-1">
                          <span
                            className={`inline-block px-2 py-1 rounded-lg text-xs font-medium border ${getRoleColor(user.role)}`}
                          >
                            {user.role.replace("_", " ").toUpperCase()}
                          </span>
                        </div>
                      </div>
                      <div className="bg-gray-800/30 rounded-xl p-4 border border-gray-700/30">
                        <label className="text-gray-400 text-sm">Status</label>
                        <div className="mt-1">
                          <span
                            className={`inline-flex items-center space-x-1 px-2 py-1 rounded-lg text-xs font-medium border ${getStatusColor(user.status)}`}
                          >
                            {getStatusIcon(user.status)}
                            <span>{user.status.replace("_", " ").toUpperCase()}</span>
                          </span>
                        </div>
                      </div>
                      <div className="bg-gray-800/30 rounded-xl p-4 border border-gray-700/30">
                        <label className="text-gray-400 text-sm">Organization</label>
                        <p className="text-white mt-1">{user.organization || "Not specified"}</p>
                      </div>
                    </div>
                  </div>
                )}

                {activeTab === "sessions" && (
                  <motion.div className="space-y-3" variants={listAnim} initial="hidden" animate="show">
                    {userSessions.map((session) => (
                      <motion.div
                        key={session.session_id}
                        variants={listItem}
                        className="p-4 bg-gray-800/40 backdrop-blur-sm rounded-xl border border-gray-700/50"
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-3">
                            <ComputerDesktopIcon className="w-5 h-5 text-cyan-400" />
                            <div>
                              <p className="text-white text-sm">{session.ip_address}</p>
                              <p className="text-gray-400 text-xs truncate max-w-xs">
                                {session.user_agent}
                              </p>
                            </div>
                          </div>
                          <button className="text-red-400 hover:text-red-300 text-sm font-medium focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900">
                            Revoke
                          </button>
                        </div>
                      </motion.div>
                    ))}
                  </motion.div>
                )}

                {activeTab === "tokens" && (
                  <motion.div className="space-y-3" variants={listAnim} initial="hidden" animate="show">
                    {userTokens.map((token) => (
                      <motion.div
                        key={token.token_id}
                        variants={listItem}
                        className="p-4 bg-gray-800/40 backdrop-blur-sm rounded-xl border border-gray-700/50"
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-3">
                            <KeyIcon className="w-5 h-5 text-cyan-400" />
                            <div>
                              <p className="text-white text-sm">{token.name}</p>
                              <p className="text-gray-400 text-xs font-mono">{token.prefix}...</p>
                            </div>
                          </div>
                          <button className="text-red-400 hover:text-red-300 text-sm font-medium focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900">
                            Revoke
                          </button>
                        </div>
                      </motion.div>
                    ))}
                  </motion.div>
                )}

                {activeTab === "activity" && (
                  <motion.div className="space-y-3" variants={listAnim} initial="hidden" animate="show">
                    {userActivity.map((activity) => (
                      <motion.div
                        key={activity.id}
                        variants={listItem}
                        className="p-4 bg-gray-800/40 backdrop-blur-sm rounded-xl border border-gray-700/50"
                      >
                        <div className="flex items-center space-x-3">
                          <span
                            className={`w-2 h-2 rounded-full flex-shrink-0 ${
                              activity.type === "login"
                                ? "bg-green-400"
                                : activity.type === "logout"
                                  ? "bg-gray-400"
                                  : "bg-red-400"
                            }`}
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
                      </motion.div>
                    ))}
                  </motion.div>
                )}
              </motion.div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default UserModal;
