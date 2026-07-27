/**
 * ONYX Platform - Centralized Styles Index
 * Single import point for all styling utilities
 *
 * Usage:
 * import { colors, Button, Badge, getCardClasses } from '@styles';
 *
 * Or individual imports:
 * import { colors } from '@styles/theme';
 * import { Button, Card } from '@components/ui/StyleComponents';
 * import { buttonStyles, cardStyles } from '@styles/classNames';
 */

// Theme constants (colors, spacing, typography, etc.)
export * from "./theme";
export { default as theme } from "./theme";

// Tailwind class name utilities
export * from "./classNames";
export { default as classNames } from "./classNames";

// Pre-built React components
export * from "../components/ui/StyleComponents";
export { default as components } from "../components/ui/StyleComponents";

// Convenience re-exports for most commonly used items
export {
  // Theme
  colors,
  gradients,
  spacing,
  typography,
  shadows,
  borderRadius,
  transitions,
  zIndex,
  // Animation & Dynamic style helpers
  animations,
  dynamicStyles,
  severityColors,
  getSeverityStyles,
} from "./theme";

export {
  // Class utilities
  buttonStyles,
  cardStyles,
  inputStyles,
  badgeStyles,
  tableStyles,
  layoutStyles,
  statusStyles,
  modalStyles,
  alertStyles,
  loadingStyles,
  animationStyles,
  progressStyles,
  chartStyles,
  codeStyles,
  navStyles,
  formStyles,
  // Helper functions
  getButtonClasses,
  getCardClasses,
  getInputClasses,
  getBadgeClasses,
  getAlertClasses,
  getProgressClasses,
} from "./classNames";

export {
  // Components
  Button,
  IconButton,
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
  Badge,
  SeverityBadge,
  Input,
  Textarea,
  Select,
  Alert,
  Spinner,
  LoadingOverlay,
  Skeleton,
  StatusDot,
  StatusIndicator,
  Modal,
  Divider,
  EmptyState,
  StatCard,
  ProgressBar,
  SeverityProgressBar,
  AnimatedListItem,
  DonutChart,
  Code,
  Tabs,
  FormGroup,
  FormLabel,
  FormHint,
  FormError,
  Tooltip,
  Avatar,
  Truncate,
} from "../components/ui/StyleComponents";
