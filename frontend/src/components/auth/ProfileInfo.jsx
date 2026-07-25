import {
  UserCircleIcon, EnvelopeIcon, BuildingOfficeIcon, CheckBadgeIcon,
  PencilIcon, XMarkIcon, PhoneIcon, GlobeAltIcon, ShieldCheckIcon,
  ClockIcon, CalendarIcon, ArrowPathIcon, ChevronRightIcon,
  InformationCircleIcon, FireIcon, PhotoIcon, CameraIcon,
  TrashIcon, CheckCircleIcon, CommandLineIcon, StarIcon
} from "@heroicons/react/24/outline";
import { CheckIcon } from "@heroicons/react/24/solid";

export const ProfileInfo = ({
  user,
  securityScore,
  getSecurityScoreColor,
  setHoveredCard,
  isEditing,
  formData,
  handleInputChange,
  isUpdating,
  handleSaveProfile,
  handleCancel,
  setIsEditing,
  formatDate,
  formatDateTime,
  timezones,
}) => {
  return (
    <div className="space-y-5 animate-fadeIn">
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
  );
};
