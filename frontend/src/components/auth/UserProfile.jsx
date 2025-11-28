import React, {
  useState,
  useEffect,
  useMemo,
  useCallback,
  useRef,
} from "react";
import Cropper from "react-easy-crop";
import {
  UserCircleIcon,
  EnvelopeIcon,
  BuildingOfficeIcon,
  CheckBadgeIcon,
  PencilIcon,
  KeyIcon,
  XMarkIcon,
  PhoneIcon,
  GlobeAltIcon,
  ShieldCheckIcon,
  EyeIcon,
  EyeSlashIcon,
  Cog6ToothIcon,
  ArrowRightOnRectangleIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ClockIcon,
  UserGroupIcon,
  CalendarIcon,
  SparklesIcon,
  LockClosedIcon,
  FingerPrintIcon,
  BellIcon,
  DevicePhoneMobileIcon,
  ComputerDesktopIcon,
  MapPinIcon,
  CameraIcon,
  ArrowPathIcon,
  ChevronRightIcon,
  InformationCircleIcon,
  DocumentDuplicateIcon,
  ShieldExclamationIcon,
  BoltIcon,
  StarIcon,
  TrophyIcon,
  FireIcon,
  CommandLineIcon,
  ChartBarIcon,
  QrCodeIcon,
  TrashIcon,
  PhotoIcon,
  ArrowsPointingOutIcon,
} from "@heroicons/react/24/outline";
import { CheckIcon, HeartIcon } from "@heroicons/react/24/solid";
import toast from "react-hot-toast";
import { useAuth } from "./AuthContext";
import { authAPI } from "../../services/api";

/**
 * UserProfile Component
 * Comprehensive profile management modal with enhanced UI/UX
 */
export const UserProfile = ({ onClose }) => {
  const {
    user,
    updateProfile,
    logout,
    resendVerificationEmail,
    refreshUserProfile,
  } = useAuth();
  const [activeTab, setActiveTab] = useState("profile");
  const [isEditing, setIsEditing] = useState(false);
  const [isUpdating, setIsUpdating] = useState(false);
  const [isClosing, setIsClosing] = useState(false);
  const [hoveredCard, setHoveredCard] = useState(null);
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

  // Loading states
  const [loadingNotifications, setLoadingNotifications] = useState(true);
  const [loadingSessions, setLoadingSessions] = useState(true);
  const [loading2FA, setLoading2FA] = useState(true);

  // Notification preferences - fetched from API
  const [notifications, setNotifications] = useState({
    email: true,
    push: true,
    security: true,
    updates: false,
    marketing: false,
  });
  const [savingNotifications, setSavingNotifications] = useState(false);

  // Two-factor auth state
  const [twoFactorEnabled, setTwoFactorEnabled] = useState(false);
  const [twoFactorSetupData, setTwoFactorSetupData] = useState(null);
  const [twoFactorCode, setTwoFactorCode] = useState("");
  const [showTwoFactorSetup, setShowTwoFactorSetup] = useState(false);
  const [showTwoFactorDisable, setShowTwoFactorDisable] = useState(false);
  const [disableCode, setDisableCode] = useState("");
  const [processing2FA, setProcessing2FA] = useState(false);
  const [backupCodesRemaining, setBackupCodesRemaining] = useState(0);

  // Sessions state - fetched from API
  const [activeSessions, setActiveSessions] = useState([]);
  const [revokingSession, setRevokingSession] = useState(null);

  // Profile form data
  const [formData, setFormData] = useState({
    full_name: user?.full_name || "",
    organization: user?.organization || "",
    department: user?.department || "",
    phone: user?.phone || "",
    timezone: user?.timezone || "UTC",
  });

  // Password change form data
  const [passwordData, setPasswordData] = useState({
    current_password: "",
    new_password: "",
    confirm_password: "",
  });
  const [showPasswords, setShowPasswords] = useState({
    current: false,
    new: false,
    confirm: false,
  });
  const [isChangingPassword, setIsChangingPassword] = useState(false);
  const [isResendingVerification, setIsResendingVerification] = useState(false);

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
      "from-cyan-500 via-blue-500 to-indigo-500",
      "from-emerald-500 via-teal-500 to-cyan-500",
      "from-orange-500 via-red-500 to-pink-500",
      "from-yellow-500 via-orange-500 to-red-500",
      "from-pink-500 via-rose-500 to-red-500",
    ];
    const index = (user?.username?.charCodeAt(0) || 0) % gradients.length;
    return gradients[index];
  }, [user]);

  // Profile completion percentage
  // 100% when: full_name, organization, phone, email verified, 2FA enabled, and avatar set
  const profileCompletion = useMemo(() => {
    const fields = [
      user?.full_name, // ~17% - Has full name
      user?.organization, // ~17% - Has organization
      user?.phone, // ~17% - Has phone number
      user?.is_email_verified, // ~17% - Email verified
      twoFactorEnabled, // ~17% - 2FA enabled
      user?.avatar_url || avatarPreview, // ~17% - Has avatar
    ];
    const filled = fields.filter(Boolean).length;
    return Math.round((filled / fields.length) * 100);
  }, [user, twoFactorEnabled, avatarPreview]);

  // Reset form when user changes
  useEffect(() => {
    if (user) {
      setFormData({
        full_name: user.full_name || "",
        organization: user.organization || "",
        department: user.department || "",
        phone: user.phone || "",
        timezone: user.timezone || "UTC",
      });
      // Update 2FA status from user data if available
      if (typeof user.two_factor_enabled === "boolean") {
        setTwoFactorEnabled(user.two_factor_enabled);
      }
    }
  }, [user]);

  // Fetch notification preferences
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
        console.log("Could not fetch notification preferences, using defaults");
      } finally {
        setLoadingNotifications(false);
      }
    };
    fetchNotifications();
  }, []);

  // Fetch 2FA status
  useEffect(() => {
    const fetch2FAStatus = async () => {
      try {
        setLoading2FA(true);
        const status = await authAPI.get2FAStatus();
        setTwoFactorEnabled(status.enabled);
        setBackupCodesRemaining(status.backup_codes_remaining || 0);
      } catch (error) {
        console.log("Could not fetch 2FA status");
      } finally {
        setLoading2FA(false);
      }
    };
    fetch2FAStatus();
  }, []);

  // Fetch active sessions
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
            lastActive: session.is_current
              ? "Now"
              : formatRelativeTime(session.last_active),
            createdAt: session.created_at,
          }))
        );
      } catch (error) {
        console.log("Could not fetch sessions");
        setActiveSessions([]);
      } finally {
        setLoadingSessions(false);
      }
    };
    fetchSessions();
  }, []);

  // Format relative time
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
    if (diffHours < 24)
      return `${diffHours} hour${diffHours > 1 ? "s" : ""} ago`;
    return `${diffDays} day${diffDays > 1 ? "s" : ""} ago`;
  };

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
    }, 200);
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handlePasswordInputChange = (e) => {
    const { name, value } = e.target;
    setPasswordData((prev) => ({
      ...prev,
      [name]: value,
    }));
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
      setPasswordData({
        current_password: "",
        new_password: "",
        confirm_password: "",
      });
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to change password");
    } finally {
      setIsChangingPassword(false);
    }
  };

  const handleResendVerification = async () => {
    setIsResendingVerification(true);
    try {
      await resendVerificationEmail();
    } catch (error) {
      // Error handled in AuthContext
    } finally {
      setIsResendingVerification(false);
    }
  };

  const handleLogout = () => {
    logout();
    handleClose();
  };

  // ===== NOTIFICATION HANDLERS =====
  const handleNotificationToggle = async (key) => {
    const newValue = !notifications[key];
    const prevNotifications = { ...notifications };

    // Optimistic update
    setNotifications((prev) => ({ ...prev, [key]: newValue }));

    try {
      setSavingNotifications(true);
      await authAPI.updateNotificationPreferences({ [key]: newValue });
    } catch (error) {
      // Revert on error
      setNotifications(prevNotifications);
      toast.error("Failed to update notification preferences");
    } finally {
      setSavingNotifications(false);
    }
  };

  // ===== TWO-FACTOR AUTHENTICATION HANDLERS =====
  const handleSetup2FA = async () => {
    try {
      setProcessing2FA(true);
      const setupData = await authAPI.setup2FA();
      setTwoFactorSetupData(setupData);
      setShowTwoFactorSetup(true);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to setup 2FA");
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
      toast.error(error.response?.data?.detail || "Invalid verification code");
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
      toast.error(error.response?.data?.detail || "Invalid verification code");
    } finally {
      setProcessing2FA(false);
    }
  };

  // ===== SESSION HANDLERS =====
  const handleRevokeSession = async (sessionId) => {
    try {
      setRevokingSession(sessionId);
      await authAPI.revokeSession(sessionId);
      setActiveSessions((prev) => prev.filter((s) => s.id !== sessionId));
      toast.success("Session terminated");
    } catch (error) {
      toast.error(
        error.response?.data?.detail || "Failed to terminate session"
      );
    } finally {
      setRevokingSession(null);
    }
  };

  const handleRevokeAllSessions = async () => {
    if (!confirm("Are you sure you want to terminate all other sessions?"))
      return;

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

  // ===== AVATAR HANDLERS =====

  // Create cropped image from canvas
  const createCroppedImage = useCallback(async (imageSrc, pixelCrop) => {
    return new Promise((resolve, reject) => {
      const image = new Image();
      image.crossOrigin = "anonymous";

      image.onload = () => {
        const canvas = document.createElement("canvas");
        const ctx = canvas.getContext("2d");

        // Set canvas size to 400x400 for high quality avatar
        const outputSize = 400;
        canvas.width = outputSize;
        canvas.height = outputSize;

        // Draw the cropped area scaled to output size
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

        // Convert to base64 with good quality
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
    // Reset the input so same file can be selected again
    e.target.value = "";
  };

  const onCropComplete = useCallback((croppedArea, croppedAreaPixels) => {
    setCroppedAreaPixels(croppedAreaPixels);
  }, []);

  const handleSaveAvatar = async () => {
    if (!avatarSource || !croppedAreaPixels) return;

    try {
      setSavingAvatar(true);
      const croppedImage = await createCroppedImage(
        avatarSource,
        croppedAreaPixels
      );

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
      console.error("Remove avatar error:", error);
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

  // Open avatar modal for editing existing avatar or just to remove
  const handleAvatarClick = () => {
    // Open modal - show preview mode (avatarSource = null means preview, not crop)
    setAvatarSource(null);
    setShowAvatarModal(true);
    setCrop({ x: 0, y: 0 });
    setZoom(1);
  };

  const formatDate = (dateString) => {
    if (!dateString) return "N/A";
    // Ensure the date is treated as UTC if no timezone specified
    const date = new Date(
      dateString.endsWith("Z") ? dateString : dateString + "Z"
    );
    return date.toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  };

  const formatDateTime = (dateString) => {
    if (!dateString) return "Never";
    // Ensure the date is treated as UTC if no timezone specified
    const date = new Date(
      dateString.endsWith("Z") ? dateString : dateString + "Z"
    );
    return date.toLocaleString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

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

  const tabs = [
    { key: "profile", label: "Profile", icon: UserCircleIcon },
    { key: "account", label: "Account", icon: Cog6ToothIcon },
    { key: "security", label: "Security", icon: ShieldCheckIcon },
    { key: "notifications", label: "Alerts", icon: BellIcon },
  ];

  // Security score calculation
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

    // Assume password is strong if they completed registration
    score += 20;
    factors.push({ name: "Strong Password", completed: true });

    return { score, factors };
  }, [user, twoFactorEnabled]);

  // Get security score color
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
    return {
      gradient: "from-red-500 to-rose-500",
      text: "text-red-400",
      bg: "bg-red-500",
    };
  };

  // Copy to clipboard
  const copyToClipboard = useCallback((text) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    toast.success("Copied to clipboard!");
    setTimeout(() => setCopied(false), 2000);
  }, []);

  // Password strength checker
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
    <div
      className={`fixed inset-0 z-50 flex items-center justify-center p-4 transition-all duration-300 ${
        isClosing ? "opacity-0" : "opacity-100"
      }`}
    >
      {/* Backdrop with animated gradient */}
      <div
        className="absolute inset-0 bg-gradient-to-br from-black/80 via-gray-900/90 to-black/80 backdrop-blur-xl"
        onClick={handleClose}
      />

      {/* Floating particles effect */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {[...Array(6)].map((_, i) => (
          <div
            key={i}
            className="absolute w-2 h-2 bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full opacity-20 animate-float"
            style={{
              left: `${20 + i * 15}%`,
              top: `${10 + i * 12}%`,
              animationDelay: `${i * 0.5}s`,
              animationDuration: `${4 + i}s`,
            }}
          />
        ))}
      </div>

      {/* Modal */}
      <div
        className={`relative w-full max-w-3xl max-h-[92vh] overflow-hidden bg-gradient-to-br from-gray-900/95 via-gray-900/98 to-gray-800/95 rounded-3xl shadow-2xl shadow-purple-500/10 border border-white/10 transition-all duration-500 ${
          isClosing
            ? "scale-95 opacity-0 translate-y-4"
            : "scale-100 opacity-100 translate-y-0"
        }`}
      >
        {/* Animated Background Effects */}
        <div className="absolute inset-0 overflow-hidden rounded-3xl pointer-events-none">
          <div className="absolute -top-40 -left-40 w-80 h-80 bg-gradient-to-br from-indigo-500/20 via-purple-500/15 to-transparent rounded-full blur-3xl animate-pulse" />
          <div
            className="absolute -bottom-40 -right-40 w-80 h-80 bg-gradient-to-tl from-cyan-500/20 via-blue-500/15 to-transparent rounded-full blur-3xl animate-pulse"
            style={{ animationDelay: "1s" }}
          />
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-gradient-radial from-purple-500/5 to-transparent rounded-full blur-3xl" />
          {/* Grid pattern overlay */}
          <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.01)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.01)_1px,transparent_1px)] bg-[size:60px_60px]" />
        </div>

        {/* Header */}
        <div className="relative border-b border-white/10 bg-gradient-to-r from-gray-900/50 to-gray-800/50 backdrop-blur-sm">
          <div className="p-6 pb-4">
            <div className="flex items-start justify-between">
              {/* Profile Header with enhanced avatar */}
              <div className="flex items-center gap-5">
                {/* Enhanced Avatar with upload */}
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
                    {/* Camera/Edit overlay */}
                    <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 flex items-center justify-center transition-all duration-300">
                      {avatarPreview || user?.avatar_url ? (
                        <PencilIcon className="h-6 w-6 text-white" />
                      ) : (
                        <CameraIcon className="h-6 w-6 text-white" />
                      )}
                    </div>
                  </div>
                  {/* Hidden file input */}
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/*"
                    onChange={handleAvatarSelect}
                    className="hidden"
                  />
                  {/* Verification Badge */}
                  {user?.is_email_verified && (
                    <div className="absolute -bottom-1 -right-1 w-7 h-7 bg-gradient-to-r from-emerald-400 to-green-500 rounded-full flex items-center justify-center border-3 border-gray-900 shadow-lg shadow-emerald-500/30 animate-bounce-subtle">
                      <CheckIcon className="h-4 w-4 text-white" />
                    </div>
                  )}
                  {/* Role Badge */}
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
                      className="p-1 hover:bg-white/10 rounded-lg transition-colors"
                      title="Copy username"
                    >
                      <DocumentDuplicateIcon
                        className={`h-3.5 w-3.5 ${
                          copied
                            ? "text-green-400"
                            : "text-gray-500 hover:text-gray-300"
                        }`}
                      />
                    </button>
                  </div>

                  {/* Enhanced Profile Completion */}
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

              {/* Close Button with hover effect */}
              <button
                onClick={handleClose}
                className="p-2.5 hover:bg-red-500/10 hover:border-red-500/30 border border-transparent rounded-xl transition-all duration-300 group"
              >
                <XMarkIcon className="h-5 w-5 text-gray-400 group-hover:text-red-400 group-hover:rotate-90 transition-all duration-300" />
              </button>
            </div>

            {/* Enhanced Tabs with sliding indicator */}
            <div className="flex gap-1 mt-6 p-1.5 bg-gray-800/60 rounded-2xl backdrop-blur-sm border border-white/5">
              {tabs.map((tab) => (
                <button
                  key={tab.key}
                  onClick={() => setActiveTab(tab.key)}
                  className={`relative flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-300 ${
                    activeTab === tab.key
                      ? "text-white"
                      : "text-gray-400 hover:text-gray-300 hover:bg-white/5"
                  }`}
                >
                  {activeTab === tab.key && (
                    <div className="absolute inset-0 bg-gradient-to-r from-indigo-500/20 via-purple-500/20 to-pink-500/20 rounded-xl border border-indigo-500/30 shadow-lg shadow-indigo-500/10" />
                  )}
                  <tab.icon
                    className={`h-4 w-4 relative z-10 transition-transform duration-300 ${
                      activeTab === tab.key ? "scale-110" : ""
                    }`}
                  />
                  <span className="relative z-10 hidden sm:inline">
                    {tab.label}
                  </span>
                  {tab.key === "security" && securityScore.score < 80 && (
                    <span className="relative z-10 w-2 h-2 bg-amber-500 rounded-full animate-pulse" />
                  )}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="relative overflow-y-auto max-h-[calc(92vh-220px)] p-6 scrollbar-thin scrollbar-thumb-indigo-500/30 scrollbar-track-transparent hover:scrollbar-thumb-indigo-500/50">
          {/* Profile Tab */}
          {activeTab === "profile" && (
            <div className="space-y-5 animate-fadeIn">
              {/* Security Score Card - New Feature */}
              <div
                className="relative overflow-hidden rounded-2xl p-5 bg-gradient-to-br from-gray-800/40 to-gray-900/40 border border-white/5 group hover:border-indigo-500/20 transition-all duration-500"
                onMouseEnter={() => setHoveredCard("security")}
                onMouseLeave={() => setHoveredCard(null)}
              >
                <div className="absolute inset-0 bg-gradient-to-r from-indigo-500/5 via-purple-500/5 to-pink-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                <div className="relative flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="relative">
                      <svg className="w-16 h-16 -rotate-90">
                        <circle
                          cx="32"
                          cy="32"
                          r="28"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="4"
                          className="text-gray-700"
                        />
                        <circle
                          cx="32"
                          cy="32"
                          r="28"
                          fill="none"
                          stroke="url(#scoreGradient)"
                          strokeWidth="4"
                          strokeLinecap="round"
                          strokeDasharray={`${
                            (securityScore.score / 100) * 176
                          } 176`}
                          className="transition-all duration-1000 ease-out"
                        />
                        <defs>
                          <linearGradient
                            id="scoreGradient"
                            x1="0%"
                            y1="0%"
                            x2="100%"
                            y2="0%"
                          >
                            <stop offset="0%" stopColor="#6366f1" />
                            <stop offset="50%" stopColor="#a855f7" />
                            <stop offset="100%" stopColor="#ec4899" />
                          </linearGradient>
                        </defs>
                      </svg>
                      <div className="absolute inset-0 flex items-center justify-center">
                        <span
                          className={`text-lg font-bold ${
                            getSecurityScoreColor(securityScore.score).text
                          }`}
                        >
                          {securityScore.score}
                        </span>
                      </div>
                    </div>
                    <div>
                      <h3 className="text-white font-semibold flex items-center gap-2">
                        Security Score
                        {securityScore.score >= 80 && (
                          <FireIcon className="h-4 w-4 text-orange-400" />
                        )}
                      </h3>
                      <p className="text-gray-400 text-sm">
                        {securityScore.score >= 80
                          ? "Excellent protection"
                          : securityScore.score >= 60
                          ? "Good, but can improve"
                          : "Needs attention"}
                      </p>
                    </div>
                  </div>
                  <div className="hidden md:flex flex-wrap gap-2 max-w-xs">
                    {securityScore.factors.slice(0, 4).map((factor, i) => (
                      <span
                        key={i}
                        className={`px-2 py-1 text-xs rounded-lg border ${
                          factor.completed
                            ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
                            : "bg-gray-700/50 border-gray-600/50 text-gray-400"
                        }`}
                      >
                        {factor.completed ? "✓" : "○"} {factor.name}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              {/* Quick Stats Bar - Enhanced */}
              <div className="grid grid-cols-3 gap-3">
                {[
                  {
                    label: "Member Since",
                    value:
                      formatDate(user?.created_at)
                        ?.split(",")[0]
                        ?.split(" ")[0] || "N/A",
                    icon: CalendarIcon,
                    gradient: "from-indigo-500/10 to-purple-500/10",
                    border: "border-indigo-500/20",
                    iconBg: "bg-indigo-500/20",
                    iconColor: "text-indigo-400",
                  },
                  {
                    label: "Account Role",
                    value: user?.role || "User",
                    icon: ShieldCheckIcon,
                    gradient: "from-emerald-500/10 to-teal-500/10",
                    border: "border-emerald-500/20",
                    iconBg: "bg-emerald-500/20",
                    iconColor: "text-emerald-400",
                  },
                  {
                    label: user?.is_email_verified ? "Verified" : "Unverified",
                    value: user?.is_email_verified ? "✓" : "○",
                    icon: CheckBadgeIcon,
                    gradient: user?.is_email_verified
                      ? "from-green-500/10 to-emerald-500/10"
                      : "from-amber-500/10 to-orange-500/10",
                    border: user?.is_email_verified
                      ? "border-green-500/20"
                      : "border-amber-500/20",
                    iconBg: user?.is_email_verified
                      ? "bg-green-500/20"
                      : "bg-amber-500/20",
                    iconColor: user?.is_email_verified
                      ? "text-green-400"
                      : "text-amber-400",
                  },
                ].map((stat, i) => (
                  <div
                    key={i}
                    className={`bg-gradient-to-br ${stat.gradient} border ${stat.border} rounded-2xl p-4 text-center group hover:scale-[1.02] transition-all duration-300 cursor-default`}
                  >
                    <div
                      className={`inline-flex p-2 ${stat.iconBg} rounded-xl mb-2 group-hover:scale-110 transition-transform duration-300`}
                    >
                      <stat.icon className={`h-5 w-5 ${stat.iconColor}`} />
                    </div>
                    <p className="text-xl font-bold text-white capitalize">
                      {stat.value}
                    </p>
                    <p className="text-xs text-gray-400 mt-1">{stat.label}</p>
                  </div>
                ))}
              </div>

              {/* Profile Fields - Enhanced with better interactivity */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Username (Read-only) */}
                <div className="group bg-gray-800/30 hover:bg-gray-800/50 border border-gray-700/50 hover:border-indigo-500/30 rounded-2xl p-4 transition-all duration-300 hover:shadow-lg hover:shadow-indigo-500/5">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="p-1.5 bg-indigo-500/20 rounded-lg group-hover:scale-110 transition-transform duration-300">
                      <UserCircleIcon className="h-4 w-4 text-indigo-400" />
                    </div>
                    <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                      Username
                    </span>
                    <span className="ml-auto px-2 py-0.5 text-[10px] bg-gray-700/50 text-gray-400 rounded-full">
                      Read-only
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <p className="text-white font-medium pl-9 font-mono">
                      @{user?.username}
                    </p>
                  </div>
                </div>

                {/* Email */}
                <div className="group bg-gray-800/30 hover:bg-gray-800/50 border border-gray-700/50 hover:border-cyan-500/30 rounded-2xl p-4 transition-all duration-300 hover:shadow-lg hover:shadow-cyan-500/5">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <div className="p-1.5 bg-cyan-500/20 rounded-lg group-hover:scale-110 transition-transform duration-300">
                        <EnvelopeIcon className="h-4 w-4 text-cyan-400" />
                      </div>
                      <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                        Email
                      </span>
                    </div>
                    {user?.is_email_verified ? (
                      <span className="flex items-center gap-1 text-xs text-green-400 bg-green-500/10 px-2.5 py-1 rounded-full border border-green-500/20 animate-pulse-subtle">
                        <CheckBadgeIcon className="h-3.5 w-3.5" />
                        Verified
                      </span>
                    ) : (
                      <span className="flex items-center gap-1 text-xs text-amber-400 bg-amber-500/10 px-2.5 py-1 rounded-full border border-amber-500/20">
                        <ClockIcon className="h-3.5 w-3.5" />
                        Pending
                      </span>
                    )}
                  </div>
                  <p className="text-white font-medium pl-9 truncate">
                    {user?.email}
                  </p>
                </div>
              </div>

              {/* Editable Fields - Enhanced with better animations */}
              <div className="space-y-4">
                {/* Full Name */}
                <div className="group bg-gray-800/30 hover:bg-gray-800/50 border border-gray-700/50 hover:border-purple-500/30 rounded-2xl p-4 transition-all duration-300 hover:shadow-lg hover:shadow-purple-500/5">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="p-1.5 bg-purple-500/20 rounded-lg group-hover:scale-110 transition-transform duration-300">
                      <UserCircleIcon className="h-4 w-4 text-purple-400" />
                    </div>
                    <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                      Full Name
                    </span>
                    {isEditing && (
                      <span className="ml-auto text-xs text-indigo-400 animate-pulse">
                        Editing...
                      </span>
                    )}
                  </div>
                  {isEditing ? (
                    <div className="relative">
                      <input
                        type="text"
                        name="full_name"
                        value={formData.full_name}
                        onChange={handleInputChange}
                        className="w-full pl-9 pr-4 py-2.5 bg-gray-900/70 border border-purple-500/30 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-500/30 transition-all duration-300"
                        placeholder="Enter your full name"
                      />
                      <div className="absolute inset-0 rounded-xl bg-gradient-to-r from-purple-500/5 to-transparent pointer-events-none" />
                    </div>
                  ) : (
                    <p className="text-white font-medium pl-9">
                      {user?.full_name || (
                        <span className="text-gray-500 italic flex items-center gap-1">
                          <InformationCircleIcon className="h-4 w-4" />
                          Not provided
                        </span>
                      )}
                    </p>
                  )}
                </div>

                {/* Organization & Department */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="group bg-gray-800/30 hover:bg-gray-800/50 border border-gray-700/50 hover:border-blue-500/30 rounded-2xl p-4 transition-all duration-300 hover:shadow-lg hover:shadow-blue-500/5">
                    <div className="flex items-center gap-2 mb-2">
                      <div className="p-1.5 bg-blue-500/20 rounded-lg group-hover:scale-110 transition-transform duration-300">
                        <BuildingOfficeIcon className="h-4 w-4 text-blue-400" />
                      </div>
                      <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                        Organization
                      </span>
                    </div>
                    {isEditing ? (
                      <div className="relative">
                        <input
                          type="text"
                          name="organization"
                          value={formData.organization}
                          onChange={handleInputChange}
                          className="w-full pl-9 pr-4 py-2.5 bg-gray-900/70 border border-blue-500/30 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/30 transition-all duration-300"
                          placeholder="Your organization"
                        />
                      </div>
                    ) : (
                      <p className="text-white font-medium pl-9">
                        {user?.organization || (
                          <span className="text-gray-500 italic">
                            Not provided
                          </span>
                        )}
                      </p>
                    )}
                  </div>

                  <div className="group bg-gray-800/30 hover:bg-gray-800/50 border border-gray-700/50 hover:border-pink-500/30 rounded-2xl p-4 transition-all duration-300 hover:shadow-lg hover:shadow-pink-500/5">
                    <div className="flex items-center gap-2 mb-2">
                      <div className="p-1.5 bg-pink-500/20 rounded-lg group-hover:scale-110 transition-transform duration-300">
                        <CommandLineIcon className="h-4 w-4 text-pink-400" />
                      </div>
                      <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                        Department
                      </span>
                    </div>
                    {isEditing ? (
                      <div className="relative">
                        <input
                          type="text"
                          name="department"
                          value={formData.department}
                          onChange={handleInputChange}
                          className="w-full pl-9 pr-4 py-2.5 bg-gray-900/70 border border-pink-500/30 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-pink-500 focus:ring-2 focus:ring-pink-500/30 transition-all duration-300"
                          placeholder="Your department"
                        />
                      </div>
                    ) : (
                      <p className="text-white font-medium pl-9">
                        {user?.department || (
                          <span className="text-gray-500 italic">
                            Not provided
                          </span>
                        )}
                      </p>
                    )}
                  </div>
                </div>

                {/* Phone & Timezone */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="group bg-gray-800/30 hover:bg-gray-800/50 border border-gray-700/50 hover:border-green-500/30 rounded-2xl p-4 transition-all duration-300 hover:shadow-lg hover:shadow-green-500/5">
                    <div className="flex items-center gap-2 mb-2">
                      <div className="p-1.5 bg-green-500/20 rounded-lg group-hover:scale-110 transition-transform duration-300">
                        <PhoneIcon className="h-4 w-4 text-green-400" />
                      </div>
                      <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                        Phone
                      </span>
                      {!user?.phone && !isEditing && (
                        <span className="ml-auto px-2 py-0.5 text-[10px] bg-amber-500/10 border border-amber-500/20 text-amber-400 rounded-full">
                          +15 security
                        </span>
                      )}
                    </div>
                    {isEditing ? (
                      <div className="relative">
                        <input
                          type="tel"
                          name="phone"
                          value={formData.phone}
                          onChange={handleInputChange}
                          className="w-full pl-9 pr-4 py-2.5 bg-gray-900/70 border border-green-500/30 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-green-500 focus:ring-2 focus:ring-green-500/30 transition-all duration-300"
                          placeholder="+1 (555) 000-0000"
                        />
                      </div>
                    ) : (
                      <p className="text-white font-medium pl-9">
                        {user?.phone || (
                          <span className="text-gray-500 italic">
                            Not provided
                          </span>
                        )}
                      </p>
                    )}
                  </div>

                  <div className="group bg-gray-800/30 hover:bg-gray-800/50 border border-gray-700/50 hover:border-orange-500/30 rounded-2xl p-4 transition-all duration-300 hover:shadow-lg hover:shadow-orange-500/5">
                    <div className="flex items-center gap-2 mb-2">
                      <div className="p-1.5 bg-orange-500/20 rounded-lg group-hover:scale-110 transition-transform duration-300">
                        <GlobeAltIcon className="h-4 w-4 text-orange-400" />
                      </div>
                      <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                        Timezone
                      </span>
                    </div>
                    {isEditing ? (
                      <div className="relative">
                        <select
                          name="timezone"
                          value={formData.timezone}
                          onChange={handleInputChange}
                          className="w-full pl-9 pr-10 py-2.5 bg-gray-900/70 border border-orange-500/30 rounded-xl text-white focus:outline-none focus:border-orange-500 focus:ring-2 focus:ring-orange-500/30 transition-all duration-300 appearance-none cursor-pointer"
                        >
                          {timezones.map((tz) => (
                            <option key={tz} value={tz} className="bg-gray-900">
                              {tz.replace(/_/g, " ")}
                            </option>
                          ))}
                        </select>
                        <ChevronRightIcon className="absolute right-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400 rotate-90 pointer-events-none" />
                      </div>
                    ) : (
                      <p className="text-white font-medium pl-9">
                        {(user?.timezone || "UTC").replace(/_/g, " ")}
                      </p>
                    )}
                  </div>
                </div>
              </div>

              {/* Action Buttons - Enhanced with better visuals */}
              <div className="pt-5">
                {isEditing ? (
                  <div className="flex gap-3">
                    <button
                      onClick={handleSaveProfile}
                      disabled={isUpdating}
                      className="flex-1 py-3.5 px-6 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 text-white font-semibold rounded-xl hover:from-indigo-600 hover:via-purple-600 hover:to-pink-600 shadow-lg shadow-purple-500/25 hover:shadow-purple-500/40 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none flex items-center justify-center gap-2 group"
                    >
                      {isUpdating ? (
                        <>
                          <ArrowPathIcon className="w-5 h-5 animate-spin" />
                          Saving...
                        </>
                      ) : (
                        <>
                          <CheckCircleIcon className="h-5 w-5 group-hover:scale-110 transition-transform" />
                          Save Changes
                        </>
                      )}
                    </button>
                    <button
                      onClick={handleCancel}
                      disabled={isUpdating}
                      className="flex-1 py-3.5 px-6 bg-gray-700/50 hover:bg-gray-700 text-white font-semibold rounded-xl border border-gray-600/50 hover:border-gray-500 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                    >
                      <XMarkIcon className="h-5 w-5" />
                      Cancel
                    </button>
                  </div>
                ) : (
                  <button
                    onClick={() => setIsEditing(true)}
                    className="w-full py-4 px-6 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 text-white font-semibold rounded-xl hover:from-indigo-600 hover:via-purple-600 hover:to-pink-600 shadow-lg shadow-purple-500/25 hover:shadow-purple-500/40 hover:scale-[1.02] transition-all duration-300 flex items-center justify-center gap-3 group relative overflow-hidden"
                  >
                    <div className="absolute inset-0 bg-gradient-to-r from-white/0 via-white/20 to-white/0 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700" />
                    <PencilIcon className="h-5 w-5 group-hover:rotate-12 transition-transform duration-300" />
                    <span>Edit Profile</span>
                    <ChevronRightIcon className="h-5 w-5 group-hover:translate-x-1 transition-transform duration-300" />
                  </button>
                )}
              </div>
            </div>
          )}

          {/* Account Tab - Enhanced */}
          {activeTab === "account" && (
            <div className="space-y-5 animate-fadeIn">
              {/* Email Verification Status - Enhanced */}
              <div
                className={`relative overflow-hidden rounded-2xl p-6 border transition-all duration-500 ${
                  user?.is_email_verified
                    ? "bg-gradient-to-br from-emerald-500/10 via-green-500/5 to-teal-500/10 border-emerald-500/20"
                    : "bg-gradient-to-br from-amber-500/10 via-orange-500/5 to-yellow-500/10 border-amber-500/20"
                }`}
              >
                {/* Animated background pattern */}
                <div className="absolute inset-0 opacity-30">
                  <div
                    className={`absolute inset-0 ${
                      user?.is_email_verified
                        ? "bg-[radial-gradient(circle_at_50%_50%,rgba(16,185,129,0.1),transparent_70%)]"
                        : "bg-[radial-gradient(circle_at_50%_50%,rgba(245,158,11,0.1),transparent_70%)]"
                    }`}
                  />
                </div>
                <div className="relative flex items-start gap-4">
                  <div
                    className={`p-3.5 rounded-2xl ${
                      user?.is_email_verified
                        ? "bg-gradient-to-br from-emerald-500/30 to-green-500/20"
                        : "bg-gradient-to-br from-amber-500/30 to-orange-500/20"
                    } shadow-lg`}
                  >
                    {user?.is_email_verified ? (
                      <CheckCircleIcon className="h-8 w-8 text-emerald-400" />
                    ) : (
                      <ExclamationTriangleIcon className="h-8 w-8 text-amber-400 animate-pulse" />
                    )}
                  </div>
                  <div className="flex-1">
                    <h4 className="text-white font-bold text-lg mb-1 flex items-center gap-2">
                      Email Verification
                      {user?.is_email_verified && (
                        <span className="px-2 py-0.5 text-xs bg-emerald-500/20 text-emerald-400 rounded-full border border-emerald-500/30">
                          Complete
                        </span>
                      )}
                    </h4>
                    <p className="text-gray-400 text-sm leading-relaxed">
                      {user?.is_email_verified
                        ? "Your email address has been verified. You have full access to all platform features and security protections."
                        : "Verify your email to unlock all features, improve account security, and receive important notifications."}
                    </p>
                    {!user?.is_email_verified && (
                      <button
                        onClick={handleResendVerification}
                        disabled={isResendingVerification}
                        className="mt-4 px-5 py-2.5 bg-gradient-to-r from-amber-500/20 to-orange-500/20 hover:from-amber-500/30 hover:to-orange-500/30 text-amber-300 text-sm font-semibold rounded-xl border border-amber-500/30 hover:border-amber-500/50 transition-all duration-300 disabled:opacity-50 flex items-center gap-2 group"
                      >
                        {isResendingVerification ? (
                          <>
                            <ArrowPathIcon className="w-4 h-4 animate-spin" />
                            Sending...
                          </>
                        ) : (
                          <>
                            <EnvelopeIcon className="h-4 w-4 group-hover:scale-110 transition-transform" />
                            Resend Verification Email
                            <ChevronRightIcon className="h-4 w-4 group-hover:translate-x-1 transition-transform" />
                          </>
                        )}
                      </button>
                    )}
                  </div>
                </div>
              </div>

              {/* Account Status & Activity - Enhanced Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Account Status */}
                <div className="group bg-gray-800/30 border border-gray-700/50 hover:border-blue-500/30 rounded-2xl p-5 hover:bg-gray-800/50 transition-all duration-300 hover:shadow-lg hover:shadow-blue-500/5">
                  <div className="flex items-center gap-3 mb-5">
                    <div className="p-2.5 bg-gradient-to-br from-blue-500/20 to-indigo-500/20 rounded-xl group-hover:scale-110 transition-transform duration-300">
                      <ShieldCheckIcon className="h-6 w-6 text-blue-400" />
                    </div>
                    <h4 className="text-white font-semibold text-lg">
                      Account Status
                    </h4>
                  </div>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between p-3 bg-gray-900/40 rounded-xl">
                      <span className="text-gray-400 text-sm flex items-center gap-2">
                        <BoltIcon className="h-4 w-4 text-emerald-400" />
                        Status
                      </span>
                      <span className="px-3 py-1.5 bg-gradient-to-r from-emerald-500/20 to-green-500/20 text-emerald-400 text-xs font-semibold rounded-lg border border-emerald-500/30 flex items-center gap-1">
                        <span className="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-pulse" />
                        {user?.status || "Active"}
                      </span>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-gray-900/40 rounded-xl">
                      <span className="text-gray-400 text-sm flex items-center gap-2">
                        <StarIcon className="h-4 w-4 text-indigo-400" />
                        Role
                      </span>
                      <span className="px-3 py-1.5 bg-gradient-to-r from-indigo-500/20 to-purple-500/20 text-indigo-400 text-xs font-semibold rounded-lg border border-indigo-500/30 capitalize">
                        {user?.role || "User"}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Activity Info */}
                <div className="group bg-gray-800/30 border border-gray-700/50 hover:border-purple-500/30 rounded-2xl p-5 hover:bg-gray-800/50 transition-all duration-300 hover:shadow-lg hover:shadow-purple-500/5">
                  <div className="flex items-center gap-3 mb-5">
                    <div className="p-2.5 bg-gradient-to-br from-purple-500/20 to-pink-500/20 rounded-xl group-hover:scale-110 transition-transform duration-300">
                      <ClockIcon className="h-6 w-6 text-purple-400" />
                    </div>
                    <h4 className="text-white font-semibold text-lg">
                      Activity
                    </h4>
                  </div>
                  <div className="space-y-4">
                    <div className="p-3 bg-gray-900/40 rounded-xl">
                      <div className="flex items-center gap-2 text-gray-400 text-xs mb-1">
                        <CalendarIcon className="h-3.5 w-3.5" />
                        Member Since
                      </div>
                      <span className="text-white text-sm font-medium">
                        {formatDate(user?.created_at)}
                      </span>
                    </div>
                    <div className="p-3 bg-gray-900/40 rounded-xl">
                      <div className="flex items-center gap-2 text-gray-400 text-xs mb-1">
                        <ArrowPathIcon className="h-3.5 w-3.5" />
                        Last Login
                      </div>
                      <span className="text-white text-sm font-medium">
                        {formatDateTime(user?.last_login)}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Security Tab - Enhanced with 2FA and Sessions */}
          {activeTab === "security" && (
            <div className="space-y-5 animate-fadeIn">
              {/* Security Overview Card */}
              <div className="relative overflow-hidden rounded-2xl p-6 bg-gradient-to-br from-gray-800/50 to-gray-900/50 border border-white/5">
                <div className="absolute inset-0 bg-gradient-to-r from-indigo-500/5 via-purple-500/5 to-pink-500/5" />
                <div className="relative flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="relative">
                      <div
                        className={`w-14 h-14 rounded-2xl bg-gradient-to-br ${
                          getSecurityScoreColor(securityScore.score).gradient
                        } flex items-center justify-center shadow-lg`}
                      >
                        <ShieldCheckIcon className="h-7 w-7 text-white" />
                      </div>
                      <div
                        className={`absolute -bottom-1 -right-1 w-6 h-6 ${
                          getSecurityScoreColor(securityScore.score).bg
                        } rounded-full flex items-center justify-center text-white text-xs font-bold border-2 border-gray-900`}
                      >
                        {securityScore.score}
                      </div>
                    </div>
                    <div>
                      <h3 className="text-white font-bold text-lg">
                        Security Overview
                      </h3>
                      <p className="text-gray-400 text-sm">
                        {
                          securityScore.factors.filter((f) => f.completed)
                            .length
                        }{" "}
                        of {securityScore.factors.length} security measures
                        active
                      </p>
                    </div>
                  </div>
                  <div className="hidden md:flex gap-2">
                    {securityScore.factors.map((factor, i) => (
                      <div
                        key={i}
                        className={`w-3 h-3 rounded-full ${
                          factor.completed ? "bg-emerald-500" : "bg-gray-600"
                        } transition-all duration-300`}
                        title={factor.name}
                      />
                    ))}
                  </div>
                </div>
              </div>

              {/* Two-Factor Authentication */}
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
                          <span className="px-2 py-0.5 text-xs bg-gray-500/20 text-gray-400 rounded-full">
                            Loading...
                          </span>
                        ) : twoFactorEnabled ? (
                          <span className="px-2 py-0.5 text-xs bg-emerald-500/20 text-emerald-400 rounded-full border border-emerald-500/30">
                            Active
                          </span>
                        ) : null}
                      </h4>
                      <p className="text-gray-400 text-sm mt-1 max-w-md">
                        Add an extra layer of security to your account by
                        requiring a verification code in addition to your
                        password.
                      </p>
                      {!twoFactorEnabled && !loading2FA && (
                        <p className="text-amber-400 text-xs mt-2 flex items-center gap-1">
                          <ShieldExclamationIcon className="h-4 w-4" />
                          Enabling 2FA increases your security score by 30
                          points
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

                {/* 2FA Setup Modal */}
                {showTwoFactorSetup && twoFactorSetupData && (
                  <div className="mt-6 p-5 bg-gray-900/60 rounded-xl border border-purple-500/20">
                    <h5 className="text-white font-semibold mb-4 flex items-center gap-2">
                      <QrCodeIcon className="h-5 w-5 text-purple-400" />
                      Setup Two-Factor Authentication
                    </h5>
                    <div className="space-y-4">
                      <div className="text-center">
                        <p className="text-gray-400 text-sm mb-3">
                          Scan this QR code with your authenticator app (Google
                          Authenticator, Authy, etc.)
                        </p>
                        <div className="inline-block p-4 bg-white rounded-xl">
                          <img
                            src={`https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=${encodeURIComponent(
                              twoFactorSetupData.qr_code_url
                            )}`}
                            alt="2FA QR Code"
                            className="w-36 h-36"
                          />
                        </div>
                      </div>
                      <div className="text-center">
                        <p className="text-gray-400 text-xs mb-2">
                          Or enter this secret manually:
                        </p>
                        <code className="px-3 py-1.5 bg-gray-800 rounded text-sm text-purple-400 font-mono">
                          {twoFactorSetupData.secret}
                        </code>
                      </div>
                      <div className="bg-amber-500/10 border border-amber-500/20 rounded-lg p-3">
                        <p className="text-amber-400 text-xs font-medium mb-2">
                          🔐 Save these backup codes:
                        </p>
                        <div className="grid grid-cols-4 gap-2">
                          {twoFactorSetupData.backup_codes.map((code, i) => (
                            <code
                              key={i}
                              className="text-xs text-gray-300 bg-gray-800 px-2 py-1 rounded text-center font-mono"
                            >
                              {code}
                            </code>
                          ))}
                        </div>
                      </div>
                      <div>
                        <label className="text-sm text-gray-300 mb-2">
                          Enter the 6-digit code from your app:
                        </label>
                        <input
                          type="text"
                          value={twoFactorCode}
                          onChange={(e) =>
                            setTwoFactorCode(
                              e.target.value.replace(/\D/g, "").slice(0, 6)
                            )
                          }
                          placeholder="000000"
                          className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-xl text-white text-center text-2xl tracking-widest font-mono focus:outline-none focus:border-purple-500"
                          maxLength={6}
                        />
                      </div>
                      <div className="flex gap-3">
                        <button
                          onClick={() => {
                            setShowTwoFactorSetup(false);
                            setTwoFactorSetupData(null);
                            setTwoFactorCode("");
                          }}
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

                {/* 2FA Disable Modal */}
                {showTwoFactorDisable && (
                  <div className="mt-6 p-5 bg-gray-900/60 rounded-xl border border-red-500/20">
                    <h5 className="text-white font-semibold mb-4 flex items-center gap-2">
                      <ShieldExclamationIcon className="h-5 w-5 text-red-400" />
                      Disable Two-Factor Authentication
                    </h5>
                    <div className="space-y-4">
                      <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-3">
                        <p className="text-red-400 text-sm">
                          ⚠️ Disabling 2FA will make your account less secure.
                          You'll need to enter your current 2FA code or a backup
                          code to confirm.
                        </p>
                      </div>
                      <div>
                        <label className="text-sm text-gray-300 mb-2 block">
                          Enter your 2FA code or backup code:
                        </label>
                        <input
                          type="text"
                          value={disableCode}
                          onChange={(e) =>
                            setDisableCode(
                              e.target.value
                                .replace(/[^a-zA-Z0-9]/g, "")
                                .slice(0, 8)
                                .toUpperCase()
                            )
                          }
                          placeholder="000000 or BACKUP"
                          className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-xl text-white text-center text-xl tracking-widest font-mono focus:outline-none focus:border-red-500 uppercase"
                          maxLength={8}
                          autoFocus
                        />
                        <p className="text-gray-500 text-xs mt-2 text-center">
                          Enter 6-digit code from your authenticator app or
                          8-character backup code
                        </p>
                      </div>
                      <div className="flex gap-3">
                        <button
                          onClick={() => {
                            setShowTwoFactorDisable(false);
                            setDisableCode("");
                          }}
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

              {/* Active Sessions */}
              <div className="bg-gray-800/30 border border-gray-700/50 hover:border-blue-500/30 rounded-2xl p-6 transition-all duration-300">
                <div className="flex items-center justify-between mb-5">
                  <div className="flex items-center gap-3">
                    <div className="p-2.5 bg-gradient-to-br from-blue-500/20 to-cyan-500/20 rounded-xl">
                      <DevicePhoneMobileIcon className="h-6 w-6 text-blue-400" />
                    </div>
                    <div>
                      <h4 className="text-white font-semibold text-lg">
                        Active Sessions
                      </h4>
                      <p className="text-gray-400 text-xs">
                        {loadingSessions
                          ? "Loading..."
                          : `${activeSessions.length} device${
                              activeSessions.length !== 1 ? "s" : ""
                            } logged in`}
                      </p>
                    </div>
                  </div>
                  {activeSessions.length > 1 && (
                    <button
                      onClick={handleRevokeAllSessions}
                      disabled={revokingSession === "all"}
                      className="px-3 py-1.5 text-xs text-red-400 bg-red-500/10 hover:bg-red-500/20 border border-red-500/20 rounded-lg transition-all disabled:opacity-50"
                    >
                      {revokingSession === "all"
                        ? "Signing out..."
                        : "Sign out all others"}
                    </button>
                  )}
                </div>
                <div className="space-y-3">
                  {loadingSessions ? (
                    <div className="space-y-3">
                      {[1, 2].map((i) => (
                        <div
                          key={i}
                          className="p-4 rounded-xl bg-gray-900/40 animate-pulse"
                        >
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
                          <div
                            className={`p-2.5 rounded-xl ${
                              session.current
                                ? "bg-indigo-500/20"
                                : "bg-gray-700/50"
                            }`}
                          >
                            {session.device?.toLowerCase().includes("iphone") ||
                            session.device?.toLowerCase().includes("android") ||
                            session.device?.toLowerCase().includes("mobile") ? (
                              <DevicePhoneMobileIcon
                                className={`h-5 w-5 ${
                                  session.current
                                    ? "text-indigo-400"
                                    : "text-gray-400"
                                }`}
                              />
                            ) : (
                              <ComputerDesktopIcon
                                className={`h-5 w-5 ${
                                  session.current
                                    ? "text-indigo-400"
                                    : "text-gray-400"
                                }`}
                              />
                            )}
                          </div>
                          <div>
                            <div className="flex items-center gap-2">
                              <p className="text-white font-medium text-sm">
                                {session.device}
                              </p>
                              <span className="text-gray-500 text-xs">•</span>
                              <p className="text-gray-400 text-xs">
                                {session.browser}
                              </p>
                              {session.current && (
                                <span className="px-2 py-0.5 text-[10px] bg-emerald-500/20 text-emerald-400 rounded-full border border-emerald-500/30">
                                  Current
                                </span>
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
                              {session.ip && (
                                <span className="text-gray-500 text-xs">
                                  {session.ip}
                                </span>
                              )}
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

              {/* Password Change Section - Enhanced */}
              <div className="bg-gray-800/30 border border-gray-700/50 hover:border-indigo-500/30 rounded-2xl p-6 transition-all duration-300">
                <div className="flex items-center gap-3 mb-6">
                  <div className="p-2.5 bg-gradient-to-br from-indigo-500/20 to-purple-500/20 rounded-xl">
                    <LockClosedIcon className="h-6 w-6 text-indigo-400" />
                  </div>
                  <div>
                    <h3 className="text-white font-semibold text-lg">
                      Change Password
                    </h3>
                    <p className="text-gray-500 text-sm">
                      Keep your account secure with a strong password
                    </p>
                  </div>
                </div>

                <form onSubmit={handlePasswordChange} className="space-y-5">
                  {/* Current Password */}
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
                        onClick={() =>
                          setShowPasswords((prev) => ({
                            ...prev,
                            current: !prev.current,
                          }))
                        }
                        className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-500 hover:text-white transition-colors p-1"
                      >
                        {showPasswords.current ? (
                          <EyeSlashIcon className="h-5 w-5" />
                        ) : (
                          <EyeIcon className="h-5 w-5" />
                        )}
                      </button>
                    </div>
                  </div>

                  {/* New Password */}
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
                        onClick={() =>
                          setShowPasswords((prev) => ({
                            ...prev,
                            new: !prev.new,
                          }))
                        }
                        className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-500 hover:text-white transition-colors p-1"
                      >
                        {showPasswords.new ? (
                          <EyeSlashIcon className="h-5 w-5" />
                        ) : (
                          <EyeIcon className="h-5 w-5" />
                        )}
                      </button>
                    </div>
                    {/* Enhanced Password Strength Indicator */}
                    {passwordData.new_password && (
                      <div className="mt-3 space-y-2">
                        <div className="flex gap-1.5">
                          {[1, 2, 3, 4, 5].map((level) => (
                            <div
                              key={level}
                              className={`h-1.5 flex-1 rounded-full transition-all duration-500 ${
                                level <= passwordStrength.strength
                                  ? passwordStrength.color
                                  : "bg-gray-700"
                              }`}
                            />
                          ))}
                        </div>
                        <div className="flex items-center justify-between">
                          <p className="text-xs text-gray-500">
                            Password strength:{" "}
                            <span
                              className={
                                passwordStrength.strength >= 4
                                  ? "text-green-400"
                                  : passwordStrength.strength >= 3
                                  ? "text-yellow-400"
                                  : "text-red-400"
                              }
                            >
                              {passwordStrength.label}
                            </span>
                          </p>
                          <div className="flex gap-2 text-xs">
                            {[
                              {
                                label: "8+",
                                active: passwordData.new_password.length >= 8,
                              },
                              {
                                label: "a-z",
                                active: /[a-z]/.test(passwordData.new_password),
                              },
                              {
                                label: "A-Z",
                                active: /[A-Z]/.test(passwordData.new_password),
                              },
                              {
                                label: "0-9",
                                active: /[0-9]/.test(passwordData.new_password),
                              },
                              {
                                label: "@#$",
                                active: /[^a-zA-Z0-9]/.test(
                                  passwordData.new_password
                                ),
                              },
                            ].map((req, i) => (
                              <span
                                key={i}
                                className={`px-1.5 py-0.5 rounded ${
                                  req.active
                                    ? "bg-emerald-500/20 text-emerald-400"
                                    : "bg-gray-700/50 text-gray-500"
                                }`}
                              >
                                {req.label}
                              </span>
                            ))}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Confirm Password */}
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
                          passwordData.confirm_password &&
                          passwordData.new_password !==
                            passwordData.confirm_password
                            ? "border-red-500 focus:border-red-500 focus:ring-red-500/20"
                            : passwordData.confirm_password &&
                              passwordData.new_password ===
                                passwordData.confirm_password
                            ? "border-green-500 focus:border-green-500 focus:ring-green-500/20"
                            : "border-gray-700 hover:border-gray-600 focus:border-indigo-500 focus:ring-indigo-500/20"
                        }`}
                        placeholder="Confirm new password"
                        required
                      />
                      <button
                        type="button"
                        onClick={() =>
                          setShowPasswords((prev) => ({
                            ...prev,
                            confirm: !prev.confirm,
                          }))
                        }
                        className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-500 hover:text-white transition-colors p-1"
                      >
                        {showPasswords.confirm ? (
                          <EyeSlashIcon className="h-5 w-5" />
                        ) : (
                          <EyeIcon className="h-5 w-5" />
                        )}
                      </button>
                    </div>
                    {passwordData.confirm_password &&
                      passwordData.new_password !==
                        passwordData.confirm_password && (
                        <p className="text-xs text-red-400 mt-2 flex items-center gap-1">
                          <XMarkIcon className="h-3.5 w-3.5" />
                          Passwords don't match
                        </p>
                      )}
                    {passwordData.confirm_password &&
                      passwordData.new_password ===
                        passwordData.confirm_password && (
                        <p className="text-xs text-green-400 mt-2 flex items-center gap-1">
                          <CheckIcon className="h-3.5 w-3.5" />
                          Passwords match
                        </p>
                      )}
                  </div>

                  <button
                    type="submit"
                    disabled={
                      isChangingPassword ||
                      !passwordData.current_password ||
                      !passwordData.new_password ||
                      passwordData.new_password !==
                        passwordData.confirm_password
                    }
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

              {/* Logout Section - Enhanced */}
              <div className="bg-gradient-to-br from-red-500/10 via-rose-500/5 to-pink-500/10 border border-red-500/20 rounded-2xl p-6 group hover:border-red-500/40 transition-all duration-300">
                <div className="flex items-start gap-4">
                  <div className="p-3 bg-gradient-to-br from-red-500/20 to-rose-500/20 rounded-xl group-hover:scale-110 transition-transform duration-300">
                    <ArrowRightOnRectangleIcon className="h-6 w-6 text-red-400" />
                  </div>
                  <div className="flex-1">
                    <h3 className="text-white font-semibold text-lg mb-1">
                      Sign Out
                    </h3>
                    <p className="text-gray-400 text-sm mb-4">
                      Sign out from this device. You'll need to log in again to
                      access your account.
                    </p>
                    <button
                      onClick={handleLogout}
                      className="w-full py-3.5 px-6 bg-red-500/20 hover:bg-red-500/30 border border-red-500/30 hover:border-red-500/50 text-red-400 font-semibold rounded-xl transition-all duration-300 flex items-center justify-center gap-2 group/btn"
                    >
                      <ArrowRightOnRectangleIcon className="h-5 w-5 group-hover/btn:translate-x-1 transition-transform" />
                      Sign Out
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Notifications Tab - New */}
          {activeTab === "notifications" && (
            <div className="space-y-5 animate-fadeIn">
              {/* Notification Header */}
              <div className="relative overflow-hidden rounded-2xl p-6 bg-gradient-to-br from-gray-800/50 to-gray-900/50 border border-white/5">
                <div className="absolute inset-0 bg-gradient-to-r from-purple-500/5 via-pink-500/5 to-rose-500/5" />
                <div className="relative flex items-center gap-4">
                  <div className="p-3 bg-gradient-to-br from-purple-500/20 to-pink-500/20 rounded-xl">
                    <BellIcon className="h-7 w-7 text-purple-400" />
                  </div>
                  <div>
                    <h3 className="text-white font-bold text-lg">
                      Notification Preferences
                    </h3>
                    <p className="text-gray-400 text-sm">
                      {loadingNotifications
                        ? "Loading preferences..."
                        : "Control how and when you receive notifications"}
                    </p>
                  </div>
                  {savingNotifications && (
                    <div className="ml-auto">
                      <ArrowPathIcon className="h-5 w-5 text-indigo-400 animate-spin" />
                    </div>
                  )}
                </div>
              </div>

              {/* Notification Categories */}
              <div className="space-y-4">
                {loadingNotifications ? (
                  <div className="space-y-4">
                    {[1, 2, 3, 4, 5].map((i) => (
                      <div
                        key={i}
                        className="bg-gray-800/30 border border-gray-700/50 rounded-2xl p-5 animate-pulse"
                      >
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
                  [
                    {
                      key: "email",
                      title: "Email Notifications",
                      description:
                        "Receive important updates and alerts via email",
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
                      description:
                        "Critical security notifications and login alerts",
                      icon: ShieldExclamationIcon,
                      gradient: "from-red-500/20 to-orange-500/20",
                      iconColor: "text-red-400",
                      recommended: true,
                    },
                    {
                      key: "updates",
                      title: "Product Updates",
                      description:
                        "New features, improvements, and platform updates",
                      icon: SparklesIcon,
                      gradient: "from-emerald-500/20 to-teal-500/20",
                      iconColor: "text-emerald-400",
                    },
                    {
                      key: "marketing",
                      title: "Marketing & Promotions",
                      description:
                        "Special offers, tips, and educational content",
                      icon: HeartIcon,
                      gradient: "from-pink-500/20 to-rose-500/20",
                      iconColor: "text-pink-400",
                    },
                  ].map((item) => (
                    <div
                      key={item.key}
                      className="group bg-gray-800/30 border border-gray-700/50 hover:border-gray-600/50 rounded-2xl p-5 transition-all duration-300"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          <div
                            className={`p-3 bg-gradient-to-br ${item.gradient} rounded-xl group-hover:scale-110 transition-transform duration-300`}
                          >
                            <item.icon
                              className={`h-5 w-5 ${item.iconColor}`}
                            />
                          </div>
                          <div>
                            <div className="flex items-center gap-2">
                              <h4 className="text-white font-medium">
                                {item.title}
                              </h4>
                              {item.recommended && (
                                <span className="px-2 py-0.5 text-[10px] bg-amber-500/20 text-amber-400 rounded-full border border-amber-500/30">
                                  Recommended
                                </span>
                              )}
                            </div>
                            <p className="text-gray-400 text-sm mt-0.5">
                              {item.description}
                            </p>
                          </div>
                        </div>
                        <button
                          onClick={() => handleNotificationToggle(item.key)}
                          disabled={savingNotifications}
                          className={`relative flex-shrink-0 w-14 h-8 rounded-full transition-all duration-300 disabled:opacity-50 ${
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

              {/* Quick Actions */}
              <div className="bg-gray-800/30 border border-gray-700/50 rounded-2xl p-5">
                <h4 className="text-white font-semibold mb-4 flex items-center gap-2">
                  <BoltIcon className="h-5 w-5 text-amber-400" />
                  Quick Actions
                </h4>
                <div className="grid grid-cols-2 gap-3">
                  <button
                    onClick={async () => {
                      const allOn = {
                        email: true,
                        push: true,
                        security: true,
                        updates: true,
                        marketing: true,
                      };
                      setNotifications(allOn);
                      try {
                        await authAPI.updateNotificationPreferences(allOn);
                        toast.success("All notifications enabled");
                      } catch (error) {
                        toast.error("Failed to update preferences");
                      }
                    }}
                    disabled={savingNotifications}
                    className="py-3 px-4 bg-gradient-to-r from-emerald-500/10 to-green-500/10 hover:from-emerald-500/20 hover:to-green-500/20 border border-emerald-500/20 text-emerald-400 font-medium rounded-xl transition-all duration-300 flex items-center justify-center gap-2 disabled:opacity-50"
                  >
                    <CheckCircleIcon className="h-5 w-5" />
                    Enable All
                  </button>
                  <button
                    onClick={async () => {
                      const minimal = {
                        email: false,
                        push: false,
                        security: true,
                        updates: false,
                        marketing: false,
                      };
                      setNotifications(minimal);
                      try {
                        await authAPI.updateNotificationPreferences(minimal);
                        toast.success("Only security alerts enabled");
                      } catch (error) {
                        toast.error("Failed to update preferences");
                      }
                    }}
                    disabled={savingNotifications}
                    className="py-3 px-4 bg-gradient-to-r from-gray-700/50 to-gray-600/50 hover:from-gray-700 hover:to-gray-600 border border-gray-600/50 text-gray-300 font-medium rounded-xl transition-all duration-300 flex items-center justify-center gap-2 disabled:opacity-50"
                  >
                    <XMarkIcon className="h-5 w-5" />
                    Minimal Only
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Avatar Crop Modal */}
      {showAvatarModal && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
          <div className="bg-gray-900 border border-gray-700/50 rounded-3xl shadow-2xl w-full max-w-xl overflow-hidden animate-scale-in">
            {/* Modal Header */}
            <div className="px-6 py-4 border-b border-gray-700/50 bg-gradient-to-r from-indigo-500/10 to-purple-500/10">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-gradient-to-br from-indigo-500/20 to-purple-500/20 rounded-xl">
                    <PhotoIcon className="h-5 w-5 text-indigo-400" />
                  </div>
                  <h3 className="text-lg font-bold text-white">Edit Avatar</h3>
                </div>
                <button
                  onClick={handleCancelAvatarEdit}
                  className="p-2 hover:bg-gray-800/50 rounded-xl transition-all duration-300"
                >
                  <XMarkIcon className="h-5 w-5 text-gray-400 hover:text-white" />
                </button>
              </div>
            </div>

            {/* Cropper Area or Preview */}
            <div className="relative h-80 bg-gray-950 flex items-center justify-center">
              {avatarSource ? (
                <Cropper
                  image={avatarSource}
                  crop={crop}
                  zoom={zoom}
                  minZoom={1}
                  maxZoom={3}
                  aspect={1}
                  cropShape="round"
                  showGrid={false}
                  objectFit="vertical-cover"
                  restrictPosition={true}
                  onCropChange={setCrop}
                  onZoomChange={setZoom}
                  onCropComplete={onCropComplete}
                  style={{
                    containerStyle: {
                      backgroundColor: "#030712",
                    },
                  }}
                />
              ) : (
                <div className="flex flex-col items-center gap-5 text-center p-6">
                  <div className="w-48 h-48 rounded-full bg-gradient-to-br from-gray-800 to-gray-700 flex items-center justify-center border-4 border-gray-600/50 overflow-hidden shadow-2xl shadow-black/50 ring-4 ring-indigo-500/20">
                    {avatarPreview || user?.avatar_url ? (
                      <img
                        src={avatarPreview || user?.avatar_url}
                        alt="Current avatar"
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <PhotoIcon className="h-16 w-16 text-gray-500" />
                    )}
                  </div>
                  <p className="text-gray-400 text-sm">
                    {avatarPreview || user?.avatar_url
                      ? "Current avatar"
                      : "No avatar set"}
                  </p>
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    className="flex items-center gap-2 px-5 py-3 bg-indigo-500/20 hover:bg-indigo-500/30 border border-indigo-500/40 text-indigo-300 hover:text-indigo-200 rounded-xl transition-all duration-300"
                  >
                    <CameraIcon className="h-5 w-5" />
                    <span className="text-sm font-medium">
                      Upload New Photo
                    </span>
                  </button>
                </div>
              )}
            </div>

            {/* Zoom Control - only show when cropping */}
            {avatarSource && (
              <div className="px-6 py-4 bg-gray-800/30 border-t border-gray-700/30">
                <div className="flex items-center gap-4">
                  <ArrowsPointingOutIcon className="h-5 w-5 text-gray-400" />
                  <input
                    type="range"
                    min={1}
                    max={3}
                    step={0.05}
                    value={zoom}
                    onChange={(e) => setZoom(Number(e.target.value))}
                    className="flex-1 h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-indigo-500"
                  />
                  <span className="text-gray-400 text-sm font-mono w-12 text-right">
                    {Math.round(zoom * 100)}%
                  </span>
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div className="px-6 py-4 border-t border-gray-700/50 bg-gray-800/20">
              <div className="flex items-center justify-between gap-3">
                {/* Left side - Remove or Upload buttons */}
                <div className="flex items-center gap-2">
                  {/* Remove Avatar Button - show when has avatar (in preview or crop mode) */}
                  {(avatarPreview || user?.avatar_url) && (
                    <button
                      onClick={handleRemoveAvatar}
                      disabled={savingAvatar}
                      className="flex items-center gap-2 px-4 py-2.5 bg-red-500/10 hover:bg-red-500/20 border border-red-500/30 text-red-400 hover:text-red-300 rounded-xl transition-all duration-300 disabled:opacity-50"
                    >
                      <TrashIcon className="h-4 w-4" />
                      <span className="text-sm font-medium">Remove</span>
                    </button>
                  )}
                  {/* Change photo button when cropping */}
                  {avatarSource && (
                    <button
                      onClick={() => fileInputRef.current?.click()}
                      className="flex items-center gap-2 px-4 py-2.5 bg-gray-700/50 hover:bg-gray-600/50 border border-gray-600/50 text-gray-300 hover:text-white rounded-xl transition-all duration-300"
                    >
                      <CameraIcon className="h-4 w-4" />
                      <span className="text-sm font-medium">Change</span>
                    </button>
                  )}
                </div>

                {/* Right side - Cancel & Save */}
                <div className="flex items-center gap-2">
                  <button
                    onClick={handleCancelAvatarEdit}
                    disabled={savingAvatar}
                    className="px-5 py-2.5 bg-gray-800/50 hover:bg-gray-700/50 border border-gray-700/50 text-gray-300 hover:text-white rounded-xl transition-all duration-300 text-sm font-medium disabled:opacity-50"
                  >
                    Cancel
                  </button>
                  {avatarSource && (
                    <button
                      onClick={handleSaveAvatar}
                      disabled={savingAvatar || !croppedAreaPixels}
                      className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-indigo-500 to-purple-500 hover:from-indigo-600 hover:to-purple-600 text-white rounded-xl transition-all duration-300 text-sm font-medium shadow-lg shadow-indigo-500/30 disabled:opacity-50"
                    >
                      {savingAvatar ? (
                        <>
                          <svg
                            className="animate-spin h-4 w-4"
                            fill="none"
                            viewBox="0 0 24 24"
                          >
                            <circle
                              className="opacity-25"
                              cx="12"
                              cy="12"
                              r="10"
                              stroke="currentColor"
                              strokeWidth="4"
                            />
                            <path
                              className="opacity-75"
                              fill="currentColor"
                              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                            />
                          </svg>
                          <span>Saving...</span>
                        </>
                      ) : (
                        <>
                          <CheckIcon className="h-4 w-4" />
                          <span>Save Avatar</span>
                        </>
                      )}
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
