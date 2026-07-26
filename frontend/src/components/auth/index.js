/**
 * Authentication Components - Central Export
 * Modular authentication system with separate components
 */

// Context and Provider
export { AuthProvider, useAuth } from "./AuthContext";

// Form Components
export { LoginForm } from "./LoginForm";
export { RegisterForm } from "./RegisterForm";
export { ForgotPasswordForm } from "./ForgotPasswordForm";
export { ResetPasswordForm } from "./ResetPasswordForm";

// Success/Info Components
export { RegistrationSuccess } from "./RegistrationSuccess";
export { ForgotPasswordSuccess } from "./ForgotPasswordSuccess";
export { EmailVerification } from "./EmailVerification";

// Composite Components
export { UserProfile } from "./UserProfile";
export { AuthModal } from "./AuthModal";
export { ProfileInfo } from "./ProfileInfo";
export { AccountInfo } from "./AccountInfo";
export { AvatarCropModal } from "./AvatarCropModal";
export { SecuritySettings } from "./SecuritySettings";
export { NotificationPreferences } from "./NotificationPreferences";

// Auth Pages
export { EmailVerificationPage, PasswordResetPage, AuthRoutingHandler } from "./AuthPages";

// Verification Banner
export { VerificationBanner } from "./VerificationBanner";

// Route Guards
export { AdminRoute } from "./AdminRoute";
