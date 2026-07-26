import { useState, useEffect, useMemo, useCallback, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ParticleBackground } from "../../styles/components";
import {
  UserCircleIcon,
  PencilIcon,
  XMarkIcon,
  ShieldCheckIcon,
  SparklesIcon,
  BellIcon,
  CameraIcon,
  DocumentDuplicateIcon,
  TrophyIcon,
} from "@heroicons/react/24/outline";
import { CheckIcon } from "@heroicons/react/24/solid";
import toast from "react-hot-toast";
import { useAuth } from "./AuthContext";
import { authAPI } from "../../services/api";
import { SecuritySettings } from "./SecuritySettings";
import { NotificationPreferences } from "./NotificationPreferences";
import { ProfileInfo } from "./ProfileInfo";
import { AccountInfo } from "./AccountInfo";
import { AvatarCropModal } from "./AvatarCropModal";

/**
 * UserProfile Component
 * Comprehensive profile management modal with enhanced UI/UX
 */
export const UserProfile = ({ onClose }) => {
  const { user, updateProfile, logout, resendVerificationEmail, refreshUserProfile } = useAuth();
  const [activeTab, setActiveTab] = useState("profile");
  const [isEditing, setIsEditing] = useState(false);
  const [isUpdating, setIsUpdating] = useState(false);
  const [isClosing, setIsClosing] = useState(false);
  const [_hoveredCard, _setHoveredCard] = useState(null);
  const [copied, setCopied] = useState(false);
  const fileInputRef = useRef(null);
  const [avatarPreview, setAvatarPreview] = useState(null);

  // Avatar crop modal state
  const [showAvatarModal, setShowAvatarModal] = useState(false);
  const [avatarSource, setAvatarSource] = useState(null);
  const [crop, setCrop] = useState({ x: 0, y: 0 });
  const [zoom, setZoom] = useState(1);
  const [croppedAreaPixels, setCroppedAreaPixels] = useState(null);
  const [savingAvatar, setSavingAvatar] = useState(false);

  // Two-factor auth state (shared with header's security score)
  const [twoFactorEnabled, setTwoFactorEnabled] = useState(false);

  // Get user initials for avatar
  const userInitials = useMemo(() => {
    if (user?.full_name) {
      const names = user.full_name.split(" ");
      return names.length > 1
        ? `${names[0][0]}${names[names.length - 1][0]}`.toUpperCase()
        : names[0].substring(0, 2).toUpperCase();
    }
    return user?.username?.substring(0, 2).toUpperCase() || "U";
  }, [user]);

  // Generate avatar gradient based on username
  const avatarGradient = useMemo(() => {
    const gradients = [
      "from-violet-500 via-purple-500 to-fuchsia-500",
      "from-cyan-500 via-violet-500 to-indigo-500",
      "from-emerald-500 via-teal-500 to-cyan-500",
      "from-orange-500 via-red-500 to-pink-500",
      "from-yellow-500 via-orange-500 to-red-500",
      "from-pink-500 via-rose-500 to-red-500",
    ];
    const index = (user?.username?.charCodeAt(0) || 0) % gradients.length;
    return gradients[index];
  }, [user]);

  // Profile completion percentage
  const profileCompletion = useMemo(() => {
    const fields = [
      user?.full_name,
      user?.organization,
      user?.phone,
      user?.is_email_verified,
      twoFactorEnabled,
      user?.avatar_url || avatarPreview,
    ];
    const filled = fields.filter(Boolean).length;
    return Math.round((filled / fields.length) * 100);
  }, [user, twoFactorEnabled, avatarPreview]);

  // Reset form when user changes
  useEffect(() => {
    if (user) {
      if (typeof user.two_factor_enabled === "boolean") {
        setTwoFactorEnabled(user.two_factor_enabled);
      }
    }
  }, [user]);

  // Prevent background scrolling when modal is open
  useEffect(() => {
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = "unset";
    };
  }, []);

  // Handle close with animation
  const handleClose = () => {
    setIsClosing(true);
    setTimeout(() => {
      onClose();
    }, 300);
  };

  // ===== PROFILE HANDLERS =====
  const [formData, setFormData] = useState({
    full_name: user?.full_name || "",
    organization: user?.organization || "",
    department: user?.department || "",
    phone: user?.phone || "",
    timezone: user?.timezone || "UTC",
  });

  useEffect(() => {
    if (user) {
      setFormData({
        full_name: user.full_name || "",
        organization: user.organization || "",
        department: user.department || "",
        phone: user.phone || "",
        timezone: user.timezone || "UTC",
      });
    }
  }, [user]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSaveProfile = async () => {
    setIsUpdating(true);
    try {
      await updateProfile(formData);
      setIsEditing(false);
    } catch (error) {
      // Error is handled by updateProfile in AuthContext
    } finally {
      setIsUpdating(false);
    }
  };

  const handleCancel = () => {
    setFormData({
      full_name: user?.full_name || "",
      organization: user?.organization || "",
      department: user?.department || "",
      phone: user?.phone || "",
      timezone: user?.timezone || "UTC",
    });
    setIsEditing(false);
  };

  const handleResendVerification = async () => {
    try {
      await resendVerificationEmail(user?.email);
    } catch (error) {
      // Error handled in AuthContext
    }
  };

  // ===== AVATAR HANDLERS =====
  const createCroppedImage = useCallback(async (imageSrc, pixelCrop) => {
    return new Promise((resolve, reject) => {
      const image = new Image();
      image.crossOrigin = "anonymous";
      image.onload = () => {
        const canvas = document.createElement("canvas");
        const ctx = canvas.getContext("2d");
        const outputSize = 400;
        canvas.width = outputSize;
        canvas.height = outputSize;
        ctx.drawImage(
          image,
          pixelCrop.x,
          pixelCrop.y,
          pixelCrop.width,
          pixelCrop.height,
          0,
          0,
          outputSize,
          outputSize
        );
        const base64 = canvas.toDataURL("image/jpeg", 0.92);
        resolve(base64);
      };
      image.onerror = () => reject(new Error("Failed to load image"));
      image.src = imageSrc;
    });
  }, []);

  const handleAvatarSelect = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      if (file.size > 10 * 1024 * 1024) {
        toast.error("Image must be less than 10MB");
        return;
      }
      if (!file.type.startsWith("image/")) {
        toast.error("Please select an image file");
        return;
      }
      const reader = new FileReader();
      reader.onloadend = () => {
        setAvatarSource(reader.result);
        setShowAvatarModal(true);
        setCrop({ x: 0, y: 0 });
        setZoom(1);
      };
      reader.readAsDataURL(file);
    }
    e.target.value = "";
  };

  const onCropComplete = useCallback((croppedArea, croppedAreaPixels) => {
    setCroppedAreaPixels(croppedAreaPixels);
  }, []);

  const handleSaveAvatar = async () => {
    if (!avatarSource || !croppedAreaPixels) return;
    try {
      setSavingAvatar(true);
      const croppedImage = await createCroppedImage(avatarSource, croppedAreaPixels);
      await authAPI.updateAvatar(croppedImage);
      setAvatarPreview(croppedImage);
      setShowAvatarModal(false);
      setAvatarSource(null);
      toast.success("Avatar updated successfully!");
      if (refreshUserProfile) refreshUserProfile();
    } catch (error) {
      toast.error("Failed to save avatar");
    } finally {
      setSavingAvatar(false);
    }
  };

  const handleRemoveAvatar = async () => {
    try {
      setSavingAvatar(true);
      await authAPI.updateAvatar("");
      setAvatarPreview(null);
      setShowAvatarModal(false);
      setAvatarSource(null);
      toast.success("Avatar removed");
      if (refreshUserProfile) refreshUserProfile();
    } catch (error) {
      toast.error("Failed to remove avatar");
    } finally {
      setSavingAvatar(false);
    }
  };

  const handleCancelAvatarEdit = () => {
    setShowAvatarModal(false);
    setAvatarSource(null);
    setCrop({ x: 0, y: 0 });
    setZoom(1);
  };

  const handleAvatarClick = () => {
    setAvatarSource(null);
    setShowAvatarModal(true);
    setCrop({ x: 0, y: 0 });
    setZoom(1);
  };

  const handleLogout = () => {
    logout();
    handleClose();
  };

  // ===== UTILITY FUNCTIONS =====
  const formatDate = (dateString) => {
    if (!dateString) return "N/A";
    const date = new Date(dateString.endsWith("Z") ? dateString : dateString + "Z");
    return date.toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" });
  };

  const formatDateTime = (dateString) => {
    if (!dateString) return "Never";
    const date = new Date(dateString.endsWith("Z") ? dateString : dateString + "Z");
    return date.toLocaleString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const copyToClipboard = useCallback((text) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    toast.success("Copied to clipboard!");
    setTimeout(() => setCopied(false), 2000);
  }, []);

  const timezones = [
    "UTC",
    "America/New_York",
    "America/Chicago",
    "America/Denver",
    "America/Los_Angeles",
    "Europe/London",
    "Europe/Paris",
    "Europe/Berlin",
    "Asia/Tokyo",
    "Asia/Shanghai",
    "Asia/Kolkata",
    "Australia/Sydney",
  ];

  // ===== SECURITY SCORE =====
  const securityScore = useMemo(() => {
    let score = 0;
    const factors = [];
    if (user?.is_email_verified) {
      score += 25;
      factors.push({ name: "Email Verified", completed: true });
    } else {
      factors.push({ name: "Email Verified", completed: false });
    }
    if (user?.phone) {
      score += 15;
      factors.push({ name: "Phone Added", completed: true });
    } else {
      factors.push({ name: "Phone Added", completed: false });
    }
    if (twoFactorEnabled) {
      score += 30;
      factors.push({ name: "2FA Enabled", completed: true });
    } else {
      factors.push({ name: "2FA Enabled", completed: false });
    }
    if (user?.organization) {
      score += 10;
      factors.push({ name: "Organization Set", completed: true });
    } else {
      factors.push({ name: "Organization Set", completed: false });
    }
    score += 20;
    factors.push({ name: "Strong Password", completed: true });
    return { score, factors };
  }, [user, twoFactorEnabled]);

  const getSecurityScoreColor = (score) => {
    if (score >= 80)
      return {
        gradient: "from-emerald-500 to-green-500",
        text: "text-emerald-400",
        bg: "bg-emerald-500",
      };
    if (score >= 60)
      return {
        gradient: "from-yellow-500 to-amber-500",
        text: "text-yellow-400",
        bg: "bg-yellow-500",
      };
    if (score >= 40)
      return {
        gradient: "from-orange-500 to-red-500",
        text: "text-orange-400",
        bg: "bg-orange-500",
      };
    return { gradient: "from-red-500 to-rose-500", text: "text-red-400", bg: "bg-red-500" };
  };

  const tabs = [
    { key: "profile", label: "Profile", icon: UserCircleIcon },
    { key: "account", label: "Account", icon: SparklesIcon },
    { key: "security", label: "Security", icon: ShieldCheckIcon },
    { key: "notifications", label: "Alerts", icon: BellIcon },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <AnimatePresence>
        {!isClosing && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-gradient-to-br from-black/80 via-gray-900/90 to-black/80 backdrop-blur-xl"
            onClick={handleClose}
          />
        )}
      </AnimatePresence>

      {/* Floating particles */}
      <ParticleBackground />

      {/* Modal */}
      <AnimatePresence>
        {!isClosing && (
          <motion.div
            key="modal"
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ type: "spring", damping: 25, stiffness: 300 }}
            className="relative w-full max-w-3xl max-h-[92vh] overflow-hidden bg-gradient-to-br from-gray-900/95 via-gray-900/98 to-gray-800/95 rounded-3xl shadow-2xl shadow-cyan-500/10 border border-gray-700/50"
          >
        {/* Animated Background Effects */}
        <ParticleBackground />

        {/* Header */}
        <div className="relative border-b border-gray-700/50 bg-gradient-to-r from-gray-900/50 to-gray-800/50 backdrop-blur-sm">
          <div className="p-6 pb-4">
            <div className="flex items-start justify-between">
              {/* Profile Header */}
              <div className="flex items-center gap-5">
                {/* Avatar */}
                <div className="relative group">
                  <div className="absolute -inset-1 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 rounded-2xl opacity-75 blur group-hover:opacity-100 transition-opacity duration-300" />
                  <div
                    className={`relative w-20 h-20 bg-gradient-to-br ${avatarGradient} rounded-2xl flex items-center justify-center shadow-xl transition-all duration-300 group-hover:scale-105 overflow-hidden cursor-pointer`}
                    onClick={handleAvatarClick}
                  >
                    {avatarPreview || user?.avatar_url ? (
                      <img
                        src={avatarPreview || user?.avatar_url}
                        alt="Avatar"
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <span className="text-2xl font-bold text-white drop-shadow-lg">
                        {userInitials}
                      </span>
                    )}
                    <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 flex items-center justify-center transition-all duration-300">
                      {avatarPreview || user?.avatar_url ? (
                        <PencilIcon className="h-6 w-6 text-white" />
                      ) : (
                        <CameraIcon className="h-6 w-6 text-white" />
                      )}
                    </div>
                  </div>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/*"
                    onChange={handleAvatarSelect}
                    className="hidden"
                  />
                  {user?.is_email_verified && (
                    <div className="absolute -bottom-1 -right-1 w-7 h-7 bg-gradient-to-r from-emerald-400 to-green-500 rounded-full flex items-center justify-center border-3 border-gray-900 shadow-lg shadow-emerald-500/30 animate-bounce-subtle">
                      <CheckIcon className="h-4 w-4 text-white" />
                    </div>
                  )}
                  {user?.role === "admin" && (
                    <div className="absolute -top-2 -right-2 w-7 h-7 bg-gradient-to-r from-amber-400 to-orange-500 rounded-full flex items-center justify-center border-2 border-gray-900 shadow-lg shadow-amber-500/30">
                      <SparklesIcon className="h-4 w-4 text-white" />
                    </div>
                  )}
                </div>

                <div className="space-y-1">
                  <div className="flex items-center gap-3">
                    <h2 className="text-2xl font-bold bg-gradient-to-r from-white via-gray-100 to-gray-300 bg-clip-text text-transparent">
                      {user?.full_name || user?.username || "User"}
                    </h2>
                    {user?.role === "admin" && (
                      <span className="px-2 py-0.5 bg-gradient-to-r from-amber-500/20 to-orange-500/20 border border-amber-500/30 rounded-full text-xs font-semibold text-amber-400">
                        Admin
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <p className="text-gray-400 text-sm flex items-center gap-1.5 font-mono">
                      <span className="text-indigo-400">@</span>
                      {user?.username}
                    </p>
                    <button
                      onClick={() => copyToClipboard(user?.username)}
                      className="p-1 hover:bg-gray-700/50 rounded-lg focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900 transition-colors"
                      title="Copy username"
                    >
                      <DocumentDuplicateIcon
                        className={`h-3.5 w-3.5 ${copied ? "text-green-400" : "text-gray-500 hover:text-gray-300"}`}
                      />
                    </button>
                  </div>
                  <div className="flex items-center gap-3 mt-3">
                    <div className="relative h-2 w-32 bg-gray-700/50 rounded-full overflow-hidden">
                      <div
                        className="absolute inset-y-0 left-0 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 rounded-full transition-all duration-700 ease-out"
                        style={{ width: `${profileCompletion}%` }}
                      />
                      <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-shimmer" />
                    </div>
                    <span className="text-xs font-medium text-gray-400">
                      {profileCompletion}% complete
                    </span>
                    {profileCompletion === 100 && (
                      <TrophyIcon className="h-4 w-4 text-yellow-400 animate-bounce-subtle" />
                    )}
                  </div>
                </div>
              </div>

              <button
                onClick={handleClose}
                aria-label="Close profile"
                className="p-2.5 hover:bg-red-500/10 hover:border-red-500/30 border border-transparent rounded-xl focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900 transition-all duration-300 group"
              >
                <XMarkIcon className="h-5 w-5 text-gray-400 group-hover:text-red-400 group-hover:rotate-90 transition-all duration-300" />
              </button>
            </div>

            {/* Tabs */}
            <div className="flex gap-1 mt-6 p-1.5 bg-gray-800/60 rounded-2xl backdrop-blur-sm border border-gray-700/50">
              {tabs.map((tab) => (
                <motion.button
                  key={tab.key}
                  onClick={() => setActiveTab(tab.key)}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className={`relative flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-xl text-sm font-medium focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900 transition-colors duration-300 ${
                    activeTab === tab.key
                      ? "text-white"
                      : "text-gray-400 hover:text-gray-300 hover:bg-gray-700/50"
                  }`}
                >
                  {activeTab === tab.key && (
                    <motion.div
                      layoutId="activeTab"
                      className="absolute inset-0 bg-gradient-to-r from-cyan-500/20 via-violet-500/20 to-pink-500/20 rounded-xl border border-cyan-500/30 shadow-lg shadow-violet-500/10"
                    />
                  )}
                  <tab.icon
                    className={`h-4 w-4 relative z-10 transition-transform duration-300 ${activeTab === tab.key ? "scale-110" : ""}`}
                  />
                  <span className="relative z-10 hidden sm:inline">{tab.label}</span>
                  {tab.key === "security" && securityScore.score < 80 && (
                    <span className="relative z-10 w-2 h-2 bg-amber-500 rounded-full animate-pulse" />
                  )}
                </motion.button>
              ))}
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="relative overflow-y-auto max-h-[calc(92vh-220px)] p-6 scrollbar-thin scrollbar-thumb-cyan-500/30 scrollbar-track-transparent hover:scrollbar-thumb-violet-500/50">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -12 }}
              transition={{ duration: 0.2 }}
            >
              {/* Profile Tab */}
              {activeTab === "profile" && (
                <ProfileInfo
                  user={user}
                  securityScore={securityScore}
                  getSecurityScoreColor={getSecurityScoreColor}
                  setHoveredCard={_setHoveredCard}
                  isEditing={isEditing}
                  formData={formData}
                  handleInputChange={handleInputChange}
                  isUpdating={isUpdating}
                  handleSaveProfile={handleSaveProfile}
                  handleCancel={handleCancel}
                  setIsEditing={setIsEditing}
                  formatDate={formatDate}
                  formatDateTime={formatDateTime}
                  timezones={timezones}
                />
              )}

              {/* Account Tab */}
              {activeTab === "account" && (
                <AccountInfo
                  user={user}
                  handleResendVerification={handleResendVerification}
                  formatDate={formatDate}
                  formatDateTime={formatDateTime}
                />
              )}

              {/* Security Tab */}
              {activeTab === "security" && (
                <SecuritySettings
                  securityScore={securityScore}
                  getSecurityScoreColor={getSecurityScoreColor}
                  onLogout={handleLogout}
                />
              )}

              {/* Notifications Tab */}
              {activeTab === "notifications" && <NotificationPreferences />}
            </motion.div>
          </AnimatePresence>
        </div>
          </motion.div>
        )}
      </AnimatePresence>

      <AvatarCropModal
        showAvatarModal={showAvatarModal}
        avatarSource={avatarSource}
        crop={crop}
        zoom={zoom}
        croppedAreaPixels={croppedAreaPixels}
        savingAvatar={savingAvatar}
        avatarPreview={avatarPreview}
        user={user}
        fileInputRef={fileInputRef}
        handleCancelAvatarEdit={handleCancelAvatarEdit}
        handleSaveAvatar={handleSaveAvatar}
        handleRemoveAvatar={handleRemoveAvatar}
        onCropComplete={onCropComplete}
        setCrop={setCrop}
        setZoom={setZoom}
        handleAvatarSelect={handleAvatarSelect}
      />
    </div>
  );
};
