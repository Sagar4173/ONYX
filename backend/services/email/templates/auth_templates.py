"""
Authentication Email Templates
Handles verification, password reset, login alerts, and 2FA notifications
"""

from .base_template import get_base_template, GRADIENTS


def get_verification_template() -> str:
    """Email verification template"""
    return get_base_template(
        title="Email Verification",
        header_gradient=GRADIENTS["purple"],
        header_icon="✉️",
        header_subtitle="Verify Your Email Address",
        content='''
        <h2 style="color: #f1f5f9; font-size: 24px; margin: 0 0 16px 0; font-weight: 600;">
            Welcome to SecureDevOps! 👋
        </h2>
        
        <p style="color: #94a3b8; font-size: 16px; line-height: 1.7; margin: 0 0 24px 0;">
            Thank you for joining our platform. To complete your registration and unlock all security features, please verify your email address.
        </p>
        
        <!-- CTA Button -->
        <div style="text-align: center; margin: 32px 0;">
            <a href="{{ verification_url }}" 
               style="background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); 
                      color: #ffffff; 
                      padding: 16px 40px; 
                      text-decoration: none; 
                      border-radius: 12px; 
                      display: inline-block;
                      font-weight: 600;
                      font-size: 16px;
                      box-shadow: 0 10px 30px -5px rgba(99, 102, 241, 0.5);
                      transition: all 0.3s ease;">
                Verify Email Address →
            </a>
        </div>
        
        <!-- Features Preview -->
        <div style="margin: 32px 0; padding: 24px; background: rgba(99, 102, 241, 0.1); border-radius: 16px; border: 1px solid rgba(99, 102, 241, 0.2);">
            <h3 style="color: #e2e8f0; margin: 0 0 16px 0; font-size: 16px; font-weight: 600;">🚀 What awaits you:</h3>
            <div style="display: flex; flex-wrap: wrap; gap: 12px;">
                <span style="background: rgba(16, 185, 129, 0.2); color: #34d399; padding: 8px 16px; border-radius: 20px; font-size: 13px;">🔍 Advanced SAST Scanning</span>
                <span style="background: rgba(59, 130, 246, 0.2); color: #60a5fa; padding: 8px 16px; border-radius: 20px; font-size: 13px;">🤖 AI-Powered Analysis</span>
                <span style="background: rgba(249, 115, 22, 0.2); color: #fb923c; padding: 8px 16px; border-radius: 20px; font-size: 13px;">🔐 Secret Detection</span>
                <span style="background: rgba(168, 85, 247, 0.2); color: #c084fc; padding: 8px 16px; border-radius: 20px; font-size: 13px;">📊 Compliance Reports</span>
            </div>
        </div>
        ''',
        footer_text="This verification link expires in 2 hours."
    )


def get_password_reset_template() -> str:
    """Password reset template"""
    return get_base_template(
        title="Password Reset",
        header_gradient=GRADIENTS["red"],
        header_icon="🔑",
        header_subtitle="Reset Your Password",
        content='''
        <h2 style="color: #f1f5f9; font-size: 24px; margin: 0 0 16px 0; font-weight: 600;">
            Password Reset Request
        </h2>
        
        <p style="color: #94a3b8; font-size: 16px; line-height: 1.7; margin: 0 0 24px 0;">
            We received a request to reset your password. If you made this request, click the button below to create a new password.
        </p>
        
        <!-- CTA Button -->
        <div style="text-align: center; margin: 32px 0;">
            <a href="{{ reset_url }}" 
               style="background: linear-gradient(135deg, #ef4444 0%, #f97316 100%); 
                      color: #ffffff; 
                      padding: 16px 40px; 
                      text-decoration: none; 
                      border-radius: 12px; 
                      display: inline-block;
                      font-weight: 600;
                      font-size: 16px;
                      box-shadow: 0 10px 30px -5px rgba(239, 68, 68, 0.5);">
                Reset Password →
            </a>
        </div>
        
        <!-- Security Warning -->
        <div style="margin: 32px 0; padding: 20px; background: rgba(239, 68, 68, 0.1); border-radius: 16px; border: 1px solid rgba(239, 68, 68, 0.3);">
            <div style="display: flex; align-items: flex-start; gap: 12px;">
                <span style="font-size: 24px;">⚠️</span>
                <div>
                    <h4 style="color: #fca5a5; margin: 0 0 8px 0; font-size: 15px; font-weight: 600;">Security Notice</h4>
                    <p style="color: #f87171; margin: 0; font-size: 14px; line-height: 1.6;">
                        If you didn't request this password reset, please ignore this email. Your account remains secure and your password will not be changed.
                    </p>
                </div>
            </div>
        </div>
        ''',
        footer_text="This reset link expires in 1 hour for security reasons."
    )


def get_welcome_template() -> str:
    """Welcome email template"""
    return get_base_template(
        title="Welcome to SecureDevOps",
        header_gradient=GRADIENTS["green"],
        header_icon="🎉",
        header_subtitle="Your Security Journey Begins",
        content='''
        <h2 style="color: #f1f5f9; font-size: 24px; margin: 0 0 16px 0; font-weight: 600;">
            Welcome aboard, {{ user_name }}! 🚀
        </h2>
        
        <p style="color: #94a3b8; font-size: 16px; line-height: 1.7; margin: 0 0 24px 0;">
            Your account is now active and ready to secure your codebase. Let's explore what you can accomplish with SecureDevOps Platform.
        </p>
        
        <!-- Get Started Button -->
        <div style="text-align: center; margin: 32px 0;">
            <a href="{{ dashboard_url }}" 
               style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); 
                      color: #ffffff; 
                      padding: 16px 40px; 
                      text-decoration: none; 
                      border-radius: 12px; 
                      display: inline-block;
                      font-weight: 600;
                      font-size: 16px;
                      box-shadow: 0 10px 30px -5px rgba(16, 185, 129, 0.5);">
                Go to Dashboard →
            </a>
        </div>
        
        <!-- Feature Cards -->
        <div style="margin: 32px 0;">
            <h3 style="color: #e2e8f0; margin: 0 0 20px 0; font-size: 18px; font-weight: 600; text-align: center;">
                🛡️ Your Security Toolkit
            </h3>
            
            <div style="background: rgba(16, 185, 129, 0.1); padding: 20px; border-radius: 16px; margin-bottom: 12px; border: 1px solid rgba(16, 185, 129, 0.2);">
                <div style="display: flex; align-items: center; gap: 16px;">
                    <div style="background: rgba(16, 185, 129, 0.2); padding: 12px; border-radius: 12px;">
                        <span style="font-size: 24px;">🔍</span>
                    </div>
                    <div>
                        <h4 style="color: #34d399; margin: 0 0 4px 0; font-size: 16px; font-weight: 600;">Security Scanning</h4>
                        <p style="color: #6ee7b7; margin: 0; font-size: 14px;">SAST, secrets detection, dependency analysis, and container scanning</p>
                    </div>
                </div>
            </div>
            
            <div style="background: rgba(59, 130, 246, 0.1); padding: 20px; border-radius: 16px; margin-bottom: 12px; border: 1px solid rgba(59, 130, 246, 0.2);">
                <div style="display: flex; align-items: center; gap: 16px;">
                    <div style="background: rgba(59, 130, 246, 0.2); padding: 12px; border-radius: 12px;">
                        <span style="font-size: 24px;">🤖</span>
                    </div>
                    <div>
                        <h4 style="color: #60a5fa; margin: 0 0 4px 0; font-size: 16px; font-weight: 600;">AI-Powered Analysis</h4>
                        <p style="color: #93c5fd; margin: 0; font-size: 14px;">Intelligent vulnerability assessment with actionable remediation</p>
                    </div>
                </div>
            </div>
            
            <div style="background: rgba(168, 85, 247, 0.1); padding: 20px; border-radius: 16px; border: 1px solid rgba(168, 85, 247, 0.2);">
                <div style="display: flex; align-items: center; gap: 16px;">
                    <div style="background: rgba(168, 85, 247, 0.2); padding: 12px; border-radius: 12px;">
                        <span style="font-size: 24px;">📊</span>
                    </div>
                    <div>
                        <h4 style="color: #c084fc; margin: 0 0 4px 0; font-size: 16px; font-weight: 600;">Compliance & Reports</h4>
                        <p style="color: #d8b4fe; margin: 0; font-size: 14px;">OWASP, PCI DSS, SOC 2, and custom compliance frameworks</p>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Quick Start -->
        <div style="margin: 32px 0; padding: 24px; background: rgba(255,255,255,0.05); border-radius: 16px; border: 1px solid rgba(255,255,255,0.1);">
            <h3 style="color: #e2e8f0; margin: 0 0 16px 0; font-size: 16px; font-weight: 600;">🎯 Quick Start Guide</h3>
            <ol style="color: #94a3b8; margin: 0; padding-left: 20px; line-height: 2;">
                <li><strong style="color: #e2e8f0;">Add a project</strong> - Connect your repository or upload code</li>
                <li><strong style="color: #e2e8f0;">Run your first scan</strong> - Choose scanners and analyze</li>
                <li><strong style="color: #e2e8f0;">Review findings</strong> - Get AI-powered insights</li>
                <li><strong style="color: #e2e8f0;">Set up alerts</strong> - Stay informed in real-time</li>
            </ol>
        </div>
        '''
    )


def get_login_alert_template() -> str:
    """Login alert template"""
    return get_base_template(
        title="New Login Detected",
        header_gradient=GRADIENTS["cyan"],
        header_icon="🔐",
        header_subtitle="New Login to Your Account",
        content='''
        <h2 style="color: #f1f5f9; font-size: 24px; margin: 0 0 16px 0; font-weight: 600;">
            New Login Detected
        </h2>
        
        <p style="color: #94a3b8; font-size: 16px; line-height: 1.7; margin: 0 0 24px 0;">
            We noticed a new login to your SecureDevOps account. If this was you, no action is needed.
        </p>
        
        <!-- Login Details -->
        <div style="margin: 24px 0; padding: 24px; background: rgba(6, 182, 212, 0.1); border-radius: 16px; border: 1px solid rgba(6, 182, 212, 0.2);">
            <h3 style="color: #67e8f9; margin: 0 0 16px 0; font-size: 15px; font-weight: 600;">📋 Login Details</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="color: #64748b; padding: 10px 0; font-size: 14px;">Time</td>
                    <td style="color: #e2e8f0; padding: 10px 0; font-size: 14px; text-align: right;">{{ login_time }}</td>
                </tr>
                <tr>
                    <td style="color: #64748b; padding: 10px 0; font-size: 14px;">Location</td>
                    <td style="color: #e2e8f0; padding: 10px 0; font-size: 14px; text-align: right;">{{ location }}</td>
                </tr>
                <tr>
                    <td style="color: #64748b; padding: 10px 0; font-size: 14px;">Device</td>
                    <td style="color: #e2e8f0; padding: 10px 0; font-size: 14px; text-align: right;">{{ device }}</td>
                </tr>
                <tr>
                    <td style="color: #64748b; padding: 10px 0; font-size: 14px;">Browser</td>
                    <td style="color: #e2e8f0; padding: 10px 0; font-size: 14px; text-align: right;">{{ browser }}</td>
                </tr>
                <tr>
                    <td style="color: #64748b; padding: 10px 0; font-size: 14px;">IP Address</td>
                    <td style="color: #e2e8f0; padding: 10px 0; font-size: 14px; text-align: right; font-family: monospace;">{{ ip_address }}</td>
                </tr>
            </table>
        </div>
        
        <!-- Security Warning -->
        <div style="margin: 24px 0; padding: 20px; background: rgba(239, 68, 68, 0.1); border-radius: 16px; border: 1px solid rgba(239, 68, 68, 0.3);">
            <div style="display: flex; align-items: flex-start; gap: 12px;">
                <span style="font-size: 24px;">⚠️</span>
                <div>
                    <h4 style="color: #fca5a5; margin: 0 0 8px 0; font-size: 15px; font-weight: 600;">Not you?</h4>
                    <p style="color: #f87171; margin: 0; font-size: 14px; line-height: 1.6;">
                        If you didn't log in, your account may be compromised. Please change your password immediately and enable two-factor authentication.
                    </p>
                </div>
            </div>
        </div>
        
        <!-- Action Buttons -->
        <div style="text-align: center; margin: 32px 0;">
            <a href="{{ secure_account_url }}" 
               style="background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); 
                      color: #ffffff; 
                      padding: 14px 28px; 
                      text-decoration: none; 
                      border-radius: 12px; 
                      display: inline-block;
                      font-weight: 600;
                      font-size: 14px;
                      margin-right: 12px;
                      box-shadow: 0 8px 20px -5px rgba(239, 68, 68, 0.4);">
                Secure Account
            </a>
            <a href="{{ review_sessions_url }}" 
               style="background: rgba(255,255,255,0.1); 
                      color: #e2e8f0; 
                      padding: 14px 28px; 
                      text-decoration: none; 
                      border-radius: 12px; 
                      display: inline-block;
                      font-weight: 600;
                      font-size: 14px;
                      border: 1px solid rgba(255,255,255,0.2);">
                Review Sessions
            </a>
        </div>
        ''',
        footer_text="This is an automated security notification."
    )


def get_2fa_enabled_template() -> str:
    """2FA enabled template"""
    return get_base_template(
        title="Two-Factor Authentication Enabled",
        header_gradient=GRADIENTS["green"],
        header_icon="🛡️",
        header_subtitle="2FA Successfully Activated",
        content='''
        <h2 style="color: #f1f5f9; font-size: 24px; margin: 0 0 16px 0; font-weight: 600;">
            Two-Factor Authentication Enabled ✅
        </h2>
        
        <p style="color: #94a3b8; font-size: 16px; line-height: 1.7; margin: 0 0 24px 0;">
            Great news! Two-factor authentication has been successfully enabled on your SecureDevOps account. Your account is now more secure.
        </p>
        
        <!-- Success Badge -->
        <div style="text-align: center; margin: 32px 0;">
            <div style="display: inline-block; background: rgba(16, 185, 129, 0.2); padding: 20px 40px; border-radius: 16px; border: 1px solid rgba(16, 185, 129, 0.3);">
                <span style="font-size: 48px;">🔐</span>
                <p style="color: #34d399; margin: 12px 0 0 0; font-size: 16px; font-weight: 600;">Your account is now protected</p>
            </div>
        </div>
        
        <!-- What's Changed -->
        <div style="margin: 32px 0; padding: 24px; background: rgba(16, 185, 129, 0.1); border-radius: 16px; border: 1px solid rgba(16, 185, 129, 0.2);">
            <h3 style="color: #34d399; margin: 0 0 16px 0; font-size: 16px; font-weight: 600;">📋 What's Changed</h3>
            <ul style="color: #6ee7b7; margin: 0; padding-left: 20px; line-height: 1.8;">
                <li>You'll need to enter a 6-digit code when logging in</li>
                <li>Codes are generated by your authenticator app</li>
                <li>Each code expires after 30 seconds</li>
                <li>Invalid codes are rejected for security</li>
            </ul>
        </div>
        
        <!-- Backup Codes Reminder -->
        <div style="margin: 24px 0; padding: 20px; background: rgba(234, 179, 8, 0.1); border-radius: 16px; border: 1px solid rgba(234, 179, 8, 0.3);">
            <div style="display: flex; align-items: flex-start; gap: 12px;">
                <span style="font-size: 24px;">⚠️</span>
                <div>
                    <h4 style="color: #fbbf24; margin: 0 0 8px 0; font-size: 15px; font-weight: 600;">Save Your Backup Codes</h4>
                    <p style="color: #fcd34d; margin: 0; font-size: 14px; line-height: 1.6;">
                        Make sure you've saved your backup codes in a secure location. You'll need them if you lose access to your authenticator app.
                    </p>
                </div>
            </div>
        </div>
        
        <!-- Security Notice -->
        <div style="margin: 24px 0; padding: 20px; background: rgba(239, 68, 68, 0.1); border-radius: 16px; border: 1px solid rgba(239, 68, 68, 0.2);">
            <div style="display: flex; align-items: flex-start; gap: 12px;">
                <span style="font-size: 24px;">🚨</span>
                <div>
                    <h4 style="color: #fca5a5; margin: 0 0 8px 0; font-size: 15px; font-weight: 600;">Wasn't You?</h4>
                    <p style="color: #f87171; margin: 0; font-size: 14px; line-height: 1.6;">
                        If you didn't enable 2FA, your account may be compromised. Please secure your account immediately and contact support.
                    </p>
                </div>
            </div>
        </div>
        
        <!-- Action Button -->
        <div style="text-align: center; margin: 32px 0;">
            <a href="{{ security_settings_url }}" 
               style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); 
                      color: #ffffff; 
                      padding: 14px 28px; 
                      text-decoration: none; 
                      border-radius: 12px; 
                      display: inline-block;
                      font-weight: 600;
                      font-size: 14px;
                      box-shadow: 0 8px 20px -5px rgba(16, 185, 129, 0.4);">
                View Security Settings
            </a>
        </div>
        ''',
        footer_text="This is an automated security notification."
    )


def get_2fa_disabled_template() -> str:
    """2FA disabled template"""
    return get_base_template(
        title="Two-Factor Authentication Disabled",
        header_gradient=GRADIENTS["orange"],
        header_icon="⚠️",
        header_subtitle="2FA Has Been Disabled",
        content='''
        <h2 style="color: #f1f5f9; font-size: 24px; margin: 0 0 16px 0; font-weight: 600;">
            Two-Factor Authentication Disabled
        </h2>
        
        <p style="color: #94a3b8; font-size: 16px; line-height: 1.7; margin: 0 0 24px 0;">
            Two-factor authentication has been disabled on your SecureDevOps account. Your account is now less secure.
        </p>
        
        <!-- Warning Badge -->
        <div style="text-align: center; margin: 32px 0;">
            <div style="display: inline-block; background: rgba(249, 115, 22, 0.2); padding: 20px 40px; border-radius: 16px; border: 1px solid rgba(249, 115, 22, 0.3);">
                <span style="font-size: 48px;">🔓</span>
                <p style="color: #fb923c; margin: 12px 0 0 0; font-size: 16px; font-weight: 600;">2FA Protection Removed</p>
            </div>
        </div>
        
        <!-- What This Means -->
        <div style="margin: 32px 0; padding: 24px; background: rgba(249, 115, 22, 0.1); border-radius: 16px; border: 1px solid rgba(249, 115, 22, 0.2);">
            <h3 style="color: #fb923c; margin: 0 0 16px 0; font-size: 16px; font-weight: 600;">📋 What This Means</h3>
            <ul style="color: #fdba74; margin: 0; padding-left: 20px; line-height: 1.8;">
                <li>Your account is now protected only by your password</li>
                <li>No verification code will be required to log in</li>
                <li>Your account is more vulnerable to unauthorized access</li>
            </ul>
        </div>
        
        <!-- Re-enable Recommendation -->
        <div style="margin: 24px 0; padding: 20px; background: rgba(16, 185, 129, 0.1); border-radius: 16px; border: 1px solid rgba(16, 185, 129, 0.2);">
            <div style="display: flex; align-items: flex-start; gap: 12px;">
                <span style="font-size: 24px;">💡</span>
                <div>
                    <h4 style="color: #34d399; margin: 0 0 8px 0; font-size: 15px; font-weight: 600;">Recommendation</h4>
                    <p style="color: #6ee7b7; margin: 0; font-size: 14px; line-height: 1.6;">
                        We strongly recommend re-enabling 2FA to protect your account. Two-factor authentication adds an essential layer of security.
                    </p>
                </div>
            </div>
        </div>
        
        <!-- Security Alert -->
        <div style="margin: 24px 0; padding: 20px; background: rgba(239, 68, 68, 0.15); border-radius: 16px; border: 1px solid rgba(239, 68, 68, 0.3);">
            <div style="display: flex; align-items: flex-start; gap: 12px;">
                <span style="font-size: 24px;">🚨</span>
                <div>
                    <h4 style="color: #fca5a5; margin: 0 0 8px 0; font-size: 15px; font-weight: 600;">Wasn't You?</h4>
                    <p style="color: #f87171; margin: 0; font-size: 14px; line-height: 1.6;">
                        If you didn't disable 2FA, your account has been compromised. Change your password immediately and contact support.
                    </p>
                </div>
            </div>
        </div>
        
        <!-- Action Buttons -->
        <div style="text-align: center; margin: 32px 0;">
            <a href="{{ enable_2fa_url }}" 
               style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); 
                      color: #ffffff; 
                      padding: 14px 28px; 
                      text-decoration: none; 
                      border-radius: 12px; 
                      display: inline-block;
                      font-weight: 600;
                      font-size: 14px;
                      margin-right: 12px;
                      box-shadow: 0 8px 20px -5px rgba(16, 185, 129, 0.4);">
                Re-enable 2FA
            </a>
            <a href="{{ secure_account_url }}" 
               style="background: rgba(255,255,255,0.1); 
                      color: #e2e8f0; 
                      padding: 14px 28px; 
                      text-decoration: none; 
                      border-radius: 12px; 
                      display: inline-block;
                      font-weight: 600;
                      font-size: 14px;
                      border: 1px solid rgba(255,255,255,0.2);">
                Secure Account
            </a>
        </div>
        ''',
        footer_text="This is an automated security notification."
    )


def get_2fa_recovery_used_template() -> str:
    """2FA recovery code used template"""
    return get_base_template(
        title="Recovery Code Used",
        header_gradient=GRADIENTS["amber"],
        header_icon="🔑",
        header_subtitle="A Recovery Code Was Used",
        content='''
        <h2 style="color: #f1f5f9; font-size: 24px; margin: 0 0 16px 0; font-weight: 600;">
            Recovery Code Used for Login
        </h2>
        
        <p style="color: #94a3b8; font-size: 16px; line-height: 1.7; margin: 0 0 24px 0;">
            A recovery code was used to log into your SecureDevOps account. This may have been you, or someone with access to your backup codes.
        </p>
        
        <!-- Warning Badge -->
        <div style="text-align: center; margin: 32px 0;">
            <div style="display: inline-block; background: rgba(245, 158, 11, 0.2); padding: 20px 40px; border-radius: 16px; border: 1px solid rgba(245, 158, 11, 0.3);">
                <span style="font-size: 48px;">🔐</span>
                <p style="color: #fbbf24; margin: 12px 0 0 0; font-size: 16px; font-weight: 600;">Recovery Code Consumed</p>
            </div>
        </div>
        
        <!-- Usage Details -->
        <div style="margin: 32px 0; padding: 24px; background: rgba(245, 158, 11, 0.1); border-radius: 16px; border: 1px solid rgba(245, 158, 11, 0.2);">
            <h3 style="color: #fbbf24; margin: 0 0 16px 0; font-size: 16px; font-weight: 600;">📋 Usage Details</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="color: #64748b; padding: 10px 0; font-size: 14px;">Used At</td>
                    <td style="color: #e2e8f0; padding: 10px 0; font-size: 14px; text-align: right;">{{ used_at }}</td>
                </tr>
                <tr>
                    <td style="color: #64748b; padding: 10px 0; font-size: 14px;">IP Address</td>
                    <td style="color: #e2e8f0; padding: 10px 0; font-size: 14px; text-align: right; font-family: monospace;">{{ ip_address }}</td>
                </tr>
                <tr>
                    <td style="color: #64748b; padding: 10px 0; font-size: 14px;">Remaining Codes</td>
                    <td style="color: {{ '#fbbf24' if remaining_codes > 3 else '#ef4444' }}; padding: 10px 0; font-size: 14px; text-align: right; font-weight: 600;">{{ remaining_codes }} codes left</td>
                </tr>
            </table>
        </div>
        
        <!-- Important Notice -->
        <div style="margin: 24px 0; padding: 20px; background: rgba(234, 179, 8, 0.1); border-radius: 16px; border: 1px solid rgba(234, 179, 8, 0.3);">
            <div style="display: flex; align-items: flex-start; gap: 12px;">
                <span style="font-size: 24px;">⚠️</span>
                <div>
                    <h4 style="color: #fbbf24; margin: 0 0 8px 0; font-size: 15px; font-weight: 600;">Generate New Codes</h4>
                    <p style="color: #fcd34d; margin: 0; font-size: 14px; line-height: 1.6;">
                        Each recovery code can only be used once. Consider generating new backup codes to ensure you always have access to your account.
                    </p>
                </div>
            </div>
        </div>
        
        <!-- Security Alert -->
        <div style="margin: 24px 0; padding: 20px; background: rgba(239, 68, 68, 0.15); border-radius: 16px; border: 1px solid rgba(239, 68, 68, 0.3);">
            <div style="display: flex; align-items: flex-start; gap: 12px;">
                <span style="font-size: 24px;">🚨</span>
                <div>
                    <h4 style="color: #fca5a5; margin: 0 0 8px 0; font-size: 15px; font-weight: 600;">Wasn't You?</h4>
                    <p style="color: #f87171; margin: 0; font-size: 14px; line-height: 1.6;">
                        If you didn't use a recovery code, someone may have access to your backup codes. Secure your account immediately and regenerate your codes.
                    </p>
                </div>
            </div>
        </div>
        
        <!-- Action Button -->
        <div style="text-align: center; margin: 32px 0;">
            <a href="{{ security_url }}" 
               style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); 
                      color: #ffffff; 
                      padding: 14px 28px; 
                      text-decoration: none; 
                      border-radius: 12px; 
                      display: inline-block;
                      font-weight: 600;
                      font-size: 14px;
                      box-shadow: 0 8px 20px -5px rgba(245, 158, 11, 0.4);">
                Manage Recovery Codes
            </a>
        </div>
        ''',
        footer_text="This is an automated security notification."
    )


def get_password_changed_template() -> str:
    """Password changed notification template"""
    return get_base_template(
        title="Password Changed",
        header_gradient=GRADIENTS["purple"],
        header_icon="🔑",
        header_subtitle="Your Password Has Been Changed",
        content='''
        <h2 style="color: #f1f5f9; font-size: 24px; margin: 0 0 16px 0; font-weight: 600;">
            Password Successfully Changed
        </h2>
        
        <p style="color: #94a3b8; font-size: 16px; line-height: 1.7; margin: 0 0 24px 0;">
            Your SecureDevOps account password was changed on {{ changed_at }}. If you made this change, no further action is needed.
        </p>
        
        <!-- Success Badge -->
        <div style="text-align: center; margin: 32px 0;">
            <div style="display: inline-block; background: rgba(99, 102, 241, 0.2); padding: 20px 40px; border-radius: 16px; border: 1px solid rgba(99, 102, 241, 0.3);">
                <span style="font-size: 48px;">✅</span>
                <p style="color: #a5b4fc; margin: 12px 0 0 0; font-size: 16px; font-weight: 600;">Password Updated</p>
            </div>
        </div>
        
        <!-- Change Details -->
        <div style="margin: 32px 0; padding: 24px; background: rgba(99, 102, 241, 0.1); border-radius: 16px; border: 1px solid rgba(99, 102, 241, 0.2);">
            <h3 style="color: #a5b4fc; margin: 0 0 16px 0; font-size: 16px; font-weight: 600;">📋 Change Details</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="color: #64748b; padding: 10px 0; font-size: 14px;">Changed At</td>
                    <td style="color: #e2e8f0; padding: 10px 0; font-size: 14px; text-align: right;">{{ changed_at }}</td>
                </tr>
                <tr>
                    <td style="color: #64748b; padding: 10px 0; font-size: 14px;">IP Address</td>
                    <td style="color: #e2e8f0; padding: 10px 0; font-size: 14px; text-align: right; font-family: monospace;">{{ ip_address }}</td>
                </tr>
                <tr>
                    <td style="color: #64748b; padding: 10px 0; font-size: 14px;">Device</td>
                    <td style="color: #e2e8f0; padding: 10px 0; font-size: 14px; text-align: right;">{{ device }}</td>
                </tr>
            </table>
        </div>
        
        <!-- Security Alert -->
        <div style="margin: 24px 0; padding: 20px; background: rgba(239, 68, 68, 0.15); border-radius: 16px; border: 1px solid rgba(239, 68, 68, 0.3);">
            <div style="display: flex; align-items: flex-start; gap: 12px;">
                <span style="font-size: 24px;">🚨</span>
                <div>
                    <h4 style="color: #fca5a5; margin: 0 0 8px 0; font-size: 15px; font-weight: 600;">Didn't Change Your Password?</h4>
                    <p style="color: #f87171; margin: 0; font-size: 14px; line-height: 1.6;">
                        If you didn't make this change, your account may be compromised. Click the button below to secure your account immediately.
                    </p>
                </div>
            </div>
        </div>
        
        <!-- Action Button -->
        <div style="text-align: center; margin: 32px 0;">
            <a href="{{ secure_account_url }}" 
               style="background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); 
                      color: #ffffff; 
                      padding: 14px 28px; 
                      text-decoration: none; 
                      border-radius: 12px; 
                      display: inline-block;
                      font-weight: 600;
                      font-size: 14px;
                      box-shadow: 0 8px 20px -5px rgba(239, 68, 68, 0.4);">
                Secure My Account
            </a>
        </div>
        ''',
        footer_text="This is an automated security notification."
    )
