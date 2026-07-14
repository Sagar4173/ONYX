"""
Security Email Templates
Handles scan results, security alerts, vulnerability notifications, and weekly digests
"""

from .base_template import get_base_template, GRADIENTS, SEVERITY_COLORS


def get_scan_completed_template() -> str:
    """Scan completion notification template"""
    return get_base_template(
        title="Scan Completed",
        header_gradient=GRADIENTS["blue"],
        header_icon="✅",
        header_subtitle="Security Scan Completed",
        content='''
        <h2 style="color: #f1f5f9; font-size: 24px; margin: 0 0 16px 0; font-weight: 600;">
            Scan Complete: {{ project_name }}
        </h2>
        
        <p style="color: #94a3b8; font-size: 16px; line-height: 1.7; margin: 0 0 24px 0;">
            Your {{ scan_type }} security scan has finished. Here's a summary of the findings:
        </p>
        
        <!-- Stats Grid -->
        <div style="display: table; width: 100%; margin: 24px 0;">
            <div style="display: table-row;">
                <div style="display: table-cell; width: 25%; padding: 8px;">
                    <div style="background: rgba(239, 68, 68, 0.15); padding: 20px; border-radius: 16px; text-align: center; border: 1px solid rgba(239, 68, 68, 0.3);">
                        <div style="font-size: 32px; font-weight: 700; color: #f87171;">{{ critical_count }}</div>
                        <div style="font-size: 12px; color: #fca5a5; text-transform: uppercase; letter-spacing: 1px; margin-top: 4px;">Critical</div>
                    </div>
                </div>
                <div style="display: table-cell; width: 25%; padding: 8px;">
                    <div style="background: rgba(249, 115, 22, 0.15); padding: 20px; border-radius: 16px; text-align: center; border: 1px solid rgba(249, 115, 22, 0.3);">
                        <div style="font-size: 32px; font-weight: 700; color: #fb923c;">{{ high_count }}</div>
                        <div style="font-size: 12px; color: #fdba74; text-transform: uppercase; letter-spacing: 1px; margin-top: 4px;">High</div>
                    </div>
                </div>
                <div style="display: table-cell; width: 25%; padding: 8px;">
                    <div style="background: rgba(234, 179, 8, 0.15); padding: 20px; border-radius: 16px; text-align: center; border: 1px solid rgba(234, 179, 8, 0.3);">
                        <div style="font-size: 32px; font-weight: 700; color: #fbbf24;">{{ medium_count }}</div>
                        <div style="font-size: 12px; color: #fcd34d; text-transform: uppercase; letter-spacing: 1px; margin-top: 4px;">Medium</div>
                    </div>
                </div>
                <div style="display: table-cell; width: 25%; padding: 8px;">
                    <div style="background: rgba(34, 197, 94, 0.15); padding: 20px; border-radius: 16px; text-align: center; border: 1px solid rgba(34, 197, 94, 0.3);">
                        <div style="font-size: 32px; font-weight: 700; color: #4ade80;">{{ low_count }}</div>
                        <div style="font-size: 12px; color: #86efac; text-transform: uppercase; letter-spacing: 1px; margin-top: 4px;">Low</div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Scan Details -->
        <div style="margin: 24px 0; padding: 20px; background: rgba(59, 130, 246, 0.1); border-radius: 16px; border: 1px solid rgba(59, 130, 246, 0.2);">
            <h3 style="color: #93c5fd; margin: 0 0 16px 0; font-size: 15px; font-weight: 600;">📋 Scan Details</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="color: #64748b; padding: 8px 0; font-size: 14px;">Scan Type</td>
                    <td style="color: #e2e8f0; padding: 8px 0; font-size: 14px; text-align: right;">{{ scan_type }}</td>
                </tr>
                <tr>
                    <td style="color: #64748b; padding: 8px 0; font-size: 14px;">Duration</td>
                    <td style="color: #e2e8f0; padding: 8px 0; font-size: 14px; text-align: right;">{{ duration }}</td>
                </tr>
                <tr>
                    <td style="color: #64748b; padding: 8px 0; font-size: 14px;">Files Scanned</td>
                    <td style="color: #e2e8f0; padding: 8px 0; font-size: 14px; text-align: right;">{{ files_scanned }}</td>
                </tr>
                <tr>
                    <td style="color: #64748b; padding: 8px 0; font-size: 14px;">Completed At</td>
                    <td style="color: #e2e8f0; padding: 8px 0; font-size: 14px; text-align: right;">{{ completed_at }}</td>
                </tr>
            </table>
        </div>
        
        <!-- View Report Button -->
        <div style="text-align: center; margin: 32px 0;">
            <a href="{{ report_url }}" 
               style="background: linear-gradient(135deg, #3b82f6 0%, #6366f1 100%); 
                      color: #ffffff; 
                      padding: 16px 40px; 
                      text-decoration: none; 
                      border-radius: 12px; 
                      display: inline-block;
                      font-weight: 600;
                      font-size: 16px;
                      box-shadow: 0 10px 30px -5px rgba(59, 130, 246, 0.5);">
                View Full Report →
            </a>
        </div>
        ''',
        footer_text="You received this because scan notifications are enabled."
    )


def get_security_alert_template() -> str:
    """Security alert notification template"""
    return get_base_template(
        title="Security Alert",
        header_gradient=GRADIENTS["dark_red"],
        header_icon="🚨",
        header_subtitle="Critical Security Alert",
        content='''
        <div style="background: rgba(239, 68, 68, 0.2); padding: 16px 20px; border-radius: 12px; margin-bottom: 24px; border: 1px solid rgba(239, 68, 68, 0.4);">
            <p style="color: #fca5a5; margin: 0; font-size: 14px; font-weight: 500;">
                ⚠️ Immediate attention required
            </p>
        </div>
        
        <h2 style="color: #f1f5f9; font-size: 24px; margin: 0 0 16px 0; font-weight: 600;">
            {{ alert_title }}
        </h2>
        
        <p style="color: #94a3b8; font-size: 16px; line-height: 1.7; margin: 0 0 24px 0;">
            {{ alert_description }}
        </p>
        
        <!-- Alert Details -->
        <div style="margin: 24px 0; padding: 24px; background: rgba(239, 68, 68, 0.1); border-radius: 16px; border-left: 4px solid #ef4444;">
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="color: #f87171; padding: 10px 0; font-size: 14px; font-weight: 500;">Severity</td>
                    <td style="padding: 10px 0; text-align: right;">
                        <span style="background: {{ severity_color }}; color: white; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600;">{{ severity }}</span>
                    </td>
                </tr>
                <tr>
                    <td style="color: #f87171; padding: 10px 0; font-size: 14px; font-weight: 500;">Project</td>
                    <td style="color: #e2e8f0; padding: 10px 0; font-size: 14px; text-align: right;">{{ project_name }}</td>
                </tr>
                <tr>
                    <td style="color: #f87171; padding: 10px 0; font-size: 14px; font-weight: 500;">File</td>
                    <td style="color: #e2e8f0; padding: 10px 0; font-size: 14px; text-align: right; font-family: monospace;">{{ file_path }}</td>
                </tr>
                <tr>
                    <td style="color: #f87171; padding: 10px 0; font-size: 14px; font-weight: 500;">Detected At</td>
                    <td style="color: #e2e8f0; padding: 10px 0; font-size: 14px; text-align: right;">{{ detected_at }}</td>
                </tr>
            </table>
        </div>
        
        <!-- Vulnerability Type -->
        <div style="margin: 24px 0; padding: 20px; background: rgba(255,255,255,0.05); border-radius: 16px;">
            <h3 style="color: #e2e8f0; margin: 0 0 12px 0; font-size: 15px; font-weight: 600;">🔍 Vulnerability Details</h3>
            <p style="color: #94a3b8; margin: 0; font-size: 14px; line-height: 1.7;">
                <strong style="color: #e2e8f0;">Type:</strong> {{ vulnerability_type }}<br>
                <strong style="color: #e2e8f0;">CWE:</strong> {{ cwe_id }}<br>
                <strong style="color: #e2e8f0;">CVSS Score:</strong> {{ cvss_score }}
            </p>
        </div>
        
        <!-- Recommendation -->
        <div style="margin: 24px 0; padding: 20px; background: rgba(16, 185, 129, 0.1); border-radius: 16px; border: 1px solid rgba(16, 185, 129, 0.2);">
            <h3 style="color: #34d399; margin: 0 0 12px 0; font-size: 15px; font-weight: 600;">💡 Recommended Action</h3>
            <p style="color: #6ee7b7; margin: 0; font-size: 14px; line-height: 1.7;">
                {{ recommendation }}
            </p>
        </div>
        
        <!-- View Details Button -->
        <div style="text-align: center; margin: 32px 0;">
            <a href="{{ alert_url }}" 
               style="background: linear-gradient(135deg, #dc2626 0%, #ef4444 100%); 
                      color: #ffffff; 
                      padding: 16px 40px; 
                      text-decoration: none; 
                      border-radius: 12px; 
                      display: inline-block;
                      font-weight: 600;
                      font-size: 16px;
                      box-shadow: 0 10px 30px -5px rgba(220, 38, 38, 0.5);">
                View & Remediate →
            </a>
        </div>
        ''',
        footer_text="This is an automated security alert. Please review immediately."
    )


def get_new_vulnerability_template() -> str:
    """New vulnerability detection template"""
    return get_base_template(
        title="New Vulnerability Found",
        header_gradient=GRADIENTS["orange"],
        header_icon="🔓",
        header_subtitle="New Vulnerability Detected",
        content='''
        <h2 style="color: #f1f5f9; font-size: 24px; margin: 0 0 16px 0; font-weight: 600;">
            {{ vulnerability_title }}
        </h2>
        
        <p style="color: #94a3b8; font-size: 16px; line-height: 1.7; margin: 0 0 24px 0;">
            A new {{ severity }} severity vulnerability has been detected in your project <strong style="color: #e2e8f0;">{{ project_name }}</strong>.
        </p>
        
        <!-- Severity Badge -->
        <div style="text-align: center; margin: 24px 0;">
            <span style="background: {{ severity_color }}; color: white; padding: 8px 24px; border-radius: 24px; font-size: 14px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;">
                {{ severity }} SEVERITY
            </span>
        </div>
        
        <!-- Vulnerability Info -->
        <div style="margin: 24px 0; padding: 24px; background: rgba(249, 115, 22, 0.1); border-radius: 16px; border: 1px solid rgba(249, 115, 22, 0.2);">
            <h3 style="color: #fdba74; margin: 0 0 16px 0; font-size: 15px; font-weight: 600;">📍 Location</h3>
            <div style="background: rgba(0,0,0,0.3); padding: 16px; border-radius: 12px; font-family: 'Monaco', 'Menlo', monospace;">
                <p style="color: #e2e8f0; margin: 0 0 8px 0; font-size: 14px;">
                    <span style="color: #64748b;">File:</span> {{ file_path }}
                </p>
                <p style="color: #e2e8f0; margin: 0; font-size: 14px;">
                    <span style="color: #64748b;">Line:</span> {{ line_number }}
                </p>
            </div>
        </div>
        
        <!-- Description -->
        <div style="margin: 24px 0; padding: 20px; background: rgba(255,255,255,0.05); border-radius: 16px;">
            <h3 style="color: #e2e8f0; margin: 0 0 12px 0; font-size: 15px; font-weight: 600;">📝 Description</h3>
            <p style="color: #94a3b8; margin: 0; font-size: 14px; line-height: 1.7;">
                {{ description }}
            </p>
        </div>
        
        <!-- Fix Suggestion -->
        <div style="margin: 24px 0; padding: 20px; background: rgba(16, 185, 129, 0.1); border-radius: 16px; border: 1px solid rgba(16, 185, 129, 0.2);">
            <h3 style="color: #34d399; margin: 0 0 12px 0; font-size: 15px; font-weight: 600;">🛠️ How to Fix</h3>
            <p style="color: #6ee7b7; margin: 0; font-size: 14px; line-height: 1.7;">
                {{ fix_suggestion }}
            </p>
        </div>
        
        <!-- Action Button -->
        <div style="text-align: center; margin: 32px 0;">
            <a href="{{ vulnerability_url }}" 
               style="background: linear-gradient(135deg, #f97316 0%, #ea580c 100%); 
                      color: #ffffff; 
                      padding: 16px 40px; 
                      text-decoration: none; 
                      border-radius: 12px; 
                      display: inline-block;
                      font-weight: 600;
                      font-size: 16px;
                      box-shadow: 0 10px 30px -5px rgba(249, 115, 22, 0.5);">
                View Details & Fix →
            </a>
        </div>
        ''',
        footer_text="Act quickly on high and critical vulnerabilities to maintain security."
    )


def get_weekly_digest_template() -> str:
    """Weekly security digest template"""
    return get_base_template(
        title="Weekly Security Digest",
        header_gradient=GRADIENTS["purple_blue"],
        header_icon="📊",
        header_subtitle="Your Weekly Security Summary",
        content='''
        <h2 style="color: #f1f5f9; font-size: 24px; margin: 0 0 8px 0; font-weight: 600;">
            Week of {{ week_start }} - {{ week_end }}
        </h2>
        
        <p style="color: #94a3b8; font-size: 16px; line-height: 1.7; margin: 0 0 24px 0;">
            Here's your security summary for the past week across all projects.
        </p>
        
        <!-- Overall Stats -->
        <div style="background: linear-gradient(135deg, rgba(99, 102, 241, 0.2) 0%, rgba(139, 92, 246, 0.2) 100%); padding: 24px; border-radius: 16px; margin-bottom: 24px; border: 1px solid rgba(139, 92, 246, 0.3);">
            <h3 style="color: #c4b5fd; margin: 0 0 16px 0; font-size: 16px; font-weight: 600;">📈 Overview</h3>
            <div style="display: table; width: 100%;">
                <div style="display: table-cell; width: 33%; text-align: center; padding: 8px;">
                    <div style="font-size: 36px; font-weight: 700; color: #a78bfa;">{{ total_scans }}</div>
                    <div style="font-size: 12px; color: #c4b5fd; margin-top: 4px;">Scans Run</div>
                </div>
                <div style="display: table-cell; width: 33%; text-align: center; padding: 8px; border-left: 1px solid rgba(139, 92, 246, 0.3); border-right: 1px solid rgba(139, 92, 246, 0.3);">
                    <div style="font-size: 36px; font-weight: 700; color: #f87171;">{{ total_vulnerabilities }}</div>
                    <div style="font-size: 12px; color: #fca5a5; margin-top: 4px;">Vulnerabilities</div>
                </div>
                <div style="display: table-cell; width: 33%; text-align: center; padding: 8px;">
                    <div style="font-size: 36px; font-weight: 700; color: #4ade80;">{{ resolved_count }}</div>
                    <div style="font-size: 12px; color: #86efac; margin-top: 4px;">Resolved</div>
                </div>
            </div>
        </div>
        
        <!-- Severity Breakdown -->
        <div style="margin: 24px 0; padding: 20px; background: rgba(255,255,255,0.05); border-radius: 16px;">
            <h3 style="color: #e2e8f0; margin: 0 0 16px 0; font-size: 15px; font-weight: 600;">🎯 Severity Breakdown</h3>
            
            <!-- Critical Bar -->
            <div style="margin-bottom: 16px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                    <span style="color: #f87171; font-size: 13px; font-weight: 500;">Critical</span>
                    <span style="color: #f87171; font-size: 13px;">{{ critical_count }}</span>
                </div>
                <div style="background: rgba(255,255,255,0.1); border-radius: 8px; height: 8px; overflow: hidden;">
                    <div style="background: linear-gradient(90deg, #ef4444, #f87171); height: 100%; width: {{ critical_percent }}%; border-radius: 8px;"></div>
                </div>
            </div>
            
            <!-- High Bar -->
            <div style="margin-bottom: 16px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                    <span style="color: #fb923c; font-size: 13px; font-weight: 500;">High</span>
                    <span style="color: #fb923c; font-size: 13px;">{{ high_count }}</span>
                </div>
                <div style="background: rgba(255,255,255,0.1); border-radius: 8px; height: 8px; overflow: hidden;">
                    <div style="background: linear-gradient(90deg, #f97316, #fb923c); height: 100%; width: {{ high_percent }}%; border-radius: 8px;"></div>
                </div>
            </div>
            
            <!-- Medium Bar -->
            <div style="margin-bottom: 16px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                    <span style="color: #fbbf24; font-size: 13px; font-weight: 500;">Medium</span>
                    <span style="color: #fbbf24; font-size: 13px;">{{ medium_count }}</span>
                </div>
                <div style="background: rgba(255,255,255,0.1); border-radius: 8px; height: 8px; overflow: hidden;">
                    <div style="background: linear-gradient(90deg, #eab308, #fbbf24); height: 100%; width: {{ medium_percent }}%; border-radius: 8px;"></div>
                </div>
            </div>
            
            <!-- Low Bar -->
            <div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                    <span style="color: #4ade80; font-size: 13px; font-weight: 500;">Low</span>
                    <span style="color: #4ade80; font-size: 13px;">{{ low_count }}</span>
                </div>
                <div style="background: rgba(255,255,255,0.1); border-radius: 8px; height: 8px; overflow: hidden;">
                    <div style="background: linear-gradient(90deg, #22c55e, #4ade80); height: 100%; width: {{ low_percent }}%; border-radius: 8px;"></div>
                </div>
            </div>
        </div>
        
        <!-- Top Issues -->
        <div style="margin: 24px 0; padding: 20px; background: rgba(239, 68, 68, 0.1); border-radius: 16px; border: 1px solid rgba(239, 68, 68, 0.2);">
            <h3 style="color: #fca5a5; margin: 0 0 16px 0; font-size: 15px; font-weight: 600;">⚠️ Top Issues Requiring Attention</h3>
            {{ top_issues_html }}
        </div>
        
        <!-- View Dashboard Button -->
        <div style="text-align: center; margin: 32px 0;">
            <a href="{{ dashboard_url }}" 
               style="background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%); 
                      color: #ffffff; 
                      padding: 16px 40px; 
                      text-decoration: none; 
                      border-radius: 12px; 
                      display: inline-block;
                      font-weight: 600;
                      font-size: 16px;
                      box-shadow: 0 10px 30px -5px rgba(139, 92, 246, 0.5);">
                View Full Dashboard →
            </a>
        </div>
        ''',
        footer_text="You're receiving this weekly digest based on your notification preferences."
    )


def get_scan_report_attachment_template() -> str:
    """Full scan report template for email attachment, using same styling as base"""
    return get_base_template(
        title="Security Scan Report",
        header_gradient=GRADIENTS["blue"],
        header_icon="📋",
        header_subtitle="Detailed Security Scan Report",
        content='''
        <h2 style="color: #f1f5f9; font-size: 24px; margin: 0 0 16px 0; font-weight: 600;">
            Scan Report: {{ project_name }}
        </h2>
        
        <p style="color: #94a3b8; font-size: 16px; line-height: 1.7; margin: 0 0 24px 0;">
            Generated on {{ generated_at }} — {{ total_findings }} finding(s) across {{ scanner_count }} scanner(s).
        </p>
        
        {{ severity_section }}
        
        {% if findings_section %}
        <div style="margin: 24px 0;">
            <h3 style="color: #e2e8f0; font-size: 18px; margin: 0 0 16px 0; font-weight: 600;">🔍 Findings</h3>
            {{ findings_section }}
        </div>
        {% endif %}
        
        <div style="text-align: center; margin: 32px 0; padding: 20px; background: rgba(255,255,255,0.03); border-radius: 16px;">
            <p style="color: #64748b; font-size: 13px; margin: 0;">
                This report was generated automatically by ONYX Security Intelligence Platform.
            </p>
        </div>
        ''',
        footer_text="Detailed security scan report attached."
    )
