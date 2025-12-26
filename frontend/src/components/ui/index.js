/**
 * ONYX UI Components Library
 * Advanced, accessible, and beautifully animated UI components
 */

// Core Components
export {
  default as Skeleton,
  SkeletonText,
  SkeletonCard,
  SkeletonTable,
  SkeletonStats,
} from "./Skeleton";
export { default as Tooltip } from "./Tooltip";
export { default as Modal, ConfirmModal } from "./Modal";
export { default as Dropdown, DropdownButton } from "./Dropdown";
export { default as Tabs } from "./Tabs";
export { default as Badge, SeverityBadge, StatusBadge } from "./Badge";
export { default as Avatar, AvatarGroup } from "./Avatar";
export {
  default as Progress,
  CircularProgress,
  SegmentedProgress,
} from "./Progress";
export { default as Switch, SwitchGroup } from "./Switch";
export { default as Notification, NotificationContainer } from "./Notification";
export { default as AnimatedCard, FeatureCard } from "./AnimatedCard";
export { default as FloatingActionButton } from "./FloatingActionButton";
export { default as SearchInput, CommandPalette } from "./SearchInput";
export { default as DataTable } from "./DataTable";
export { default as StatCard, StatsGrid, CompactStat } from "./StatCard";

// Card Components
export {
  default as Card,
  CardHeader,
  CardContent,
  CardFooter,
  ListCard,
  StatsCard,
  GradientCard,
} from "./Card";

// Empty States
export {
  default as EmptyState,
  NoSearchResults,
  NoDataState,
  ErrorState,
  ComingSoonState,
} from "./EmptyState";

// Animation Components
export {
  default as PageTransition,
  AnimatedSection,
  StaggeredList,
  FadeIn,
  ScaleIn,
  SlideIn,
  ConditionalAnimation,
  HoverScale,
  PulseAnimation,
} from "./PageTransition";

// Form Components
export { default as Button, IconButton, ButtonGroup } from "./Button";
export { default as Input, TextArea, Select } from "./Input";

// Hooks
export {
  useDebounce,
  useLocalStorage,
  useMediaQuery,
  useIsMobile,
  useIsTablet,
  useIsDesktop,
  useOnClickOutside,
  useKeyPress,
  useScrollPosition,
  useIntersectionObserver,
  useAnimatedCounter,
  useCopyToClipboard,
  useToggle,
  usePrevious,
  useHover,
  useWindowSize,
  useInterval,
} from "./hooks";

// Chart Components
export {
  BarChart,
  HorizontalBarChart,
  DonutChart,
  LineChart,
  Sparkline,
  GaugeChart,
  ChartContainer,
} from "./Chart";

// Layout Components
export {
  Container,
  Grid,
  Flex,
  Breadcrumb,
  PageHeader,
  Section,
  Divider,
  Stack,
  AspectRatio,
  Center,
} from "./Layout";
