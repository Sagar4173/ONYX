"""
Security Email Templates
Handles scan results, security alerts, vulnerability notifications, and weekly digests
All templates follow ONYX design language with consistent card, button, and typography patterns
"""

from .base_template import GRADIENTS, get_base_template


def _btn(gradient: str, url_var: str, label: str, width: str = "auto") -> str:
    return f'''
    <div style="text-align: center; margin: 32px 0;">
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
                  box-shadow: 0 8px 24px -4px rgba(99, 102, 241, 0.3);">
            {label} &rarr;
        </a>
    </div>'''


def _card(content: str, border_left: str = None) -> str:
    border = f'border-left: 4px solid {border_left};' if border_left else ''
    return f'''
    <div style="margin: 24px 0; padding: 20px 24px; background: rgba(255,255,255,0.03); border-radius: 12px; border: 1px solid rgba(255,255,255,0.08); {border}">
        {content}
    </div>'''


def _severity_grid(*items) -> str:
    cells = ""
    for sev, count_var, bg, border, text_color, label in items:
        cells += f'''
        <td class="badge-cell" style="padding: 6px; width: 25%;">
            <div style="background: {bg}; padding: 16px 8px; border-radius: 12px; text-align: center; border: 1px solid {border};">
                <div style="font-size: 28px; font-weight: 700; color: {text_color};">{{{{ {count_var} }}}}</div>
                <div style="font-size: 10px; color: {text_color}; text-transform: uppercase; letter-spacing: 1.5px; margin-top: 4px; font-weight: 600;">{label}</div>
            </div>
        </td>'''
    return f'''
    <table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin: 24px 0; width: 100%;">
        <tr>{cells}</tr>
    </table>'''


def _info_row(label: str, value_var: str) -> str:
    return f'''
    <tr>
        <td style="color: #64748b; padding: 8px 0; font-size: 13px; border-bottom: 1px solid rgba(255,255,255,0.04);">{label}</td>
        <td style="color: #e2e8f0; padding: 8px 0; font-size: 13px; text-align: right;">{{{{ {value_var} }}}}</td>
    </tr>'''


def get_scan_completed_template():
    return get_base_template(
        title="Scan Completed — ONYX",
        header_gradient=GRADIENTS["blue"],
        header_icon="✅",
        header_subtitle="Security scan completed — review your findings",
        content=f'''
        <h2 style="color: #f1f5f9; font-size: 22px; margin: 0 0 8px; font-weight: 700; line-height: 1.3;">
            Scan Complete: {{{{ project_name }}}}
        </h2>
        <p style="color: #64748b; font-size: 14px; margin: 0 0 24px; line-height: 1.6;">
            Your {{{{ scan_type }}}} scan has finished. Here's a summary of the findings.
        </p>

        {_severity_grid(
            ("critical", "critical_count", "rgba(239,68,68,0.12)", "rgba(239,68,68,0.25)", "#f87171", "Critical"),
            ("high", "high_count", "rgba(249,115,22,0.12)", "rgba(249,115,22,0.25)", "#fb923c", "High"),
            ("medium", "medium_count", "rgba(234,179,8,0.12)", "rgba(234,179,8,0.25)", "#fbbf24", "Medium"),
            ("low", "low_count", "rgba(34,197,94,0.12)", "rgba(34,197,94,0.25)", "#4ade80", "Low"),
        )}

        {_card(f'''
            <h3 style="color: #93c5fd; margin: 0 0 12px; font-size: 14px; font-weight: 600;">Scan Details</h3>
            <table style="width: 100%; border-collapse: collapse;">
                {_info_row("Scan Type", "scan_type")}
                {_info_row("Duration", "duration")}
                {_info_row("Files Scanned", "files_scanned")}
                {_info_row("Completed At", "completed_at")}
            </table>
        ''', border_left="#3b82f6")}

        {_btn("linear-gradient(135deg, #3b82f6 0%, #6366f1 100%)", "report_url", "View Full Report")}
        ''',
        footer_text="You received this because scan notifications are enabled for your project."
    )


def get_security_alert_template():
    return get_base_template(
        title="Security Alert — ONYX",
        header_gradient=GRADIENTS["dark_red"],
        header_icon="🚨",
        header_subtitle="Immediate attention required",
        content=f'''
        <div style="background: rgba(239,68,68,0.12); padding: 12px 16px; border-radius: 10px; margin-bottom: 20px; border: 1px solid rgba(239,68,68,0.25);">
            <p style="color: #fca5a5; margin: 0; font-size: 13px; font-weight: 500;">&#9888; Immediate attention required</p>
        </div>

        <h2 style="color: #f1f5f9; font-size: 22px; margin: 0 0 8px; font-weight: 700; line-height: 1.3;">
            {{{{ alert_title }}}}
        </h2>
        <p style="color: #64748b; font-size: 14px; margin: 0 0 24px; line-height: 1.6;">
            {{{{ alert_description }}}}
        </p>

        {_card(f'''
            <h3 style="color: #f87171; margin: 0 0 12px; font-size: 14px; font-weight: 600;">Alert Details</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="color: #64748b; padding: 8px 0; font-size: 13px; border-bottom: 1px solid rgba(255,255,255,0.04);">Severity</td>
                    <td style="padding: 8px 0; text-align: right;">
                        <span style="background: {{{{ severity_color }}}}; color: white; padding: 3px 12px; border-radius: 12px; font-size: 11px; font-weight: 600;">{{{{ severity }}}}</span>
                    </td>
                </tr>
                {_info_row("Project", "project_name")}
                {_info_row("File", "file_path")}
                {_info_row("Detected At", "detected_at")}
            </table>
        ''', border_left="#ef4444")}

        {_card('''
            <h3 style="color: #e2e8f0; margin: 0 0 8px; font-size: 14px; font-weight: 600;">&#128270; Vulnerability Details</h3>
            <table role="presentation" cellpadding="0" cellspacing="0" border="0">
                <tr><td style="color: #94a3b8; padding: 3px 0; font-size: 13px;"><span style="color: #64748b;">Type:</span> {{ vulnerability_type }}</td></tr>
                <tr><td style="color: #94a3b8; padding: 3px 0; font-size: 13px;"><span style="color: #64748b;">CWE:</span> {{ cwe_id }}</td></tr>
                <tr><td style="color: #94a3b8; padding: 3px 0; font-size: 13px;"><span style="color: #64748b;">CVSS:</span> {{ cvss_score }}</td></tr>
            </table>
        ''')}

        {_card('''
            <h3 style="color: #34d399; margin: 0 0 8px; font-size: 14px; font-weight: 600;">&#128161; Recommended Action</h3>
            <p style="color: #6ee7b7; margin: 0; font-size: 13px; line-height: 1.5;">{{ recommendation }}</p>
        ''', border_left="#10b981")}

        {_btn("linear-gradient(135deg, #dc2626 0%, #ef4444 100%)", "alert_url", "View & Remediate")}
        ''',
        footer_text="This is an automated security alert. Please review and act immediately."
    )


def get_new_vulnerability_template():
    return get_base_template(
        title="New Vulnerability Found — ONYX",
        header_gradient=GRADIENTS["orange"],
        header_icon="🔓",
        header_subtitle="A new vulnerability has been detected",
        content=f'''
        <h2 style="color: #f1f5f9; font-size: 22px; margin: 0 0 8px; font-weight: 700; line-height: 1.3;">
            {{{{ vulnerability_title }}}}
        </h2>
        <p style="color: #64748b; font-size: 14px; margin: 0 0 24px; line-height: 1.6;">
            A <strong style="color: {{{{ severity_color }}}};">{{{{ severity }}}}</strong> severity vulnerability was found in <strong style="color: #e2e8f0;">{{{{ project_name }}}}</strong>.
        </p>

        <div style="text-align: center; margin: 24px 0;">
            <span style="background: {{{{ severity_color }}}}; color: white; padding: 6px 24px; border-radius: 20px; font-size: 13px; font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px;">
                {{{{ severity }}}} SEVERITY
            </span>
        </div>

        {_card('''
            <h3 style="color: #fdba74; margin: 0 0 12px; font-size: 14px; font-weight: 600;">&#128205; Location</h3>
            <div style="background: rgba(0,0,0,0.3); padding: 14px; border-radius: 10px; font-family: 'Monaco', 'Menlo', 'Consolas', monospace;">
                <p style="color: #e2e8f0; margin: 0 0 6px; font-size: 13px;">
                    <span style="color: #64748b;">File:</span> {{ file_path }}
                </p>
                <p style="color: #e2e8f0; margin: 0; font-size: 13px;">
                    <span style="color: #64748b;">Line:</span> {{ line_number }}
                </p>
            </div>
        ''', border_left="#f97316")}

        {_card('''
            <h3 style="color: #e2e8f0; margin: 0 0 8px; font-size: 14px; font-weight: 600;">&#128221; Description</h3>
            <p style="color: #94a3b8; margin: 0; font-size: 13px; line-height: 1.5;">{{ description }}</p>
        ''')}

        {_card('''
            <h3 style="color: #34d399; margin: 0 0 8px; font-size: 14px; font-weight: 600;">&#128736; How to Fix</h3>
            <p style="color: #6ee7b7; margin: 0; font-size: 13px; line-height: 1.5;">{{ fix_suggestion }}</p>
        ''', border_left="#10b981")}

        {_btn("linear-gradient(135deg, #f97316 0%, #ea580c 100%)", "vulnerability_url", "View Details & Fix")}
        ''',
        footer_text="Act quickly on high and critical vulnerabilities to maintain your security posture."
    )


def get_weekly_digest_template():
    return get_base_template(
        title="Weekly Security Digest — ONYX",
        header_gradient=GRADIENTS["purple_blue"],
        header_icon="📊",
        header_subtitle="Your weekly security summary",
        content=f'''
        <h2 style="color: #f1f5f9; font-size: 22px; margin: 0 0 4px; font-weight: 700; line-height: 1.3;">
            Week of {{{{ week_start }}}} — {{{{ week_end }}}}
        </h2>
        <p style="color: #64748b; font-size: 14px; margin: 0 0 24px; line-height: 1.6;">
            Here's your security summary for the past week across all projects.
        </p>

        {_card('''
            <h3 style="color: #c4b5fd; margin: 0 0 16px; font-size: 14px; font-weight: 600;">&#128200; Overview</h3>
            <table role="presentation" cellpadding="0" cellspacing="0" border="0" style="width: 100%;">
                <tr>
                    <td style="text-align: center; padding: 8px; width: 33%;">
                        <div style="font-size: 32px; font-weight: 700; color: #a78bfa;">{{{{ total_scans }}}}</div>
                        <div style="font-size: 10px; color: #c4b5fd; text-transform: uppercase; letter-spacing: 1px; margin-top: 4px;">Scans Run</div>
                    </td>
                    <td style="text-align: center; padding: 8px; width: 33%; border-left: 1px solid rgba(139,92,246,0.2); border-right: 1px solid rgba(139,92,246,0.2);">
                        <div style="font-size: 32px; font-weight: 700; color: #f87171;">{{{{ total_vulnerabilities }}}}</div>
                        <div style="font-size: 10px; color: #fca5a5; text-transform: uppercase; letter-spacing: 1px; margin-top: 4px;">Vulnerabilities</div>
                    </td>
                    <td style="text-align: center; padding: 8px; width: 33%;">
                        <div style="font-size: 32px; font-weight: 700; color: #4ade80;">{{{{ resolved_count }}}}</div>
                        <div style="font-size: 10px; color: #86efac; text-transform: uppercase; letter-spacing: 1px; margin-top: 4px;">Resolved</div>
                    </td>
                </tr>
            </table>
        ''', border_left="#8b5cf6")}

        {_card('''
            <h3 style="color: #e2e8f0; margin: 0 0 16px; font-size: 14px; font-weight: 600;">&#127919; Severity Breakdown</h3>
            <table role="presentation" cellpadding="0" cellspacing="0" border="0" style="width: 100%;">
                <tr>
                    <td style="padding: 0 0 12px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                            <span style="color: #f87171; font-size: 12px;">Critical</span>
                            <span style="color: #f87171; font-size: 12px; font-weight: 600;">{{ critical_count }}</span>
                        </div>
                        <div style="background: rgba(255,255,255,0.06); border-radius: 6px; height: 6px; overflow: hidden;">
                            <div style="background: linear-gradient(90deg, #ef4444, #f87171); height: 100%; width: {{ critical_percent }}%; border-radius: 6px;"></div>
                        </div>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 0 0 12px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                            <span style="color: #fb923c; font-size: 12px;">High</span>
                            <span style="color: #fb923c; font-size: 12px; font-weight: 600;">{{ high_count }}</span>
                        </div>
                        <div style="background: rgba(255,255,255,0.06); border-radius: 6px; height: 6px; overflow: hidden;">
                            <div style="background: linear-gradient(90deg, #f97316, #fb923c); height: 100%; width: {{ high_percent }}%; border-radius: 6px;"></div>
                        </div>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 0 0 12px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                            <span style="color: #fbbf24; font-size: 12px;">Medium</span>
                            <span style="color: #fbbf24; font-size: 12px; font-weight: 600;">{{ medium_count }}</span>
                        </div>
                        <div style="background: rgba(255,255,255,0.06); border-radius: 6px; height: 6px; overflow: hidden;">
                            <div style="background: linear-gradient(90deg, #eab308, #fbbf24); height: 100%; width: {{ medium_percent }}%; border-radius: 6px;"></div>
                        </div>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 0;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                            <span style="color: #4ade80; font-size: 12px;">Low</span>
                            <span style="color: #4ade80; font-size: 12px; font-weight: 600;">{{ low_count }}</span>
                        </div>
                        <div style="background: rgba(255,255,255,0.06); border-radius: 6px; height: 6px; overflow: hidden;">
                            <div style="background: linear-gradient(90deg, #22c55e, #4ade80); height: 100%; width: {{ low_percent }}%; border-radius: 6px;"></div>
                        </div>
                    </td>
                </tr>
            </table>
        ''')}

        {_card('''
            <h3 style="color: #fca5a5; margin: 0 0 12px; font-size: 14px; font-weight: 600;">&#9888; Top Issues</h3>
            {{ top_issues_html }}
        ''', border_left="#ef4444")}

        {_btn("linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%)", "dashboard_url", "View Full Dashboard")}
        ''',
        footer_text="You're receiving this weekly digest based on your notification preferences."
    )


def get_scan_report_attachment_template():
    return get_base_template(
        title="Security Scan Report — ONYX",
        header_gradient=GRADIENTS["blue"],
        header_icon="📋",
        header_subtitle="Detailed security scan report attached",
        content='''
        <h2 style="color: #f1f5f9; font-size: 22px; margin: 0 0 8px; font-weight: 700; line-height: 1.3;">
            Scan Report: {{ project_name }}
        </h2>
        <p style="color: #64748b; font-size: 14px; margin: 0 0 24px; line-height: 1.6;">
            Generated on {{ generated_at }} &mdash; {{ total_findings }} finding(s) across {{ scanner_count }} scanner(s).
        </p>

        {{ severity_section }}

        {{ findings_section }}

        <div style="text-align: center; margin: 28px 0; padding: 20px; background: rgba(255,255,255,0.03); border-radius: 12px;">
            <p style="color: #64748b; font-size: 12px; margin: 0; line-height: 1.5;">
                This report was generated automatically by ONYX Security Intelligence Platform.
            </p>
        </div>
        ''',
        footer_text="Detailed security scan report attached to this email."
    )


def get_scan_report_email_template():
    return get_base_template(
        title="Security Scan Report — ONYX",
        header_gradient=GRADIENTS["purple_blue"],
        header_icon="🛡️",
        header_subtitle="Your security scan report is ready",
        content=f'''
        {_card('''
            <h2 style="color: #f1f5f9; font-size: 20px; margin: 0 0 6px; font-weight: 700;">&#128202; Executive Summary</h2>
            <p style="color: #c4b5fd; margin: 0; font-size: 13px; line-height: 1.5;">
                Security scan completed for <strong style="color: #f1f5f9;">{{{{ project_name }}}}</strong>
            </p>
        ''', border_left="#8b5cf6")}

        <div style="text-align: center; margin: 28px 0;">
            <div style="display: inline-block; background: linear-gradient(135deg, {{{{ score_bg_start }}}} 0%, {{{{ score_bg_end }}}} 100%); border-radius: 16px; padding: 20px 40px; border: 1px solid {{{{ score_border }}}};">
                <div style="font-size: 42px; font-weight: 800; color: {{{{ score_color }}}}; letter-spacing: -2px; line-height: 1;">
                    {{{{ risk_score }}}}
                </div>
                <div style="font-size: 11px; color: {{{{ score_label_color }}}}; text-transform: uppercase; letter-spacing: 2px; margin-top: 4px; font-weight: 600;">
                    Security Score
                </div>
            </div>
        </div>

        {_card(f'''
            <h3 style="color: #e2e8f0; margin: 0 0 12px; font-size: 14px; font-weight: 600;">&#128203; Scan Details</h3>
            <table style="width: 100%; border-collapse: collapse;">
                {_info_row("Project", "project_name")}
                {_info_row("Scan Type", "scan_type")}
                {_info_row("Duration", "duration")}
                {_info_row("Total Findings", "total_findings")}
                {_info_row("Completed", "completed_at")}
            </table>
        ''')}

        {_severity_grid(
            ("critical", "critical_count", "rgba(239,68,68,0.12)", "rgba(239,68,68,0.25)", "#f87171", "Critical"),
            ("high", "high_count", "rgba(249,115,22,0.12)", "rgba(249,115,22,0.25)", "#fb923c", "High"),
            ("medium", "medium_count", "rgba(234,179,8,0.12)", "rgba(234,179,8,0.25)", "#fbbf24", "Medium"),
            ("low", "low_count", "rgba(34,197,94,0.12)", "rgba(34,197,94,0.25)", "#4ade80", "Low"),
        )}

        {{{{ top_findings_html }}}}

        {{% if has_critical %}}
        <div style="margin: 28px 0; padding: 16px 20px; background: rgba(239,68,68,0.1); border-radius: 12px; border: 1px solid rgba(239,68,68,0.2); border-left: 4px solid #ef4444;">
            <h3 style="color: #fca5a5; margin: 0 0 6px; font-size: 14px; font-weight: 600;">&#128680; Immediate Action Required</h3>
            <p style="color: #fda4af; margin: 0; font-size: 13px; line-height: 1.5;">
                {{{{ critical_count }}}} critical vulnerabilities require immediate attention. Review the full report and prioritize remediation.
            </p>
        </div>
        {{% endif %}}

        {_btn("linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%)", "report_url", "View Full Report")}

        <div style="text-align: center; margin: 20px 0; padding: 14px; background: rgba(255,255,255,0.02); border-radius: 10px;">
            <p style="color: #64748b; font-size: 11px; margin: 0; line-height: 1.5;">
                {{% if has_attachment %}}&#128206; A detailed PDF report is attached to this email.{{% endif %}}
                This report was generated by ONYX Security Intelligence Platform.
            </p>
        </div>
        ''',
        footer_text="You received this because scan notifications are enabled for your project."
    )
