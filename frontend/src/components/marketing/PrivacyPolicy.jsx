/**
 * Privacy Policy Page - ONYX Security Platform
 * Professional privacy policy with real content
 */
import { Link, useNavigate } from "react-router-dom";
import {
  ShieldCheckIcon,
  LockClosedIcon,
  EyeSlashIcon,
  ServerIcon,
  GlobeAltIcon,
  UserGroupIcon,
  DocumentTextIcon,
  ArrowLeftIcon,
} from "@heroicons/react/24/outline";
import { OnyxLogo } from "../common";

const PrivacyPolicy = () => {
  const navigate = useNavigate();
  const lastUpdated = "December 26, 2025";

  const sections = [
    {
      id: "introduction",
      title: "Introduction",
      icon: DocumentTextIcon,
      content: `ONYX Security Intelligence ("ONYX," "we," "us," or "our") is committed to protecting your privacy. This Privacy Policy explains how we collect, use, disclose, and safeguard your information when you use our security scanning platform and related services.

By accessing or using ONYX, you agree to this Privacy Policy. If you do not agree with the terms of this Privacy Policy, please do not access the platform.`,
    },
    {
      id: "data-collection",
      title: "Information We Collect",
      icon: ServerIcon,
      content: `We collect information that you provide directly to us:

• **Account Information**: Email address, name, company name, and password when you register
• **Repository Data**: Source code, repository URLs, and configuration files you choose to scan
• **Scan Results**: Vulnerability findings, security scores, and remediation data
• **Usage Data**: How you interact with our platform, features used, and preferences
• **Communication Data**: Messages, feedback, and support requests

We automatically collect:
• **Device Information**: Browser type, operating system, IP address
• **Log Data**: Access times, pages viewed, referring URLs
• **Analytics**: Aggregated usage patterns and performance metrics`,
    },
    {
      id: "data-use",
      title: "How We Use Your Information",
      icon: EyeSlashIcon,
      content: `We use your information to:

• **Provide Services**: Perform security scans, generate reports, and deliver findings
• **Improve Platform**: Enhance scanning accuracy, develop new features, and optimize performance
• **Communication**: Send security alerts, product updates, and respond to inquiries
• **Security**: Detect, prevent, and address technical issues and abuse
• **Compliance**: Meet legal obligations and enforce our terms of service
• **Analytics**: Understand usage patterns to improve user experience

We never sell your personal data to third parties.`,
    },
    {
      id: "data-security",
      title: "Data Security",
      icon: LockClosedIcon,
      content: `We implement industry-standard security measures:

• **Encryption**: All data encrypted in transit (TLS 1.3) and at rest (AES-256)
• **Access Control**: Role-based access with multi-factor authentication
• **Infrastructure**: SOC 2 Type II certified data centers
• **Monitoring**: 24/7 security monitoring and intrusion detection
• **Auditing**: Regular security audits and penetration testing
• **Incident Response**: Documented incident response procedures

Your source code is processed in isolated, ephemeral environments and is not stored permanently after scanning unless you explicitly enable scan history.`,
    },
    {
      id: "data-retention",
      title: "Data Retention",
      icon: ServerIcon,
      content: `We retain your data as follows:

• **Account Data**: Retained while your account is active, deleted within 30 days of account deletion
• **Scan Results**: Retained for 90 days by default, configurable in your settings
• **Audit Logs**: Retained for 1 year for security and compliance purposes
• **Source Code**: Processed ephemerally, not permanently stored unless configured
• **Analytics Data**: Aggregated data retained for product improvement

You can request data deletion at any time through your account settings or by contacting support.`,
    },
    {
      id: "data-sharing",
      title: "Information Sharing",
      icon: UserGroupIcon,
      content: `We may share your information with:

• **Service Providers**: Cloud infrastructure, payment processors, and analytics services under strict data protection agreements
• **Legal Requirements**: When required by law, court order, or governmental authority
• **Business Transfers**: In connection with a merger, acquisition, or sale of assets
• **With Your Consent**: When you explicitly authorize sharing

We do NOT:
• Sell your personal information
• Share your source code with third parties
• Use your code to train AI models without consent
• Provide access to unauthorized parties`,
    },
    {
      id: "your-rights",
      title: "Your Rights",
      icon: ShieldCheckIcon,
      content: `Depending on your location, you may have the following rights:

• **Access**: Request a copy of your personal data
• **Correction**: Update or correct inaccurate information
• **Deletion**: Request deletion of your personal data
• **Portability**: Export your data in a machine-readable format
• **Objection**: Object to certain processing activities
• **Restriction**: Request limitation of processing
• **Withdrawal**: Withdraw consent where processing is based on consent

To exercise these rights, contact us at privacy@onyx-security.io or through your account settings.`,
    },
    {
      id: "international",
      title: "International Transfers",
      icon: GlobeAltIcon,
      content: `ONYX operates globally and may transfer your data to countries other than your country of residence. We ensure appropriate safeguards are in place:

• **Standard Contractual Clauses**: EU-approved data transfer mechanisms
• **Privacy Shield**: Compliance with applicable frameworks
• **Data Processing Agreements**: Binding agreements with all processors
• **Adequacy Decisions**: Transfers to countries with adequate protection

We comply with GDPR, CCPA, and other applicable privacy regulations.`,
    },
  ];

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-gray-950/90 backdrop-blur-xl border-b border-gray-800/50">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-3 group">
            <OnyxLogo className="w-8 h-8" />
            <span className="text-xl font-bold bg-gradient-to-r from-cyan-400 to-violet-400 bg-clip-text text-transparent">
              ONYX
            </span>
          </Link>
          <button
            onClick={() => navigate(-1)}
            className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors"
          >
            <ArrowLeftIcon className="w-4 h-4" />
            <span>Back</span>
          </button>
        </div>
      </header>

      {/* Content */}
      <main className="pt-24 pb-16">
        <div className="max-w-4xl mx-auto px-6">
          {/* Title */}
          <div className="text-center mb-12">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-cyan-500/10 border border-cyan-500/20 mb-6">
              <ShieldCheckIcon className="w-4 h-4 text-cyan-400" />
              <span className="text-sm text-cyan-400">Legal</span>
            </div>
            <h1 className="text-4xl md:text-5xl font-bold mb-4">Privacy Policy</h1>
            <p className="text-gray-400">Last updated: {lastUpdated}</p>
          </div>

          {/* Table of Contents */}
          <div className="bg-gray-900/50 border border-gray-800/50 rounded-2xl p-6 mb-12">
            <h2 className="text-lg font-semibold mb-4">Table of Contents</h2>
            <ul className="grid md:grid-cols-2 gap-2">
              {sections.map((section, i) => (
                <li key={section.id}>
                  <a
                    href={`#${section.id}`}
                    className="flex items-center gap-2 text-gray-400 hover:text-cyan-400 transition-colors text-sm"
                  >
                    <span className="text-cyan-500">{i + 1}.</span>
                    {section.title}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          {/* Sections */}
          <div className="space-y-12">
            {sections.map((section, index) => (
              <section key={section.id} id={section.id} className="scroll-mt-24">
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-2 rounded-xl bg-gradient-to-br from-cyan-500/20 to-violet-500/20">
                    <section.icon className="w-5 h-5 text-cyan-400" />
                  </div>
                  <h2 className="text-2xl font-bold">
                    {index + 1}. {section.title}
                  </h2>
                </div>
                <div className="prose prose-invert prose-gray max-w-none">
                  {section.content.split("\n\n").map((paragraph, i) => (
                    <p
                      key={i}
                      className="text-gray-400 leading-relaxed mb-4 whitespace-pre-line"
                      dangerouslySetInnerHTML={{
                        __html: paragraph
                          .replace(/\*\*(.*?)\*\*/g, "<strong class='text-white'>$1</strong>")
                          .replace(/• /g, "<span class='text-cyan-400'>•</span> "),
                      }}
                    />
                  ))}
                </div>
              </section>
            ))}
          </div>

          {/* Contact */}
          <div className="mt-16 p-8 bg-gradient-to-br from-gray-800/50 to-gray-900/50 border border-gray-700/50 rounded-2xl text-center">
            <h3 className="text-xl font-bold mb-2">Questions About Privacy?</h3>
            <p className="text-gray-400 mb-6">
              Contact our Data Protection Officer for any privacy-related inquiries.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <a
                href="mailto:privacy@onyx-security.io"
                className="px-6 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-violet-600 text-white font-semibold hover:shadow-lg hover:shadow-cyan-500/25 transition-all"
              >
                Contact Privacy Team
              </a>
              <Link
                to="/"
                className="px-6 py-3 rounded-xl border border-gray-700 text-gray-300 hover:text-white hover:border-gray-600 transition-all"
              >
                Back to Home
              </Link>
            </div>
          </div>
        </div>
      </main>

      {/* Simple Footer */}
      <footer className="border-t border-gray-800/50 py-8">
        <div className="max-w-5xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-4">
          <p className="text-gray-500 text-sm">
            © {new Date().getFullYear()} ONYX Security Intelligence
          </p>
          <div className="flex items-center gap-6 text-sm">
            <Link to="/terms" className="text-gray-500 hover:text-gray-300 transition-colors">
              Terms of Service
            </Link>
            <Link to="/privacy" className="text-cyan-400">
              Privacy Policy
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default PrivacyPolicy;
