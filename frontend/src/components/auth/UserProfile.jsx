import {
  useState,
  useEffect,
  useMemo,
  useCallback,
  useRef} from "react";
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
  ArrowRightOnRectangleIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ClockIcon,
  CalendarIcon,
  SparklesIcon,
  FingerPrintIcon,
  BellIcon,
  CameraIcon,
  ArrowPathIcon,
  ChevronRightIcon,
  InformationCircleIcon,
  DocumentDuplicateIcon,
  StarIcon,
  TrophyIcon,
  FireIcon,
  CommandLineIcon,
  PhotoIcon,
  ArrowsPointingOutIcon,
  TrashIcon} from "@heroicons/react/24/outline";
import { CheckIcon } from "@heroicons/react/24/solid";
import toast from "react-hot-toast";
import { useAuth } from "./AuthContext";
import { authAPI } from "../../services/api";
import { SecuritySettings } from "./SecuritySettings";
import { NotificationPreferences } from "./NotificationPreferences";

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
    refreshUserProfile} = useAuth();
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
    }, 200);
  };

  // ===== PROFILE HANDLERS =====
  const [formData, setFormData] = useState({
    full_name: user?.full_name || "",
    organization: user?.organization || "",
    department: user?.department || "",
    phone: user?.phone || "",
    timezone: user?.timezone || "UTC"});

  useEffect(() => {
    if (user) {
      setFormData({
        full_name: user.full_name || "",
        organization: user.organization || "",
        department: user.department || "",
        phone: user.phone || "",
        timezone: user.timezone || "UTC"});
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
      timezone: user?.timezone || "UTC"});
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
        ctx.drawImage(image, pixelCrop.x, pixelCrop.y, pixelCrop.width, pixelCrop.height, 0, 0, outputSize, outputSize);
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
    return date.toLocaleString("en-US", { year: "numeric", month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
  };

  const copyToClipboard = useCallback((text) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    toast.success("Copied to clipboard!");
    setTimeout(() => setCopied(false), 2000);
  }, []);

  const timezones = [
    "UTC", "America/New_York", "America/Chicago", "America/Denver",
    "America/Los_Angeles", "Europe/London", "Europe/Paris", "Europe/Berlin",
    "Asia/Tokyo", "Asia/Shanghai", "Asia/Kolkata", "Australia/Sydney",
  ];

  // ===== SECURITY SCORE =====
  const securityScore = useMemo(() => {
    let score = 0;
    const factors = [];
    if (user?.is_email_verified) { score += 25; factors.push({ name: "Email Verified", completed: true }); }
    else { factors.push({ name: "Email Verified", completed: false }); }
    if (user?.phone) { score += 15; factors.push({ name: "Phone Added", completed: true }); }
    else { factors.push({ name: "Phone Added", completed: false }); }
    if (twoFactorEnabled) { score += 30; factors.push({ name: "2FA Enabled", completed: true }); }
    else { factors.push({ name: "2FA Enabled", completed: false }); }
    if (user?.organization) { score += 10; factors.push({ name: "Organization Set", completed: true }); }
    else { factors.push({ name: "Organization Set", completed: false }); }
    score += 20;
    factors.push({ name: "Strong Password", completed: true });
    return { score, factors };
  }, [user, twoFactorEnabled]);

  const getSecurityScoreColor = (score) => {
    if (score >= 80) return { gradient: "from-emerald-500 to-green-500", text: "text-emerald-400", bg: "bg-emerald-500" };
    if (score >= 60) return { gradient: "from-yellow-500 to-amber-500", text: "text-yellow-400", bg: "bg-yellow-500" };
    if (score >= 40) return { gradient: "from-orange-500 to-red-500", text: "text-orange-400", bg: "bg-orange-500" };
    return { gradient: "from-red-500 to-rose-500", text: "text-red-400", bg: "bg-red-500" };
  };

  const tabs = [
    { key: "profile", label: "Profile", icon: UserCircleIcon },
    { key: "account", label: "Account", icon: SparklesIcon },
    { key: "security", label: "Security", icon: ShieldCheckIcon },
    { key: "notifications", label: "Alerts", icon: BellIcon },
  ];

  return (
    <div className={`fixed inset-0 z-50 flex items-center justify-center p-4 transition-all duration-300 ${isClosing ? "opacity-0" : "opacity-100"}`}>
      {/* Backdrop */}
      <div className="absolute inset-0 bg-gradient-to-br from-black/80 via-gray-900/90 to-black/80 backdrop-blur-xl" onClick={handleClose} />

      {/* Floating particles */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {[...Array(6)].map((_, i) => (
          <div key={i} className="absolute w-2 h-2 bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full opacity-20 animate-float"
            style={{ left: `${20 + i * 15}%`, top: `${10 + i * 12}%`, animationDelay: `${i * 0.5}s`, animationDuration: `${4 + i}s` }}
          />
        ))}
      </div>

      {/* Modal */}
      <div className={`relative w-full max-w-3xl max-h-[92vh] overflow-hidden bg-gradient-to-br from-gray-900/95 via-gray-900/98 to-gray-800/95 rounded-3xl shadow-2xl shadow-purple-500/10 border border-gray-700/50 transition-all duration-500 ${
        isClosing ? "scale-95 opacity-0 translate-y-4" : "scale-100 opacity-100 translate-y-0"
      }`}>
        {/* Animated Background Effects */}
        <div className="absolute inset-0 overflow-hidden rounded-3xl pointer-events-none">
          <div className="absolute -top-40 -left-40 w-80 h-80 bg-gradient-to-br from-indigo-500/20 via-purple-500/15 to-transparent rounded-full blur-3xl animate-pulse" />
          <div className="absolute -bottom-40 -right-40 w-80 h-80 bg-gradient-to-tl from-cyan-500/20 via-blue-500/15 to-transparent rounded-full blur-3xl animate-pulse"
            style={{ animationDelay: "1s" }}
          />
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-gradient-radial from-purple-500/5 to-transparent rounded-full blur-3xl" />
          <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.01)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.01)_1px,transparent_1px)] bg-[size:60px_60px]" />
        </div>

        {/* Header */}
        <div className="relative border-b border-gray-700/50 bg-gradient-to-r from-gray-900/50 to-gray-800/50 backdrop-blur-sm">
          <div className="p-6 pb-4">
            <div className="flex items-start justify-between">
              {/* Profile Header */}
              <div className="flex items-center gap-5">
                {/* Avatar */}
                <div className="relative group">
                  <div className="absolute -inset-1 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 rounded-2xl opacity-75 blur group-hover:opacity-100 transition-opacity duration-300" />
                  <div className={`relative w-20 h-20 bg-gradient-to-br ${avatarGradient} rounded-2xl flex items-center justify-center shadow-xl transition-all duration-300 group-hover:scale-105 overflow-hidden cursor-pointer`}
                    onClick={handleAvatarClick}
                  >
                    {avatarPreview || user?.avatar_url ? (
                      <img src={avatarPreview || user?.avatar_url} alt="Avatar" className="w-full h-full object-cover" />
                    ) : (
                      <span className="text-2xl font-bold text-white drop-shadow-lg">{userInitials}</span>
                    )}
                    <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 flex items-center justify-center transition-all duration-300">
                      {avatarPreview || user?.avatar_url ? <PencilIcon className="h-6 w-6 text-white" /> : <CameraIcon className="h-6 w-6 text-white" />}
                    </div>
                  </div>
                  <input ref={fileInputRef} type="file" accept="image/*" onChange={handleAvatarSelect} className="hidden" />
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
                      <span className="px-2 py-0.5 bg-gradient-to-r from-amber-500/20 to-orange-500/20 border border-amber-500/30 rounded-full text-xs font-semibold text-amber-400">Admin</span>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <p className="text-gray-400 text-sm flex items-center gap-1.5 font-mono">
                      <span className="text-indigo-400">@</span>
                      {user?.username}
                    </p>
                    <button onClick={() => copyToClipboard(user?.username)} className="p-1 hover:bg-gray-700/50 rounded-lg transition-colors" title="Copy username">
                      <DocumentDuplicateIcon className={`h-3.5 w-3.5 ${copied ? "text-green-400" : "text-gray-500 hover:text-gray-300"}`} />
                    </button>
                  </div>
                  <div className="flex items-center gap-3 mt-3">
                    <div className="relative h-2 w-32 bg-gray-700/50 rounded-full overflow-hidden">
                      <div className="absolute inset-y-0 left-0 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 rounded-full transition-all duration-700 ease-out"
                        style={{ width: `${profileCompletion}%` }}
                      />
                      <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-shimmer" />
                    </div>
                    <span className="text-xs font-medium text-gray-400">{profileCompletion}% complete</span>
                    {profileCompletion === 100 && <TrophyIcon className="h-4 w-4 text-yellow-400 animate-bounce-subtle" />}
                  </div>
                </div>
              </div>

              <button onClick={handleClose} className="p-2.5 hover:bg-red-500/10 hover:border-red-500/30 border border-transparent rounded-xl transition-all duration-300 group">
                <XMarkIcon className="h-5 w-5 text-gray-400 group-hover:text-red-400 group-hover:rotate-90 transition-all duration-300" />
              </button>
            </div>

            {/* Tabs */}
            <div className="flex gap-1 mt-6 p-1.5 bg-gray-800/60 rounded-2xl backdrop-blur-sm border border-gray-700/50">
              {tabs.map((tab) => (
                <button key={tab.key} onClick={() => setActiveTab(tab.key)}
                  className={`relative flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-300 ${
                    activeTab === tab.key ? "text-white" : "text-gray-400 hover:text-gray-300 hover:bg-gray-700/50"
                  }`}
                >
                  {activeTab === tab.key && (
                    <div className="absolute inset-0 bg-gradient-to-r from-indigo-500/20 via-purple-500/20 to-pink-500/20 rounded-xl border border-indigo-500/30 shadow-lg shadow-indigo-500/10" />
                  )}
                  <tab.icon className={`h-4 w-4 relative z-10 transition-transform duration-300 ${activeTab === tab.key ? "scale-110" : ""}`} />
                  <span className="relative z-10 hidden sm:inline">{tab.label}</span>
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
              {/* Security Score Card */}
              <div className="relative overflow-hidden rounded-2xl p-5 bg-gradient-to-br from-gray-800/40 to-gray-900/40 border border-gray-700/50 group hover:border-indigo-500/20 transition-all duration-500"
                onMouseEnter={() => setHoveredCard("security")} onMouseLeave={() => setHoveredCard(null)}
              >
                <div className="absolute inset-0 bg-gradient-to-r from-indigo-500/5 via-purple-500/5 to-pink-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                <div className="relative flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="relative">
                      <svg className="w-16 h-16 -rotate-90">
                        <circle cx="32" cy="32" r="28" fill="none" stroke="currentColor" strokeWidth="4" className="text-gray-700" />
                        <circle cx="32" cy="32" r="28" fill="none" stroke="url(#scoreGradient)" strokeWidth="4" strokeLinecap="round"
                          strokeDasharray={`${(securityScore.score / 100) * 176} 176`} className="transition-all duration-1000 ease-out"
                        />
                        <defs>
                          <linearGradient id="scoreGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                            <stop offset="0%" stopColor="#6366f1" /><stop offset="50%" stopColor="#a855f7" /><stop offset="100%" stopColor="#ec4899" />
                          </linearGradient>
                        </defs>
                      </svg>
                      <div className="absolute inset-0 flex items-center justify-center">
                        <span className={`text-lg font-bold ${getSecurityScoreColor(securityScore.score).text}`}>{securityScore.score}</span>
                      </div>
                    </div>
                    <div>
                      <h3 className="text-white font-semibold flex items-center gap-2">
                        Security Score
                        {securityScore.score >= 80 && <FireIcon className="h-4 w-4 text-orange-400" />}
                      </h3>
                      <p className="text-gray-400 text-sm">
                        {securityScore.score >= 80 ? "Excellent protection" : securityScore.score >= 60 ? "Good, but can improve" : "Needs attention"}
                      </p>
                    </div>
                  </div>
                  <div className="hidden md:flex flex-wrap gap-2 max-w-xs">
                    {securityScore.factors.slice(0, 4).map((factor, i) => (
                      <span key={i} className={`px-2 py-1 text-xs rounded-lg border ${factor.completed ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400" : "bg-gray-700/50 border-gray-600/50 text-gray-400"}`}>
                        {factor.completed ? "✓" : "○"} {factor.name}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              {/* Quick Stats */}
              <div className="grid grid-cols-3 gap-3">
                {[
                  { label: "Member Since", value: formatDate(user?.created_at)?.split(",")[0]?.split(" ")[0] || "N/A", icon: CalendarIcon, gradient: "from-indigo-500/10 to-purple-500/10", border: "border-indigo-500/20", iconBg: "bg-indigo-500/20", iconColor: "text-indigo-400" },
                  { label: "Account Role", value: user?.role || "User", icon: ShieldCheckIcon, gradient: "from-emerald-500/10 to-teal-500/10", border: "border-emerald-500/20", iconBg: "bg-emerald-500/20", iconColor: "text-emerald-400" },
                  { label: user?.is_email_verified ? "Verified" : "Unverified", value: user?.is_email_verified ? "✓" : "○", icon: CheckBadgeIcon,
                    gradient: user?.is_email_verified ? "from-green-500/10 to-emerald-500/10" : "from-amber-500/10 to-orange-500/10",
                    border: user?.is_email_verified ? "border-green-500/20" : "border-amber-500/20",
                    iconBg: user?.is_email_verified ? "bg-green-500/20" : "bg-amber-500/20",
                    iconColor: user?.is_email_verified ? "text-green-400" : "text-amber-400" },
                ].map((stat, i) => (
                  <div key={i} className={`bg-gradient-to-br ${stat.gradient} border ${stat.border} rounded-2xl p-4 text-center group hover:scale-[1.02] transition-all duration-300 cursor-default`}>
                    <div className={`inline-flex p-2 ${stat.iconBg} rounded-xl mb-2 group-hover:scale-110 transition-transform duration-300`}>
                      <stat.icon className={`h-5 w-5 ${stat.iconColor}`} />
                    </div>
                    <p className="text-xl font-bold text-white capitalize">{stat.value}</p>
                    <p className="text-xs text-gray-400 mt-1">{stat.label}</p>
                  </div>
                ))}
              </div>

              {/* Profile Fields */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="group bg-gray-800/30 hover:bg-gray-800/50 border border-gray-700/50 hover:border-indigo-500/30 rounded-2xl p-4 transition-all duration-300 hover:shadow-lg hover:shadow-indigo-500/5">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="p-1.5 bg-indigo-500/20 rounded-lg group-hover:scale-110 transition-transform duration-300">
                      <UserCircleIcon className="h-4 w-4 text-indigo-400" />
                    </div>
                    <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">Username</span>
                    <span className="ml-auto px-2 py-0.5 text-[10px] bg-gray-700/50 text-gray-400 rounded-full">Read-only</span>
                  </div>
                  <p className="text-white font-medium pl-9 font-mono">@{user?.username}</p>
                </div>

                <div className="group bg-gray-800/30 hover:bg-gray-800/50 border border-gray-700/50 hover:border-cyan-500/30 rounded-2xl p-4 transition-all duration-300 hover:shadow-lg hover:shadow-cyan-500/5">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <div className="p-1.5 bg-cyan-500/20 rounded-lg group-hover:scale-110 transition-transform duration-300">
                        <EnvelopeIcon className="h-4 w-4 text-cyan-400" />
                      </div>
                      <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">Email</span>
                    </div>
                    {user?.is_email_verified ? (
                      <span className="flex items-center gap-1 text-xs text-green-400 bg-green-500/10 px-2.5 py-1 rounded-full border border-green-500/20 animate-pulse-subtle">
                        <CheckBadgeIcon className="h-3.5 w-3.5" /> Verified
                      </span>
                    ) : (
                      <span className="flex items-center gap-1 text-xs text-amber-400 bg-amber-500/10 px-2.5 py-1 rounded-full border border-amber-500/20">
                        <ClockIcon className="h-3.5 w-3.5" /> Pending
                      </span>
                    )}
                  </div>
                  <p className="text-white font-medium pl-9 truncate">{user?.email}</p>
                </div>
              </div>

              {/* Editable Fields */}
              <div className="space-y-4">
                <div className="group bg-gray-800/30 hover:bg-gray-800/50 border border-gray-700/50 hover:border-purple-500/30 rounded-2xl p-4 transition-all duration-300 hover:shadow-lg hover:shadow-purple-500/5">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="p-1.5 bg-purple-500/20 rounded-lg group-hover:scale-110 transition-transform duration-300">
                      <UserCircleIcon className="h-4 w-4 text-purple-400" />
                    </div>
                    <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">Full Name</span>
                    {isEditing && <span className="ml-auto text-xs text-indigo-400 animate-pulse">Editing...</span>}
                  </div>
                  {isEditing ? (
                    <input type="text" name="full_name" value={formData.full_name} onChange={handleInputChange}
                      className="w-full pl-9 pr-4 py-2.5 bg-gray-900/70 border border-purple-500/30 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-500/30 transition-all duration-300"
                      placeholder="Enter your full name"
                    />
                  ) : (
                    <p className="text-white font-medium pl-9">{user?.full_name || <span className="text-gray-500 italic flex items-center gap-1"><InformationCircleIcon className="h-4 w-4" /> Not provided</span>}</p>
                  )}
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="group bg-gray-800/30 hover:bg-gray-800/50 border border-gray-700/50 hover:border-blue-500/30 rounded-2xl p-4 transition-all duration-300 hover:shadow-lg hover:shadow-blue-500/5">
                    <div className="flex items-center gap-2 mb-2">
                      <div className="p-1.5 bg-blue-500/20 rounded-lg group-hover:scale-110 transition-transform duration-300">
                        <BuildingOfficeIcon className="h-4 w-4 text-blue-400" />
                      </div>
                      <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">Organization</span>
                    </div>
                    {isEditing ? (
                      <input type="text" name="organization" value={formData.organization} onChange={handleInputChange}
                        className="w-full pl-9 pr-4 py-2.5 bg-gray-900/70 border border-blue-500/30 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/30 transition-all duration-300"
                        placeholder="Your organization"
                      />
                    ) : (
                      <p className="text-white font-medium pl-9">{user?.organization || <span className="text-gray-500 italic">Not provided</span>}</p>
                    )}
                  </div>

                  <div className="group bg-gray-800/30 hover:bg-gray-800/50 border border-gray-700/50 hover:border-pink-500/30 rounded-2xl p-4 transition-all duration-300 hover:shadow-lg hover:shadow-pink-500/5">
                    <div className="flex items-center gap-2 mb-2">
                      <div className="p-1.5 bg-pink-500/20 rounded-lg group-hover:scale-110 transition-transform duration-300">
                        <CommandLineIcon className="h-4 w-4 text-pink-400" />
                      </div>
                      <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">Department</span>
                    </div>
                    {isEditing ? (
                      <input type="text" name="department" value={formData.department} onChange={handleInputChange}
                        className="w-full pl-9 pr-4 py-2.5 bg-gray-900/70 border border-pink-500/30 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-pink-500 focus:ring-2 focus:ring-pink-500/30 transition-all duration-300"
                        placeholder="Your department"
                      />
                    ) : (
                      <p className="text-white font-medium pl-9">{user?.department || <span className="text-gray-500 italic">Not provided</span>}</p>
                    )}
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="group bg-gray-800/30 hover:bg-gray-800/50 border border-gray-700/50 hover:border-green-500/30 rounded-2xl p-4 transition-all duration-300 hover:shadow-lg hover:shadow-green-500/5">
                    <div className="flex items-center gap-2 mb-2">
                      <div className="p-1.5 bg-green-500/20 rounded-lg group-hover:scale-110 transition-transform duration-300">
                        <PhoneIcon className="h-4 w-4 text-green-400" />
                      </div>
                      <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">Phone</span>
                      {!user?.phone && !isEditing && <span className="ml-auto px-2 py-0.5 text-[10px] bg-amber-500/10 border border-amber-500/20 text-amber-400 rounded-full">+15 security</span>}
                    </div>
                    {isEditing ? (
                      <input type="tel" name="phone" value={formData.phone} onChange={handleInputChange}
                        className="w-full pl-9 pr-4 py-2.5 bg-gray-900/70 border border-green-500/30 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-green-500 focus:ring-2 focus:ring-green-500/30 transition-all duration-300"
                        placeholder="+1 (555) 000-0000"
                      />
                    ) : (
                      <p className="text-white font-medium pl-9">{user?.phone || <span className="text-gray-500 italic">Not provided</span>}</p>
                    )}
                  </div>

                  <div className="group bg-gray-800/30 hover:bg-gray-800/50 border border-gray-700/50 hover:border-orange-500/30 rounded-2xl p-4 transition-all duration-300 hover:shadow-lg hover:shadow-orange-500/5">
                    <div className="flex items-center gap-2 mb-2">
                      <div className="p-1.5 bg-orange-500/20 rounded-lg group-hover:scale-110 transition-transform duration-300">
                        <GlobeAltIcon className="h-4 w-4 text-orange-400" />
                      </div>
                      <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">Timezone</span>
                    </div>
                    {isEditing ? (
                      <div className="relative">
                        <select name="timezone" value={formData.timezone} onChange={handleInputChange}
                          className="w-full pl-9 pr-10 py-2.5 bg-gray-900/70 border border-orange-500/30 rounded-xl text-white focus:outline-none focus:border-orange-500 focus:ring-2 focus:ring-orange-500/30 transition-all duration-300 appearance-none cursor-pointer"
                        >
                          {timezones.map((tz) => <option key={tz} value={tz} className="bg-gray-900">{tz.replace(/_/g, " ")}</option>)}
                        </select>
                        <ChevronRightIcon className="absolute right-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400 rotate-90 pointer-events-none" />
                      </div>
                    ) : (
                      <p className="text-white font-medium pl-9">{(user?.timezone || "UTC").replace(/_/g, " ")}</p>
                    )}
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="pt-5">
                {isEditing ? (
                  <div className="flex gap-3">
                    <button onClick={handleSaveProfile} disabled={isUpdating}
                      className="flex-1 py-3.5 px-6 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 text-white font-semibold rounded-xl hover:from-indigo-600 hover:via-purple-600 hover:to-pink-600 shadow-lg shadow-purple-500/25 hover:shadow-purple-500/40 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none flex items-center justify-center gap-2 group"
                    >
                      {isUpdating ? <><ArrowPathIcon className="w-5 h-5 animate-spin" /> Saving...</> : <><CheckCircleIcon className="h-5 w-5 group-hover:scale-110 transition-transform" /> Save Changes</>}
                    </button>
                    <button onClick={handleCancel} disabled={isUpdating}
                      className="flex-1 py-3.5 px-6 bg-gray-700/50 hover:bg-gray-700 text-white font-semibold rounded-xl border border-gray-600/50 hover:border-gray-500 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                    >
                      <XMarkIcon className="h-5 w-5" /> Cancel
                    </button>
                  </div>
                ) : (
                  <button onClick={() => setIsEditing(true)}
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

          {/* Account Tab */}
          {activeTab === "account" && (
            <div className="space-y-5 animate-fadeIn">
              <div className={`relative overflow-hidden rounded-2xl p-6 border transition-all duration-500 ${
                user?.is_email_verified ? "bg-gradient-to-br from-emerald-500/10 via-green-500/5 to-teal-500/10 border-emerald-500/20" : "bg-gradient-to-br from-amber-500/10 via-orange-500/5 to-yellow-500/10 border-amber-500/20"
              }`}>
                <div className="absolute inset-0 opacity-30">
                  <div className={`absolute inset-0 ${user?.is_email_verified ? "bg-[radial-gradient(circle_at_50%_50%,rgba(16,185,129,0.1),transparent_70%)]" : "bg-[radial-gradient(circle_at_50%_50%,rgba(245,158,11,0.1),transparent_70%)]"}`} />
                </div>
                <div className="relative flex items-start gap-4">
                  <div className={`p-3.5 rounded-2xl ${user?.is_email_verified ? "bg-gradient-to-br from-emerald-500/30 to-green-500/20" : "bg-gradient-to-br from-amber-500/30 to-orange-500/20"} shadow-lg`}>
                    {user?.is_email_verified ? <CheckCircleIcon className="h-8 w-8 text-emerald-400" /> : <ExclamationTriangleIcon className="h-8 w-8 text-amber-400 animate-pulse" />}
                  </div>
                  <div className="flex-1">
                    <h4 className="text-white font-bold text-lg mb-1 flex items-center gap-2">
                      Email Verification
                      {user?.is_email_verified && <span className="px-2 py-0.5 text-xs bg-emerald-500/20 text-emerald-400 rounded-full border border-emerald-500/30">Complete</span>}
                    </h4>
                    <p className="text-gray-400 text-sm leading-relaxed">
                      {user?.is_email_verified ? "Your email address has been verified." : "Verify your email to unlock all features, improve account security, and receive important notifications."}
                    </p>
                    {!user?.is_email_verified && (
                      <button onClick={handleResendVerification}
                        className="mt-4 px-5 py-2.5 bg-gradient-to-r from-amber-500/20 to-orange-500/20 hover:from-amber-500/30 hover:to-orange-500/30 text-amber-300 text-sm font-semibold rounded-xl border border-amber-500/30 hover:border-amber-500/50 transition-all duration-300 flex items-center gap-2 group"
                      >
                        <EnvelopeIcon className="h-4 w-4 group-hover:scale-110 transition-transform" />
                        Resend Verification Email
                        <ChevronRightIcon className="h-4 w-4 group-hover:translate-x-1 transition-transform" />
                      </button>
                    )}
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="group bg-gray-800/30 border border-gray-700/50 hover:border-blue-500/30 rounded-2xl p-5 hover:bg-gray-800/50 transition-all duration-300 hover:shadow-lg hover:shadow-blue-500/5">
                  <div className="flex items-center gap-3 mb-5">
                    <div className="p-2.5 bg-gradient-to-br from-blue-500/20 to-indigo-500/20 rounded-xl group-hover:scale-110 transition-transform duration-300">
                      <ShieldCheckIcon className="h-6 w-6 text-blue-400" />
                    </div>
                    <h4 className="text-white font-semibold text-lg">Account Status</h4>
                  </div>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between p-3 bg-gray-900/40 rounded-xl">
                      <span className="text-gray-400 text-sm flex items-center gap-2"><CheckBadgeIcon className="h-4 w-4 text-emerald-400" /> Status</span>
                      <span className="px-3 py-1.5 bg-gradient-to-r from-emerald-500/20 to-green-500/20 text-emerald-400 text-xs font-semibold rounded-lg border border-emerald-500/30 flex items-center gap-1">
                        <span className="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-pulse" /> {user?.status || "Active"}
                      </span>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-gray-900/40 rounded-xl">
                      <span className="text-gray-400 text-sm flex items-center gap-2"><StarIcon className="h-4 w-4 text-indigo-400" /> Role</span>
                      <span className="px-3 py-1.5 bg-gradient-to-r from-indigo-500/20 to-purple-500/20 text-indigo-400 text-xs font-semibold rounded-lg border border-indigo-500/30 capitalize">{user?.role || "User"}</span>
                    </div>
                  </div>
                </div>

                <div className="group bg-gray-800/30 border border-gray-700/50 hover:border-purple-500/30 rounded-2xl p-5 hover:bg-gray-800/50 transition-all duration-300 hover:shadow-lg hover:shadow-purple-500/5">
                  <div className="flex items-center gap-3 mb-5">
                    <div className="p-2.5 bg-gradient-to-br from-purple-500/20 to-pink-500/20 rounded-xl group-hover:scale-110 transition-transform duration-300">
                      <ClockIcon className="h-6 w-6 text-purple-400" />
                    </div>
                    <h4 className="text-white font-semibold text-lg">Activity</h4>
                  </div>
                  <div className="space-y-4">
                    <div className="p-3 bg-gray-900/40 rounded-xl">
                      <div className="flex items-center gap-2 text-gray-400 text-xs mb-1"><CalendarIcon className="h-3.5 w-3.5" /> Member Since</div>
                      <span className="text-white text-sm font-medium">{formatDate(user?.created_at)}</span>
                    </div>
                    <div className="p-3 bg-gray-900/40 rounded-xl">
                      <div className="flex items-center gap-2 text-gray-400 text-xs mb-1"><ArrowPathIcon className="h-3.5 w-3.5" /> Last Login</div>
                      <span className="text-white text-sm font-medium">{formatDateTime(user?.last_login)}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Security Tab */}
          {activeTab === "security" && (
            <SecuritySettings securityScore={securityScore} getSecurityScoreColor={getSecurityScoreColor} onLogout={handleLogout} />
          )}

          {/* Notifications Tab */}
          {activeTab === "notifications" && <NotificationPreferences />}
        </div>
      </div>

      {/* Avatar Crop Modal */}
      {showAvatarModal && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
          <div className="bg-gray-900 border border-gray-700/50 rounded-3xl shadow-2xl w-full max-w-xl overflow-hidden animate-scale-in">
            <div className="px-6 py-4 border-b border-gray-700/50 bg-gradient-to-r from-indigo-500/10 to-purple-500/10">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-gradient-to-br from-indigo-500/20 to-purple-500/20 rounded-xl">
                    <PhotoIcon className="h-5 w-5 text-indigo-400" />
                  </div>
                  <h3 className="text-lg font-bold text-white">Edit Avatar</h3>
                </div>
                <button onClick={handleCancelAvatarEdit} className="p-2 hover:bg-gray-800/50 rounded-xl transition-all duration-300">
                  <XMarkIcon className="h-5 w-5 text-gray-400 hover:text-white" />
                </button>
              </div>
            </div>

            <div className="relative h-80 bg-gray-950 flex items-center justify-center">
              {avatarSource ? (
                <Cropper image={avatarSource} crop={crop} zoom={zoom} minZoom={1} maxZoom={3} aspect={1} cropShape="round"
                  showGrid={false} objectFit="vertical-cover" restrictPosition={true}
                  onCropChange={setCrop} onZoomChange={setZoom} onCropComplete={onCropComplete}
                  style={{ containerStyle: { backgroundColor: "#030712" } }}
                />
              ) : (
                <div className="flex flex-col items-center gap-5 text-center p-6">
                  <div className="w-48 h-48 rounded-full bg-gradient-to-br from-gray-800 to-gray-700 flex items-center justify-center border-4 border-gray-600/50 overflow-hidden shadow-2xl shadow-black/50 ring-4 ring-indigo-500/20">
                    {avatarPreview || user?.avatar_url ? (
                      <img src={avatarPreview || user?.avatar_url} alt="Current avatar" className="w-full h-full object-cover" />
                    ) : (
                      <PhotoIcon className="h-16 w-16 text-gray-500" />
                    )}
                  </div>
                  <button onClick={() => fileInputRef.current?.click()} className="flex items-center gap-2 px-5 py-3 bg-indigo-500/20 hover:bg-indigo-500/30 border border-indigo-500/40 text-indigo-300 hover:text-indigo-200 rounded-xl transition-all duration-300">
                    <CameraIcon className="h-5 w-5" />
                    <span className="text-sm font-medium">Upload New Photo</span>
                  </button>
                </div>
              )}
            </div>

            {avatarSource && (
              <div className="px-6 py-4 bg-gray-800/30 border-t border-gray-700/30">
                <div className="flex items-center gap-4">
                  <ArrowsPointingOutIcon className="h-5 w-5 text-gray-400" />
                  <input type="range" min={1} max={3} step={0.05} value={zoom} onChange={(e) => setZoom(Number(e.target.value))}
                    className="flex-1 h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-indigo-500"
                  />
                  <span className="text-gray-400 text-sm font-mono w-12 text-right">{Math.round(zoom * 100)}%</span>
                </div>
              </div>
            )}

            <div className="px-6 py-4 border-t border-gray-700/50 bg-gray-800/20">
              <div className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  {(avatarPreview || user?.avatar_url) && (
                    <button onClick={handleRemoveAvatar} disabled={savingAvatar}
                      className="flex items-center gap-2 px-4 py-2.5 bg-red-500/10 hover:bg-red-500/20 border border-red-500/30 text-red-400 hover:text-red-300 rounded-xl transition-all duration-300 disabled:opacity-50"
                    >
                      <TrashIcon className="h-4 w-4" />
                      <span className="text-sm font-medium">Remove</span>
                    </button>
                  )}
                  {avatarSource && (
                    <button onClick={() => fileInputRef.current?.click()}
                      className="flex items-center gap-2 px-4 py-2.5 bg-gray-700/50 hover:bg-gray-600/50 border border-gray-600/50 text-gray-300 hover:text-white rounded-xl transition-all duration-300"
                    >
                      <CameraIcon className="h-4 w-4" />
                      <span className="text-sm font-medium">Change</span>
                    </button>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <button onClick={handleCancelAvatarEdit} disabled={savingAvatar}
                    className="px-5 py-2.5 bg-gray-800/50 hover:bg-gray-700/50 border border-gray-700/50 text-gray-300 hover:text-white rounded-xl transition-all duration-300 text-sm font-medium disabled:opacity-50"
                  >
                    Cancel
                  </button>
                  {avatarSource && (
                    <button onClick={handleSaveAvatar} disabled={savingAvatar || !croppedAreaPixels}
                      className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-indigo-500 to-purple-500 hover:from-indigo-600 hover:to-purple-600 text-white rounded-xl transition-all duration-300 text-sm font-medium shadow-lg shadow-indigo-500/30 disabled:opacity-50"
                    >
                      {savingAvatar ? (
                        <><svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" /></svg> Saving...</>
                      ) : (
                        <><CheckIcon className="h-4 w-4" /> Save Avatar</>
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
