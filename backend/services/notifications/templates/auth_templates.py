"""
Authentication Email Templates
Handles verification, password reset, login alerts, and 2FA notifications
All templates follow ONYX design language with consistent card, button, and typography patterns
"""

from .base_template import GRADIENTS, get_base_template


def _btn(gradient: str, url_var: str, label: str, width: str = "auto") -> str:
    return f'''
    <div style="text-align: center; margin: 32px 0;">
        <!--[if mso]>
        <v:roundrect xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="urn:schemas-microsoft-com:office:word" href="{{%s}}" style="height:48px;v-text-anchor:middle;width:%s;" arcsize="12" strokecolor="transparent" fillcolor="#7c3aed">
            <w:anchorlock/>
            <center style="color:#ffffff;font-family:Arial,sans-serif;font-size:15px;font-weight:600;">{label}</center>
        </v:roundrect>
        <![endif]-->
        <!--[if !mso]><!-- -->
        <a href="{{{{ {url_var} }}}}"
           style="background: {gradient};
                  color: #ffffff;
                  padding: 14px 36px;
                  text-decoration: none;
                  border-radius: 12px;
                  display: inline-block;
                  font-weight: 600;
                  font-size: 15px;
                  letter-spacing: 0.3px;
                  box-shadow: 0 8px 24px -4px rgba(99, 102, 241, 0.3);
                  mso-hide: all;">
            {label} &rarr;
        </a>
        <!--<![endif]-->
    </div>'''


def _card(content: str, border_left: str = None) -> str:
    border = f'border-left: 4px solid {border_left};' if border_left else ''
    return f'''
    <div style="margin: 24px 0; padding: 20px 24px; background: rgba(255,255,255,0.03); border-radius: 12px; border: 1px solid rgba(255,255,255,0.08); {border}">
        {content}
    </div>'''


def _info_row(label: str, value_var: str) -> str:
    return f'''
    <tr>
        <td style="color: #64748b; padding: 8px 0; font-size: 13px; border-bottom: 1px solid rgba(255,255,255,0.04);">{label}</td>
        <td style="color: #e2e8f0; padding: 8px 0; font-size: 13px; text-align: right;">{{{{ {value_var} }}}}</td>
    </tr>'''


def get_verification_template():
    return get_base_template(
        title="Verify Your Email — ONYX",
        header_gradient=GRADIENTS["onyx"],
        header_icon="✉️",
        header_subtitle="Verify your email address to activate your account",
        content=f'''
        <h2 style="color: #f1f5f9; font-size: 22px; margin: 0 0 8px; font-weight: 700; line-height: 1.3;">
            Welcome to ONYX
        </h2>
        <p style="color: #64748b; font-size: 14px; margin: 0 0 24px; line-height: 1.6;">
            You're almost there! Click the button below to verify your email address and unlock the full power of ONYX Security Intelligence Platform.
        </p>

        {_btn("linear-gradient(135deg, #06b6d4 0%, #7c3aed 100%)", "verification_url", "Verify Email Address", "220px")}

        {_card('''
            <h3 style="color: #94a3b8; margin: 0 0 12px; font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;">What you'll get</h3>
            <table role="presentation" cellpadding="0" cellspacing="0" border="0">
                <tr>
                    <td style="padding: 4px 8px 4px 0; color: #34d399; font-size: 14px; vertical-align: middle;">&#10003;</td>
                    <td style="color: #94a3b8; font-size: 13px; padding: 4px 0;">Advanced SAST &amp; secret scanning</td>
                </tr>
                <tr>
                    <td style="padding: 4px 8px 4px 0; color: #34d399; font-size: 14px; vertical-align: middle;">&#10003;</td>
                    <td style="color: #94a3b8; font-size: 13px; padding: 4px 0;">AI-powered vulnerability analysis</td>
                </tr>
                <tr>
                    <td style="padding: 4px 8px 4px 0; color: #34d399; font-size: 14px; vertical-align: middle;">&#10003;</td>
                    <td style="color: #94a3b8; font-size: 13px; padding: 4px 0;">Compliance reports &amp; remediation</td>
                </tr>
            </table>
        ''', border_left="#06b6d4")}
        ''',
        footer_text="This verification link expires in 2 hours. If you didn't create an account, ignore this email."
    )


def get_password_reset_template():
    return get_base_template(
        title="Reset Your Password — ONYX",
        header_gradient=GRADIENTS["red"],
        header_icon="🔑",
        header_subtitle="Reset your password to regain access",
        content=f'''
        <h2 style="color: #f1f5f9; font-size: 22px; margin: 0 0 8px; font-weight: 700; line-height: 1.3;">
            Password Reset Request
        </h2>
        <p style="color: #64748b; font-size: 14px; margin: 0 0 24px; line-height: 1.6;">
            We received a request to reset the password for your ONYX account. If you made this request, click the button below to create a new password.
        </p>

        {_btn("linear-gradient(135deg, #ef4444 0%, #f97316 100%)", "reset_url", "Reset Password", "200px")}

        {_card('''
            <div style="display: flex; align-items: flex-start; gap: 12px;">
                <span style="font-size: 20px; line-height: 1; flex-shrink: 0;">&#9888;</span>
                <div>
                    <h4 style="color: #fca5a5; margin: 0 0 6px; font-size: 14px; font-weight: 600;">Security Notice</h4>
                    <p style="color: #f87171; margin: 0; font-size: 13px; line-height: 1.5;">
                        If you didn't request this password reset, please ignore this email. Your password will not be changed and your account remains secure.
                    </p>
                </div>
            </div>
        ''', border_left="#ef4444")}
        ''',
        footer_text="This reset link expires in 1 hour. Never share this link with anyone."
    )


def get_welcome_template():
    return get_base_template(
        title="Welcome to ONYX — Let's Get Started",
        header_gradient=GRADIENTS["green"],
        header_icon="🎉",
        header_subtitle="Your account is active — let's secure your codebase",
        content=f'''
        <h2 style="color: #f1f5f9; font-size: 22px; margin: 0 0 8px; font-weight: 700; line-height: 1.3;">
            Welcome aboard, {{{{ user_name }}}}!
        </h2>
        <p style="color: #64748b; font-size: 14px; margin: 0 0 24px; line-height: 1.6;">
            Your ONYX account is ready. Here's your quick-start guide to securing your codebase.
        </p>

        {_btn("linear-gradient(135deg, #10b981 0%, #059669 100%)", "dashboard_url", "Go to Dashboard", "200px")}

        <table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin: 28px 0; width: 100%;">
            <tr>
                <td style="padding: 0 0 12px;">
                    <div style="background: rgba(16, 185, 129, 0.08); padding: 16px 20px; border-radius: 12px; border: 1px solid rgba(16, 185, 129, 0.15);">
                        <div style="display: flex; align-items: center; gap: 14px;">
                            <div style="background: rgba(16, 185, 129, 0.15); width: 36px; height: 36px; border-radius: 10px; text-align: center; line-height: 36px; flex-shrink: 0;">&#128269;</div>
                            <div>
                                <h4 style="color: #34d399; margin: 0 0 2px; font-size: 14px; font-weight: 600;">Add a project</h4>
                                <p style="color: #6ee7b7; margin: 0; font-size: 12px;">Connect your repository or upload code</p>
                            </div>
                        </div>
                    </div>
                </td>
            </tr>
            <tr>
                <td style="padding: 0 0 12px;">
                    <div style="background: rgba(59, 130, 246, 0.08); padding: 16px 20px; border-radius: 12px; border: 1px solid rgba(59, 130, 246, 0.15);">
                        <div style="display: flex; align-items: center; gap: 14px;">
                            <div style="background: rgba(59, 130, 246, 0.15); width: 36px; height: 36px; border-radius: 10px; text-align: center; line-height: 36px; flex-shrink: 0;">&#128269;</div>
                            <div>
                                <h4 style="color: #60a5fa; margin: 0 0 2px; font-size: 14px; font-weight: 600;">Run your first scan</h4>
                                <p style="color: #93c5fd; margin: 0; font-size: 12px;">Choose scanners and analyze your code</p>
                            </div>
                        </div>
                    </div>
                </td>
            </tr>
            <tr>
                <td style="padding: 0 0 12px;">
                    <div style="background: rgba(168, 85, 247, 0.08); padding: 16px 20px; border-radius: 12px; border: 1px solid rgba(168, 85, 247, 0.15);">
                        <div style="display: flex; align-items: center; gap: 14px;">
                            <div style="background: rgba(168, 85, 247, 0.15); width: 36px; height: 36px; border-radius: 10px; text-align: center; line-height: 36px; flex-shrink: 0;">&#128200;</div>
                            <div>
                                <h4 style="color: #c084fc; margin: 0 0 2px; font-size: 14px; font-weight: 600;">Review findings</h4>
                                <p style="color: #d8b4fe; margin: 0; font-size: 12px;">AI-powered insights with remediation steps</p>
                            </div>
                        </div>
                    </div>
                </td>
            </tr>
        </table>

        {_card('''
            <p style="color: #94a3b8; margin: 0; font-size: 13px; line-height: 1.5;">
                <strong style="color: #e2e8f0;">Pro tip:</strong> Set up notifications in your profile settings to stay informed about scan results and security alerts in real-time.
            </p>
        ''')}
        '''
    )


def get_login_alert_template():
    return get_base_template(
        title="New Login Detected — ONYX",
        header_gradient=GRADIENTS["cyan"],
        header_icon="🔐",
        header_subtitle="New sign-in to your ONYX account",
        content=f'''
        <h2 style="color: #f1f5f9; font-size: 22px; margin: 0 0 8px; font-weight: 700; line-height: 1.3;">
            New Login Detected
        </h2>
        <p style="color: #64748b; font-size: 14px; margin: 0 0 24px; line-height: 1.6;">
            We noticed a new sign-in to your ONYX account. If this was you, no further action is needed.
        </p>

        {_card(f'''
            <h3 style="color: #67e8f9; margin: 0 0 12px; font-size: 14px; font-weight: 600;">Login Details</h3>
            <table style="width: 100%; border-collapse: collapse;">
                {_info_row("Time", "login_time")}
                {_info_row("Location", "location")}
                {_info_row("Device", "device")}
                {_info_row("Browser", "browser")}
                {_info_row("IP Address", "ip_address")}
            </table>
        ''', border_left="#06b6d4")}

        {_card('''
            <div style="display: flex; align-items: flex-start; gap: 12px;">
                <span style="font-size: 20px; line-height: 1; flex-shrink: 0;">&#9888;</span>
                <div>
                    <h4 style="color: #fca5a5; margin: 0 0 6px; font-size: 14px; font-weight: 600;">Wasn't you?</h4>
                    <p style="color: #f87171; margin: 0; font-size: 13px; line-height: 1.5;">
                        Secure your account immediately — change your password and enable two-factor authentication.
                    </p>
                </div>
            </div>
        ''', border_left="#ef4444")}

        <table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin: 0 auto;">
            <tr>
                <td style="padding: 0 6px 0 0;">
                    <a href="{{{{ secure_account_url }}}}"
                       style="background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
                              color: #ffffff;
                              padding: 12px 24px;
                              text-decoration: none;
                              border-radius: 10px;
                              display: inline-block;
                              font-weight: 600;
                              font-size: 13px;
                              white-space: nowrap;
                              box-shadow: 0 6px 16px -4px rgba(239, 68, 68, 0.3);">
                        Secure Account
                    </a>
                </td>
                <td style="padding: 0 0 0 6px;">
                    <a href="{{{{ review_sessions_url }}}}"
                       style="background: rgba(255,255,255,0.06);
                              color: #e2e8f0;
                              padding: 12px 24px;
                              text-decoration: none;
                              border-radius: 10px;
                              display: inline-block;
                              font-weight: 600;
                              font-size: 13px;
                              white-space: nowrap;
                              border: 1px solid rgba(255,255,255,0.1);">
                        Review Sessions
                    </a>
                </td>
            </tr>
        </table>
        ''',
        footer_text="This is an automated security notification. If you recognize this activity, no action needed."
    )


def get_2fa_enabled_template():
    return get_base_template(
        title="Two-Factor Authentication Enabled — ONYX",
        header_gradient=GRADIENTS["green"],
        header_icon="🛡️",
        header_subtitle="Two-factor authentication is now active",
        content=f'''
        <h2 style="color: #f1f5f9; font-size: 22px; margin: 0 0 8px; font-weight: 700; line-height: 1.3;">
            2FA Successfully Enabled
        </h2>
        <p style="color: #64748b; font-size: 14px; margin: 0 0 24px; line-height: 1.6;">
            Great news! Two-factor authentication has been activated on your ONYX account. Your account is now significantly more secure.
        </p>

        <div style="text-align: center; margin: 28px 0;">
            <div style="display: inline-block; background: rgba(16, 185, 129, 0.1); padding: 20px 36px; border-radius: 14px; border: 1px solid rgba(16, 185, 129, 0.2);">
                <span style="font-size: 44px; line-height: 1;">&#128274;</span>
                <p style="color: #34d399; margin: 10px 0 0; font-size: 14px; font-weight: 600;">Extra protection activated</p>
            </div>
        </div>

        {_card('''
            <h3 style="color: #34d399; margin: 0 0 12px; font-size: 14px; font-weight: 600;">What changed</h3>
            <table role="presentation" cellpadding="0" cellspacing="0" border="0">
                <tr><td style="padding: 3px 0; color: #6ee7b7; font-size: 13px; vertical-align: middle;">&#8226; You'll need a 6-digit code when logging in</td></tr>
                <tr><td style="padding: 3px 0; color: #6ee7b7; font-size: 13px; vertical-align: middle;">&#8226; Codes are generated by your authenticator app</td></tr>
                <tr><td style="padding: 3px 0; color: #6ee7b7; font-size: 13px; vertical-align: middle;">&#8226; Each code expires after 30 seconds</td></tr>
            </table>
        ''', border_left="#10b981")}

        {_card('''
            <div style="display: flex; align-items: flex-start; gap: 12px;">
                <span style="font-size: 20px; line-height: 1; flex-shrink: 0;">&#9888;</span>
                <div>
                    <h4 style="color: #fbbf24; margin: 0 0 6px; font-size: 14px; font-weight: 600;">Save your backup codes</h4>
                    <p style="color: #fcd34d; margin: 0; font-size: 13px; line-height: 1.5;">
                        Store your recovery codes in a secure place. You'll need them if you lose access to your authenticator app.
                    </p>
                </div>
            </div>
        ''', border_left="#eab308")}

        {_btn("linear-gradient(135deg, #10b981 0%, #059669 100%)", "security_settings_url", "View Security Settings")}
        ''',
        footer_text="This is an automated security notification. If you did not enable 2FA, secure your account immediately."
    )


def get_2fa_disabled_template():
    return get_base_template(
        title="Two-Factor Authentication Disabled — ONYX",
        header_gradient=GRADIENTS["orange"],
        header_icon="⚠️",
        header_subtitle="Two-factor authentication has been turned off",
        content=f'''
        <h2 style="color: #f1f5f9; font-size: 22px; margin: 0 0 8px; font-weight: 700; line-height: 1.3;">
            2FA Protection Removed
        </h2>
        <p style="color: #64748b; font-size: 14px; margin: 0 0 24px; line-height: 1.6;">
            Two-factor authentication has been disabled on your ONYX account. Your account is now less secure.
        </p>

        <div style="text-align: center; margin: 28px 0;">
            <div style="display: inline-block; background: rgba(249, 115, 22, 0.1); padding: 20px 36px; border-radius: 14px; border: 1px solid rgba(249, 115, 22, 0.2);">
                <span style="font-size: 44px; line-height: 1;">&#128273;</span>
                <p style="color: #fb923c; margin: 10px 0 0; font-size: 14px; font-weight: 600;">2FA protection removed</p>
            </div>
        </div>

        {_card('''
            <h3 style="color: #fb923c; margin: 0 0 12px; font-size: 14px; font-weight: 600;">What this means</h3>
            <table role="presentation" cellpadding="0" cellspacing="0" border="0">
                <tr><td style="padding: 3px 0; color: #fdba74; font-size: 13px;">&#8226; Only your password protects your account</td></tr>
                <tr><td style="padding: 3px 0; color: #fdba74; font-size: 13px;">&#8226; No verification code required to log in</td></tr>
                <tr><td style="padding: 3px 0; color: #fdba74; font-size: 13px;">&#8226; Higher risk of unauthorized access</td></tr>
            </table>
        ''', border_left="#f97316")}

        {_card('''
            <div style="display: flex; align-items: flex-start; gap: 12px;">
                <span style="font-size: 20px; line-height: 1; flex-shrink: 0;">&#128161;</span>
                <div>
                    <h4 style="color: #34d399; margin: 0 0 6px; font-size: 14px; font-weight: 600;">Recommendation</h4>
                    <p style="color: #6ee7b7; margin: 0; font-size: 13px; line-height: 1.5;">
                        Re-enable 2FA to protect your account. It's the most effective way to prevent unauthorized access.
                    </p>
                </div>
            </div>
        ''', border_left="#10b981")}

        <table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin: 0 auto;">
            <tr>
                <td style="padding: 0 6px 0 0;">
                    <a href="{{{{ enable_2fa_url }}}}"
                       style="background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                              color: #ffffff;
                              padding: 12px 24px;
                              text-decoration: none;
                              border-radius: 10px;
                              display: inline-block;
                              font-weight: 600;
                              font-size: 13px;
                              white-space: nowrap;
                              box-shadow: 0 6px 16px -4px rgba(16, 185, 129, 0.3);">
                        Re-enable 2FA
                    </a>
                </td>
                <td style="padding: 0 0 0 6px;">
                    <a href="{{{{ secure_account_url }}}}"
                       style="background: rgba(255,255,255,0.06);
                              color: #e2e8f0;
                              padding: 12px 24px;
                              text-decoration: none;
                              border-radius: 10px;
                              display: inline-block;
                              font-weight: 600;
                              font-size: 13px;
                              white-space: nowrap;
                              border: 1px solid rgba(255,255,255,0.1);">
                        Secure Account
                    </a>
                </td>
            </tr>
        </table>
        ''',
        footer_text="This is an automated security notification. If you did not disable 2FA, your account may be compromised."
    )


def get_2fa_recovery_used_template():
    return get_base_template(
        title="Recovery Code Used — ONYX",
        header_gradient=GRADIENTS["amber"],
        header_icon="🔑",
        header_subtitle="A recovery code was used to access your account",
        content=f'''
        <h2 style="color: #f1f5f9; font-size: 22px; margin: 0 0 8px; font-weight: 700; line-height: 1.3;">
            Recovery Code Used
        </h2>
        <p style="color: #64748b; font-size: 14px; margin: 0 0 24px; line-height: 1.6;">
            A recovery code was used to log into your ONYX account. This may have been you or someone with access to your backup codes.
        </p>

        {_card(f'''
            <h3 style="color: #fbbf24; margin: 0 0 12px; font-size: 14px; font-weight: 600;">Usage Details</h3>
            <table style="width: 100%; border-collapse: collapse;">
                {_info_row("Used At", "used_at")}
                {_info_row("IP Address", "ip_address")}
                <tr>
                    <td style="color: #64748b; padding: 8px 0; font-size: 13px; border-bottom: 1px solid rgba(255,255,255,0.04);">Remaining Codes</td>
                    <td style="color: {{{{ '#fbbf24' if remaining_codes > 3 else '#ef4444' }}}}; padding: 8px 0; font-size: 13px; text-align: right; font-weight: 600;">{{{{ remaining_codes }}}} left</td>
                </tr>
            </table>
        ''', border_left="#eab308")}

        {_card('''
            <div style="display: flex; align-items: flex-start; gap: 12px;">
                <span style="font-size: 20px; line-height: 1; flex-shrink: 0;">&#9888;</span>
                <div>
                    <h4 style="color: #fbbf24; margin: 0 0 6px; font-size: 14px; font-weight: 600;">Generate new codes</h4>
                    <p style="color: #fcd34d; margin: 0; font-size: 13px; line-height: 1.5;">
                        Each recovery code can only be used once. Generate a fresh set of backup codes to ensure you always have access.
                    </p>
                </div>
            </div>
        ''', border_left="#eab308")}

        {_btn("linear-gradient(135deg, #f59e0b 0%, #d97706 100%)", "security_url", "Manage Recovery Codes")}
        ''',
        footer_text="This is an automated security notification. If you didn't use a recovery code, secure your account immediately."
    )


def get_password_changed_template():
    return get_base_template(
        title="Password Changed — ONYX",
        header_gradient=GRADIENTS["purple"],
        header_icon="🔑",
        header_subtitle="Your password has been updated",
        content=f'''
        <h2 style="color: #f1f5f9; font-size: 22px; margin: 0 0 8px; font-weight: 700; line-height: 1.3;">
            Password Successfully Changed
        </h2>
        <p style="color: #64748b; font-size: 14px; margin: 0 0 24px; line-height: 1.6;">
            Your ONYX account password was changed on {{{{ changed_at }}}}. If you made this change, no further action is needed.
        </p>

        <div style="text-align: center; margin: 28px 0;">
            <div style="display: inline-block; background: rgba(99, 102, 241, 0.1); padding: 20px 36px; border-radius: 14px; border: 1px solid rgba(99, 102, 241, 0.2);">
                <span style="font-size: 44px; line-height: 1;">&#10004;</span>
                <p style="color: #a5b4fc; margin: 10px 0 0; font-size: 14px; font-weight: 600;">Password updated</p>
            </div>
        </div>

        {_card(f'''
            <h3 style="color: #a5b4fc; margin: 0 0 12px; font-size: 14px; font-weight: 600;">Change Details</h3>
            <table style="width: 100%; border-collapse: collapse;">
                {_info_row("Changed At", "changed_at")}
                {_info_row("IP Address", "ip_address")}
                {_info_row("Device", "device")}
            </table>
        ''', border_left="#6366f1")}

        {_card('''
            <div style="display: flex; align-items: flex-start; gap: 12px;">
                <span style="font-size: 20px; line-height: 1; flex-shrink: 0;">&#128680;</span>
                <div>
                    <h4 style="color: #fca5a5; margin: 0 0 6px; font-size: 14px; font-weight: 600;">Didn't change your password?</h4>
                    <p style="color: #f87171; margin: 0; font-size: 13px; line-height: 1.5;">
                        Your account may be compromised. Click below to secure your account immediately.
                    </p>
                </div>
            </div>
        ''', border_left="#ef4444")}

        {_btn("linear-gradient(135deg, #ef4444 0%, #dc2626 100%)", "secure_account_url", "Secure My Account")}
        ''',
        footer_text="This is an automated security notification. If you didn't make this change, take action immediately."
    )
