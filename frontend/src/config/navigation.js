/**
 * Navigation Configuration
 * Centralized navigation items for the application
 */
import {
  HomeIcon,
  DocumentTextIcon as DocumentReportIcon,
  CogIcon,
  UserCircleIcon,
  ChartBarIcon,
  UsersIcon,
  ClockIcon,
  ArchiveBoxIcon,
  BuildingOfficeIcon,
} from "@heroicons/react/24/outline";

export const navigation = [
  // Primary Navigation
  {
    name: "Dashboard",
    href: "/dashboard",
    icon: HomeIcon,
    gradient: "from-blue-500 to-cyan-500",
    category: "main",
  },
  {
    name: "Projects",
    href: "/projects",
    icon: UsersIcon,
    gradient: "from-indigo-500 to-purple-500",
    category: "main",
  },
  {
    name: "Reports",
    href: "/reports",
    icon: DocumentReportIcon,
    gradient: "from-purple-500 to-pink-500",
    category: "main",
  },
  {
    name: "Analytics",
    href: "/analytics",
    icon: ChartBarIcon,
    gradient: "from-green-500 to-emerald-500",
    category: "main",
  },
  // Enterprise Features
  {
    name: "User Management",
    href: "/users",
    icon: UserCircleIcon,
    gradient: "from-teal-500 to-blue-500",
    category: "enterprise",
  },
  {
    name: "Audit Logs",
    href: "/audit-logs",
    icon: ClockIcon,
    gradient: "from-amber-500 to-orange-500",
    category: "enterprise",
  },
  {
    name: "Data Retention",
    href: "/retention-policies",
    icon: ArchiveBoxIcon,
    gradient: "from-rose-500 to-pink-500",
    category: "enterprise",
  },
  {
    name: "Compliance",
    href: "/compliance",
    icon: BuildingOfficeIcon,
    gradient: "from-cyan-500 to-blue-500",
    category: "enterprise",
  },
  // Settings
  {
    name: "Settings",
    href: "/settings",
    icon: CogIcon,
    gradient: "from-gray-500 to-gray-600",
    category: "settings",
  },
];

export const getNavigationByCategory = (category) => {
  return navigation.filter((item) => item.category === category);
};

export default navigation;
