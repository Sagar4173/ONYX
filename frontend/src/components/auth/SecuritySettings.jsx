import { useState, useEffect } from "react";
import {
  KeyIcon,
  ShieldCheckIcon,
  ClockIcon,
  FingerPrintIcon,
  LockClosedIcon,
  EyeIcon,
  EyeSlashIcon,
  CheckCircleIcon,
  XMarkIcon,
  ArrowPathIcon,
  ShieldExclamationIcon,
  DevicePhoneMobileIcon,
  ComputerDesktopIcon,
  MapPinIcon,
  QrCodeIcon,
  ArrowRightOnRectangleIcon,
} from "@heroicons/react/24/outline";
import { CheckIcon } from "@heroicons/react/24/solid";
import toast from "react-hot-toast";
import { useAuth } from "./AuthContext";
import { authAPI, getApiErrorMessage } from "../../services/api";

export const SecuritySettings = ({ securityScore, getSecurityScoreColor, onLogout }) => {
  const { resendVerificationEmail, refreshUserProfile } = useAuth();

  const [passwordData, setPasswordData] = useState({
    current_password: "",
    new_password: "",
    confirm_password: "",
  });
  const [showPasswords, setShowPasswords] = useState({ current: false, new: false, confirm: false });
  const [isChangingPassword, setIsChangingPassword] = useState(false);

  const [twoFactorEnabled, setTwoFactorEnabled] = useState(false);
  const [twoFactorSetupData, setTwoFactorSetupData] = useState(null);
  const [twoFactorCode, setTwoFactorCode] = useState("");
  const [showTwoFactorSetup, setShowTwoFactorSetup] = useState(false);
  const [showTwoFactorDisable, setShowTwoFactorDisable] = useState(false);
  const [disableCode, setDisableCode] = useState("");
  const [processing2FA, setProcessing2FA] = useState(false);
  const [backupCodesRemaining, setBackupCodesRemaining] = useState(0);

  const [activeSessions, setActiveSessions] = useState([]);
  const [revokingSession, setRevokingSession] = useState(null);
  const [loadingSessions, setLoadingSessions] = useState(true);
  const [loading2FA, setLoading2FA] = useState(true);

  useEffect(() => {
    const fetch2FAStatus = async () => {
      try {
        setLoading2FA(true);
        const status = await authAPI.get2FAStatus();
        setTwoFactorEnabled(status.enabled);
        setBackupCodesRemaining(status.backup_codes_remaining || 0);
      } catch (error) {
        console.debug("Could not fetch 2FA status:", error);
      } finally {
        setLoading2FA(false);
      }
    };
    fetch2FAStatus();
  }, []);

  useEffect(() => {
    const fetchSessions = async () => {
      try {
        setLoadingSessions(true);
        const sessions = await authAPI.getSessions();
        setActiveSessions(
          sessions.map((session) => ({
            id: session.session_id,
            device: session.device || "Unknown Device",
            browser: session.browser || "Unknown Browser",
            location: session.location || "Unknown Location",
            ip: session.ip_address,
            current: session.is_current,
            lastActive: session.is_current ? "Now" : formatRelativeTime(session.last_active),
            createdAt: session.created_at,
          }))
        );
      } catch (error) {
        setActiveSessions([]);
      } finally {
        setLoadingSessions(false);
      }
    };
    fetchSessions();
  }, []);

  const formatRelativeTime = (dateString) => {
    if (!dateString) return "Unknown";
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins} min${diffMins > 1 ? "s" : ""} ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? "s" : ""} ago`;
    return `${diffDays} day${diffDays > 1 ? "s" : ""} ago`;
  };

  const handlePasswordInputChange = (e) => {
    const { name, value } = e.target;
    setPasswordData((prev) => ({ ...prev, [name]: value }));
  };

  const handlePasswordChange = async (e) => {
    e.preventDefault();
    if (passwordData.new_password !== passwordData.confirm_password) {
      toast.error("New passwords don't match");
      return;
    }
    if (passwordData.new_password.length < 8) {
      toast.error("Password must be at least 8 characters long");
      return;
    }
    setIsChangingPassword(true);
    try {
      await authAPI.changePassword({
        current_password: passwordData.current_password,
        new_password: passwordData.new_password,
      });
      toast.success("Password changed successfully!");
      setPasswordData({ current_password: "", new_password: "", confirm_password: "" });
    } catch (error) {
      const errorMsg = getApiErrorMessage(error, "Failed to change password");
      if (error.response?.status === 422 || errorMsg.toLowerCase().includes("password must")) {
        toast.error("Please ensure your password meets all requirements");
      } else {
        toast.error(errorMsg);
      }
    } finally {
      setIsChangingPassword(false);
    }
  };

  const handleSetup2FA = async () => {
    try {
      setProcessing2FA(true);
      const setupData = await authAPI.setup2FA();
      setTwoFactorSetupData(setupData);
      setShowTwoFactorSetup(true);
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Failed to setup 2FA"));
    } finally {
      setProcessing2FA(false);
    }
  };

  const handleEnable2FA = async () => {
    if (!twoFactorCode || twoFactorCode.length !== 6) {
      toast.error("Please enter a valid 6-digit code");
      return;
    }
    try {
      setProcessing2FA(true);
      await authAPI.enable2FA(twoFactorCode);
      setTwoFactorEnabled(true);
      setShowTwoFactorSetup(false);
      setTwoFactorCode("");
      setTwoFactorSetupData(null);
      toast.success("Two-factor authentication enabled successfully!");
      if (refreshUserProfile) refreshUserProfile();
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Invalid verification code"));
    } finally {
      setProcessing2FA(false);
    }
  };

  const handleDisable2FA = async () => {
    if (!disableCode || disableCode.length < 6) {
      toast.error("Please enter a valid code");
      return;
    }
    try {
      setProcessing2FA(true);
      await authAPI.disable2FA(disableCode);
      setTwoFactorEnabled(false);
      setShowTwoFactorDisable(false);
      setDisableCode("");
      toast.success("Two-factor authentication disabled");
      if (refreshUserProfile) refreshUserProfile();
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Invalid verification code"));
    } finally {
      setProcessing2FA(false);
    }
  };

  const handleRevokeSession = async (sessionId) => {
    try {
      setRevokingSession(sessionId);
      await authAPI.revokeSession(sessionId);
      setActiveSessions((prev) => prev.filter((s) => s.id !== sessionId));
      toast.success("Session terminated");
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Failed to terminate session"));
    } finally {
      setRevokingSession(null);
    }
  };

  const handleRevokeAllSessions = async () => {
    if (!confirm("Are you sure you want to terminate all other sessions?")) return;
    try {
      setRevokingSession("all");
      const result = await authAPI.revokeAllOtherSessions();
      setActiveSessions((prev) => prev.filter((s) => s.current));
      toast.success(result.message || "All other sessions terminated");
    } catch (error) {
      toast.error("Failed to terminate sessions");
    } finally {
      setRevokingSession(null);
    }
  };

  const getPasswordStrength = (password) => {
    if (!password) return { strength: 0, label: "", color: "" };
    let strength = 0;
    if (password.length >= 8) strength++;
    if (/[a-z]/.test(password)) strength++;
    if (/[A-Z]/.test(password)) strength++;
    if (/[0-9]/.test(password)) strength++;
    if (/[^a-zA-Z0-9]/.test(password)) strength++;
    const levels = [
      { label: "Very Weak", color: "bg-red-500" },
      { label: "Weak", color: "bg-orange-500" },
      { label: "Fair", color: "bg-yellow-500" },
      { label: "Good", color: "bg-lime-500" },
      { label: "Strong", color: "bg-green-500" },
    ];
    return { strength, ...levels[Math.min(strength - 1, 4)] };
  };

  const passwordStrength = getPasswordStrength(passwordData.new_password);

  return (
    <div className="space-y-5 animate-fadeIn">
      <div className="relative overflow-hidden rounded-2xl p-6 bg-gradient-to-br from-gray-800/50 to-gray-900/50 border border-gray-700/50">
        <div className="absolute inset-0 bg-gradient-to-r from-indigo-500/5 via-purple-500/5 to-pink-500/5" />
        <div className="relative flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="relative">
              <div className={`w-14 h-14 rounded-2xl bg-gradient-to-br ${getSecurityScoreColor(securityScore.score).gradient} flex items-center justify-center shadow-lg`}>
                <ShieldCheckIcon className="h-7 w-7 text-white" />
              </div>
              <div className={`absolute -bottom-1 -right-1 w-6 h-6 ${getSecurityScoreColor(securityScore.score).bg} rounded-full flex items-center justify-center text-white text-xs font-bold border-2 border-gray-900`}>
                {securityScore.score}
              </div>
            </div>
            <div>
              <h3 className="text-white font-bold text-lg">Security Overview</h3>
              <p className="text-gray-400 text-sm">
                {securityScore.factors.filter((f) => f.completed).length} of {securityScore.factors.length} security measures active
              </p>
            </div>
          </div>
          <div className="hidden md:flex gap-2">
            {securityScore.factors.map((factor, i) => (
              <div
                key={i}
                className={`w-3 h-3 rounded-full ${factor.completed ? "bg-emerald-500" : "bg-gray-600"} transition-all duration-300`}
                title={factor.name}
              />
            ))}
          </div>
        </div>
      </div>

      <div className="bg-gray-800/30 border border-gray-700/50 hover:border-purple-500/30 rounded-2xl p-6 transition-all duration-300 group">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-4">
            <div className="p-3 bg-gradient-to-br from-purple-500/20 to-pink-500/20 rounded-xl group-hover:scale-110 transition-transform duration-300">
              <FingerPrintIcon className="h-6 w-6 text-purple-400" />
            </div>
            <div>
              <h4 className="text-white font-semibold text-lg flex items-center gap-2">
                Two-Factor Authentication
                {loading2FA ? (
                  <span className="px-2 py-0.5 text-xs bg-gray-500/20 text-gray-400 rounded-full">Loading...</span>
                ) : twoFactorEnabled ? (
                  <span className="px-2 py-0.5 text-xs bg-emerald-500/20 text-emerald-400 rounded-full border border-emerald-500/30">Active</span>
                ) : null}
              </h4>
              <p className="text-gray-400 text-sm mt-1 max-w-md">
                Add an extra layer of security to your account by requiring a verification code in addition to your password.
              </p>
              {!twoFactorEnabled && !loading2FA && (
                <p className="text-amber-400 text-xs mt-2 flex items-center gap-1">
                  <ShieldExclamationIcon className="h-4 w-4" />
                  Enabling 2FA increases your security score by 30 points
                </p>
              )}
              {twoFactorEnabled && backupCodesRemaining > 0 && (
                <p className="text-gray-400 text-xs mt-2 flex items-center gap-1">
                  <KeyIcon className="h-4 w-4" />
                  {backupCodesRemaining} backup codes remaining
                </p>
              )}
            </div>
          </div>
          {loading2FA ? (
            <div className="flex-shrink-0 w-14 h-8 rounded-full bg-gray-700 animate-pulse" />
          ) : twoFactorEnabled ? (
            <button
              onClick={() => setShowTwoFactorDisable(true)}
              disabled={processing2FA}
              className="flex-shrink-0 px-4 py-2 text-sm text-red-400 bg-red-500/10 hover:bg-red-500/20 border border-red-500/30 rounded-xl transition-all disabled:opacity-50"
            >
              {processing2FA ? "Processing..." : "Disable"}
            </button>
          ) : (
            <button
              onClick={handleSetup2FA}
              disabled={processing2FA}
              className="flex-shrink-0 px-4 py-2 text-sm text-purple-400 bg-purple-500/10 hover:bg-purple-500/20 border border-purple-500/30 rounded-xl transition-all disabled:opacity-50"
            >
              {processing2FA ? "Setting up..." : "Enable 2FA"}
            </button>
          )}
        </div>

        {showTwoFactorSetup && twoFactorSetupData && (
          <div className="mt-6 p-5 bg-gray-900/60 rounded-xl border border-purple-500/20">
            <h5 className="text-white font-semibold mb-4 flex items-center gap-2">
              <QrCodeIcon className="h-5 w-5 text-purple-400" />
              Setup Two-Factor Authentication
            </h5>
            <div className="space-y-4">
              <div className="text-center">
                <p className="text-gray-400 text-sm mb-3">Scan this QR code with your authenticator app (Google Authenticator, Authy, etc.)</p>
                <div className="inline-block p-4 bg-gray-800 rounded-xl">
                  <img
                    src={`https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=${encodeURIComponent(twoFactorSetupData.qr_code_url)}`}
                    alt="2FA QR Code"
                    className="w-36 h-36"
                  />
                </div>
              </div>
              <div className="text-center">
                <p className="text-gray-400 text-xs mb-2">Or enter this secret manually:</p>
                <code className="px-3 py-1.5 bg-gray-800 rounded text-sm text-purple-400 font-mono">{twoFactorSetupData.secret}</code>
              </div>
              <div className="bg-amber-500/10 border border-amber-500/20 rounded-lg p-3">
                <p className="text-amber-400 text-xs font-medium mb-2">Save these backup codes:</p>
                <div className="grid grid-cols-4 gap-2">
                  {twoFactorSetupData.backup_codes.map((code, i) => (
                    <code key={i} className="text-xs text-gray-300 bg-gray-800 px-2 py-1 rounded text-center font-mono">{code}</code>
                  ))}
                </div>
              </div>
              <div>
                <label className="text-sm text-gray-300 mb-2">Enter the 6-digit code from your app:</label>
                <input
                  type="text"
                  value={twoFactorCode}
                  onChange={(e) => setTwoFactorCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
                  placeholder="000000"
                  className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-xl text-white text-center text-2xl tracking-widest font-mono focus:outline-none focus:border-purple-500"
                  maxLength={6}
                />
              </div>
              <div className="flex gap-3">
                <button
                  onClick={() => { setShowTwoFactorSetup(false); setTwoFactorSetupData(null); setTwoFactorCode(""); }}
                  className="flex-1 px-4 py-2.5 text-gray-400 bg-gray-800 hover:bg-gray-700 rounded-xl transition-all"
                >
                  Cancel
                </button>
                <button
                  onClick={handleEnable2FA}
                  disabled={twoFactorCode.length !== 6 || processing2FA}
                  className="flex-1 px-4 py-2.5 text-white bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {processing2FA ? "Verifying..." : "Verify & Enable"}
                </button>
              </div>
            </div>
          </div>
        )}

        {showTwoFactorDisable && (
          <div className="mt-6 p-5 bg-gray-900/60 rounded-xl border border-red-500/20">
            <h5 className="text-white font-semibold mb-4 flex items-center gap-2">
              <ShieldExclamationIcon className="h-5 w-5 text-red-400" />
              Disable Two-Factor Authentication
            </h5>
            <div className="space-y-4">
              <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-3">
                <p className="text-red-400 text-sm">Disabling 2FA will make your account less secure. You'll need to enter your current 2FA code or a backup code to confirm.</p>
              </div>
              <div>
                <label className="text-sm text-gray-300 mb-2 block">Enter your 2FA code or backup code:</label>
                <input
                  type="text"
                  value={disableCode}
                  onChange={(e) => setDisableCode(e.target.value.replace(/[^a-zA-Z0-9]/g, "").slice(0, 8).toUpperCase())}
                  placeholder="000000 or BACKUP"
                  className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-xl text-white text-center text-xl tracking-widest font-mono focus:outline-none focus:border-red-500 uppercase"
                  maxLength={8}
                  autoFocus
                />
                <p className="text-gray-500 text-xs mt-2 text-center">Enter 6-digit code from your authenticator app or 8-character backup code</p>
              </div>
              <div className="flex gap-3">
                <button
                  onClick={() => { setShowTwoFactorDisable(false); setDisableCode(""); }}
                  className="flex-1 px-4 py-2.5 text-gray-400 bg-gray-800 hover:bg-gray-700 rounded-xl transition-all"
                >
                  Cancel
                </button>
                <button
                  onClick={handleDisable2FA}
                  disabled={disableCode.length < 6 || processing2FA}
                  className="flex-1 px-4 py-2.5 text-white bg-gradient-to-r from-red-500 to-rose-500 hover:from-red-600 hover:to-rose-600 rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {processing2FA ? "Disabling..." : "Disable 2FA"}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="bg-gray-800/30 border border-gray-700/50 hover:border-blue-500/30 rounded-2xl p-6 transition-all duration-300">
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-gradient-to-br from-blue-500/20 to-cyan-500/20 rounded-xl">
              <DevicePhoneMobileIcon className="h-6 w-6 text-blue-400" />
            </div>
            <div>
              <h4 className="text-white font-semibold text-lg">Active Sessions</h4>
              <p className="text-gray-400 text-xs">
                {loadingSessions ? "Loading..." : `${activeSessions.length} device${activeSessions.length !== 1 ? "s" : ""} logged in`}
              </p>
            </div>
          </div>
          {activeSessions.length > 1 && (
            <button
              onClick={handleRevokeAllSessions}
              disabled={revokingSession === "all"}
              className="px-3 py-1.5 text-xs text-red-400 bg-red-500/10 hover:bg-red-500/20 border border-red-500/20 rounded-lg transition-all disabled:opacity-50"
            >
              {revokingSession === "all" ? "Signing out..." : "Sign out all others"}
            </button>
          )}
        </div>
        <div className="space-y-3">
          {loadingSessions ? (
            <div className="space-y-3">
              {[1, 2].map((i) => (
                <div key={i} className="p-4 rounded-xl bg-gray-900/40 animate-pulse">
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 bg-gray-700 rounded-xl" />
                    <div className="flex-1 space-y-2">
                      <div className="h-4 bg-gray-700 rounded w-1/3" />
                      <div className="h-3 bg-gray-700 rounded w-1/2" />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : activeSessions.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <DevicePhoneMobileIcon className="h-12 w-12 mx-auto mb-2 opacity-50" />
              <p>No active sessions found</p>
            </div>
          ) : (
            activeSessions.map((session) => (
              <div
                key={session.id}
                className={`flex items-center justify-between p-4 rounded-xl transition-all duration-300 ${
                  session.current
                    ? "bg-gradient-to-r from-indigo-500/10 to-purple-500/10 border border-indigo-500/20"
                    : "bg-gray-900/40 hover:bg-gray-900/60 border border-transparent"
                }`}
              >
                <div className="flex items-center gap-4">
                  <div className={`p-2.5 rounded-xl ${session.current ? "bg-indigo-500/20" : "bg-gray-700/50"}`}>
                    {session.device?.toLowerCase().includes("iphone") ||
                    session.device?.toLowerCase().includes("android") ||
                    session.device?.toLowerCase().includes("mobile") ? (
                      <DevicePhoneMobileIcon className={`h-5 w-5 ${session.current ? "text-indigo-400" : "text-gray-400"}`} />
                    ) : (
                      <ComputerDesktopIcon className={`h-5 w-5 ${session.current ? "text-indigo-400" : "text-gray-400"}`} />
                    )}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <p className="text-white font-medium text-sm">{session.device}</p>
                      <span className="text-gray-500 text-xs">&bull;</span>
                      <p className="text-gray-400 text-xs">{session.browser}</p>
                      {session.current && (
                        <span className="px-2 py-0.5 text-[10px] bg-emerald-500/20 text-emerald-400 rounded-full border border-emerald-500/30">Current</span>
                      )}
                    </div>
                    <div className="flex items-center gap-3 mt-1">
                      <span className="text-gray-500 text-xs flex items-center gap-1">
                        <MapPinIcon className="h-3 w-3" />
                        {session.location}
                      </span>
                      <span className="text-gray-500 text-xs flex items-center gap-1">
                        <ClockIcon className="h-3 w-3" />
                        {session.lastActive}
                      </span>
                      {session.ip && <span className="text-gray-500 text-xs">{session.ip}</span>}
                    </div>
                  </div>
                </div>
                {!session.current && (
                  <button
                    onClick={() => handleRevokeSession(session.id)}
                    disabled={revokingSession === session.id}
                    className="p-2 text-gray-400 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-all disabled:opacity-50"
                  >
                    {revokingSession === session.id ? (
                      <ArrowPathIcon className="h-4 w-4 animate-spin" />
                    ) : (
                      <XMarkIcon className="h-4 w-4" />
                    )}
                  </button>
                )}
              </div>
            ))
          )}
        </div>
      </div>

      <div className="bg-gray-800/30 border border-gray-700/50 hover:border-indigo-500/30 rounded-2xl p-6 transition-all duration-300">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2.5 bg-gradient-to-br from-indigo-500/20 to-purple-500/20 rounded-xl">
            <LockClosedIcon className="h-6 w-6 text-indigo-400" />
          </div>
          <div>
            <h3 className="text-white font-semibold text-lg">Change Password</h3>
            <p className="text-gray-500 text-sm">Keep your account secure with a strong password</p>
          </div>
        </div>

        <form onSubmit={handlePasswordChange} className="space-y-5">
          <div>
            <label className="text-sm font-medium text-gray-300 mb-2.5 flex items-center gap-2">
              <KeyIcon className="h-4 w-4 text-gray-500" />
              Current Password
            </label>
            <div className="relative group">
              <input
                type={showPasswords.current ? "text" : "password"}
                name="current_password"
                value={passwordData.current_password}
                onChange={handlePasswordInputChange}
                className="w-full pl-4 pr-12 py-3.5 bg-gray-900/70 border border-gray-700 hover:border-gray-600 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 transition-all duration-300"
                placeholder="Enter current password"
                required
              />
              <button
                type="button"
                onClick={() => setShowPasswords((prev) => ({ ...prev, current: !prev.current }))}
                className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-500 hover:text-white transition-colors p-1"
              >
                {showPasswords.current ? <EyeSlashIcon className="h-5 w-5" /> : <EyeIcon className="h-5 w-5" />}
              </button>
            </div>
          </div>

          <div>
            <label className="text-sm font-medium text-gray-300 mb-2.5 flex items-center gap-2">
              <FingerPrintIcon className="h-4 w-4 text-gray-500" />
              New Password
            </label>
            <div className="relative group">
              <input
                type={showPasswords.new ? "text" : "password"}
                name="new_password"
                value={passwordData.new_password}
                onChange={handlePasswordInputChange}
                className="w-full pl-4 pr-12 py-3.5 bg-gray-900/70 border border-gray-700 hover:border-gray-600 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 transition-all duration-300"
                placeholder="Enter new password"
                required
              />
              <button
                type="button"
                onClick={() => setShowPasswords((prev) => ({ ...prev, new: !prev.new }))}
                className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-500 hover:text-white transition-colors p-1"
              >
                {showPasswords.new ? <EyeSlashIcon className="h-5 w-5" /> : <EyeIcon className="h-5 w-5" />}
              </button>
            </div>
            {passwordData.new_password && (
              <div className="mt-3 space-y-2">
                <div className="flex gap-1.5">
                  {[1, 2, 3, 4, 5].map((level) => (
                    <div
                      key={level}
                      className={`h-1.5 flex-1 rounded-full transition-all duration-500 ${
                        level <= passwordStrength.strength ? passwordStrength.color : "bg-gray-700"
                      }`}
                    />
                  ))}
                </div>
                <div className="flex items-center justify-between">
                  <p className="text-xs text-gray-500">
                    Password strength:{" "}
                    <span className={
                      passwordStrength.strength >= 4 ? "text-green-400" : passwordStrength.strength >= 3 ? "text-yellow-400" : "text-red-400"
                    }>
                      {passwordStrength.label}
                    </span>
                  </p>
                  <div className="flex gap-2 text-xs">
                    {[
                      { label: "8+", active: passwordData.new_password.length >= 8 },
                      { label: "a-z", active: /[a-z]/.test(passwordData.new_password) },
                      { label: "A-Z", active: /[A-Z]/.test(passwordData.new_password) },
                      { label: "0-9", active: /[0-9]/.test(passwordData.new_password) },
                      { label: "@#$", active: /[^a-zA-Z0-9]/.test(passwordData.new_password) },
                    ].map((req, i) => (
                      <span
                        key={i}
                        className={`px-1.5 py-0.5 rounded ${req.active ? "bg-emerald-500/20 text-emerald-400" : "bg-gray-700/50 text-gray-500"}`}
                      >
                        {req.label}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>

          <div>
            <label className="text-sm font-medium text-gray-300 mb-2.5 flex items-center gap-2">
              <CheckCircleIcon className="h-4 w-4 text-gray-500" />
              Confirm New Password
            </label>
            <div className="relative group">
              <input
                type={showPasswords.confirm ? "text" : "password"}
                name="confirm_password"
                value={passwordData.confirm_password}
                onChange={handlePasswordInputChange}
                className={`w-full pl-4 pr-12 py-3.5 bg-gray-900/70 border rounded-xl text-white placeholder-gray-500 focus:outline-none focus:ring-2 transition-all duration-300 ${
                  passwordData.confirm_password && passwordData.new_password !== passwordData.confirm_password
                    ? "border-red-500 focus:border-red-500 focus:ring-red-500/20"
                    : passwordData.confirm_password && passwordData.new_password === passwordData.confirm_password
                    ? "border-green-500 focus:border-green-500 focus:ring-green-500/20"
                    : "border-gray-700 hover:border-gray-600 focus:border-indigo-500 focus:ring-indigo-500/20"
                }`}
                placeholder="Confirm new password"
                required
              />
              <button
                type="button"
                onClick={() => setShowPasswords((prev) => ({ ...prev, confirm: !prev.confirm }))}
                className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-500 hover:text-white transition-colors p-1"
              >
                {showPasswords.confirm ? <EyeSlashIcon className="h-5 w-5" /> : <EyeIcon className="h-5 w-5" />}
              </button>
            </div>
            {passwordData.confirm_password && passwordData.new_password !== passwordData.confirm_password && (
              <p className="text-xs text-red-400 mt-2 flex items-center gap-1">
                <XMarkIcon className="h-3.5 w-3.5" />
                Passwords don't match
              </p>
            )}
            {passwordData.confirm_password && passwordData.new_password === passwordData.confirm_password && (
              <p className="text-xs text-green-400 mt-2 flex items-center gap-1">
                <CheckIcon className="h-3.5 w-3.5" />
                Passwords match
              </p>
            )}
          </div>

          <button
            type="submit"
            disabled={isChangingPassword || !passwordData.current_password || !passwordData.new_password || passwordData.new_password !== passwordData.confirm_password}
            className="w-full py-4 px-6 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 text-white font-semibold rounded-xl hover:from-indigo-600 hover:via-purple-600 hover:to-pink-600 shadow-lg shadow-purple-500/25 hover:shadow-purple-500/40 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none flex items-center justify-center gap-2 group relative overflow-hidden"
          >
            <div className="absolute inset-0 bg-gradient-to-r from-white/0 via-white/20 to-white/0 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700" />
            {isChangingPassword ? (
              <>
                <ArrowPathIcon className="w-5 h-5 animate-spin" />
                Updating Password...
              </>
            ) : (
              <>
                <ShieldCheckIcon className="h-5 w-5 group-hover:scale-110 transition-transform" />
                Update Password
              </>
            )}
          </button>
        </form>
      </div>

      <div className="bg-gradient-to-br from-red-500/10 via-rose-500/5 to-pink-500/10 border border-red-500/20 rounded-2xl p-6 group hover:border-red-500/40 transition-all duration-300">
        <div className="flex items-start gap-4">
          <div className="p-3 bg-gradient-to-br from-red-500/20 to-rose-500/20 rounded-xl group-hover:scale-110 transition-transform duration-300">
            <ArrowRightOnRectangleIcon className="h-6 w-6 text-red-400" />
          </div>
          <div className="flex-1">
            <h3 className="text-white font-semibold text-lg mb-1">Sign Out</h3>
            <p className="text-gray-400 text-sm mb-4">Sign out from this device. You'll need to log in again to access your account.</p>
            <button
              onClick={onLogout}
              className="w-full py-3.5 px-6 bg-red-500/20 hover:bg-red-500/30 border border-red-500/30 hover:border-red-500/50 text-red-400 font-semibold rounded-xl transition-all duration-300 flex items-center justify-center gap-2 group/btn"
            >
              <ArrowRightOnRectangleIcon className="h-5 w-5 group-hover/btn:translate-x-1 transition-transform" />
              Sign Out
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
