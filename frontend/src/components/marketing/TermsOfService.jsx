/**
 * Terms of Service Page - ONYX Security Platform
 * Professional terms with real content
 */
import { Link, useNavigate } from "react-router-dom";
import {
  DocumentTextIcon,
  ShieldCheckIcon,
  ScaleIcon,
  ExclamationTriangleIcon,
  CurrencyDollarIcon,
  XCircleIcon,
  CheckCircleIcon,
  ArrowLeftIcon,
} from "@heroicons/react/24/outline";
import { OnyxLogo } from "../common";

const TermsOfService = () => {
  const navigate = useNavigate();
  const lastUpdated = "December 26, 2025";
  const effectiveDate = "December 26, 2025";

  const sections = [
    {
      id: "acceptance",
      title: "Acceptance of Terms",
      icon: CheckCircleIcon,
      content: `By accessing or using ONYX Security Intelligence platform ("Service"), you agree to be bound by these Terms of Service ("Terms"). If you are using the Service on behalf of an organization, you represent that you have the authority to bind that organization to these Terms.

If you do not agree to these Terms, you may not access or use the Service. We reserve the right to modify these Terms at any time, and such modifications will be effective immediately upon posting.`,
    },
    {
      id: "description",
      title: "Description of Service",
      icon: ShieldCheckIcon,
      content: `ONYX provides an AI-powered security scanning and vulnerability detection platform that includes:

• **Static Application Security Testing (SAST)**: Automated code analysis for security vulnerabilities
• **Secret Detection**: Identification of exposed credentials and sensitive data
• **Container Security**: Vulnerability scanning for Docker images and containers
• **Infrastructure as Code (IaC) Analysis**: Security checks for Terraform, CloudFormation, and Kubernetes
• **Compliance Reporting**: Automated compliance assessments (SOC2, HIPAA, GDPR, etc.)
• **Remediation Guidance**: AI-powered fix suggestions and security recommendations

The Service is provided "as is" and we continuously improve and update features.`,
    },
    {
      id: "accounts",
      title: "User Accounts",
      icon: DocumentTextIcon,
      content: `**Registration**: You must provide accurate and complete information when creating an account. You are responsible for maintaining the confidentiality of your credentials.

**Account Security**: You must immediately notify us of any unauthorized access or security breach. You are responsible for all activities that occur under your account.

**Account Types**:
• **Free Tier**: Limited scans per month, basic features
• **Professional**: Unlimited scans, advanced features, priority support
• **Enterprise**: Custom limits, dedicated support, SLA guarantees

**Eligibility**: You must be at least 18 years old and have the legal capacity to enter into these Terms.`,
    },
    {
      id: "acceptable-use",
      title: "Acceptable Use",
      icon: ScaleIcon,
      content: `You agree NOT to use the Service to:

• **Illegal Activities**: Scan repositories you don't own or have authorization to test
• **Malicious Purposes**: Develop malware, exploit vulnerabilities, or conduct attacks
• **Abuse**: Overwhelm our systems with excessive requests or denial-of-service attempts
• **Unauthorized Access**: Attempt to access other users' accounts or data
• **Reverse Engineering**: Decompile, reverse engineer, or extract source code
• **Reselling**: Resell, sublicense, or redistribute the Service without authorization
• **Harmful Content**: Upload malicious code intended to damage our systems

Violation of these terms may result in immediate termination of your account.`,
    },
    {
      id: "intellectual-property",
      title: "Intellectual Property",
      icon: DocumentTextIcon,
      content: `**Our Property**: ONYX, its logos, features, and functionality are owned by ONYX Security Intelligence and protected by intellectual property laws. You may not copy, modify, or create derivative works without permission.

**Your Content**: You retain all rights to your source code and data. By using our Service, you grant us a limited license to process your code solely for the purpose of providing security scanning services.

**Feedback**: If you provide suggestions or feedback, you grant us the right to use such feedback without compensation.

**No Training**: We do not use your proprietary code to train AI models without explicit consent.`,
    },
    {
      id: "payment",
      title: "Payment Terms",
      icon: CurrencyDollarIcon,
      content: `**Pricing**: Current pricing is available on our website. Prices are subject to change with 30 days notice.

**Billing**: 
• Monthly plans are billed in advance
• Annual plans receive discounted rates
• Enterprise agreements may have custom terms

**Taxes**: Prices do not include applicable taxes, which will be added at checkout.

**Refunds**: 
• Monthly plans: No refunds for partial months
• Annual plans: Pro-rated refunds within first 30 days
• Enterprise: As specified in your agreement

**Payment Failure**: We may suspend access if payment fails after reasonable attempts to collect.`,
    },
    {
      id: "data-handling",
      title: "Data Handling",
      icon: ShieldCheckIcon,
      content: `**Processing**: Your code is processed in isolated, ephemeral environments. We do not store your source code permanently unless you enable scan history.

**Security**: We implement industry-standard security measures including encryption, access controls, and monitoring.

**Privacy**: Data handling is governed by our Privacy Policy, which is incorporated into these Terms.

**Data Location**: Data may be processed in various geographic locations. Enterprise customers can specify data residency requirements.

**Retention**: Scan results are retained according to your plan settings. You can delete your data at any time.`,
    },
    {
      id: "disclaimers",
      title: "Disclaimers",
      icon: ExclamationTriangleIcon,
      content: `**As-Is Basis**: The Service is provided "AS IS" and "AS AVAILABLE" without warranties of any kind, express or implied.

**No Guarantee**: We do not guarantee that:
• The Service will detect all vulnerabilities
• The Service will be uninterrupted or error-free
• Scan results will be completely accurate
• The Service will meet your specific requirements

**Security Limitations**: Automated security scanning is one component of a comprehensive security program. You remain responsible for your overall security posture.

**Third-Party Tools**: We integrate with third-party scanners. We are not responsible for issues arising from these tools.`,
    },
    {
      id: "liability",
      title: "Limitation of Liability",
      icon: ScaleIcon,
      content: `**Maximum Liability**: To the fullest extent permitted by law, our total liability for any claims arising from these Terms or the Service is limited to the amount you paid us in the 12 months preceding the claim.

**Exclusions**: We are not liable for:
• Indirect, incidental, special, or consequential damages
• Loss of profits, data, or business opportunities
• Damages from security breaches of your systems
• Issues arising from your failure to address reported vulnerabilities

**Exceptions**: These limitations do not apply where prohibited by law or in cases of gross negligence or willful misconduct.`,
    },
    {
      id: "termination",
      title: "Termination",
      icon: XCircleIcon,
      content: `**By You**: You may terminate your account at any time through account settings or by contacting support.

**By Us**: We may suspend or terminate your account if you:
• Violate these Terms
• Fail to pay fees when due
• Engage in fraudulent or illegal activity
• Abuse the Service or our staff

**Effect of Termination**: Upon termination:
• Access to the Service will be revoked
• Your data will be deleted within 30 days (unless legally required to retain)
• You remain liable for any outstanding fees
• Provisions that should survive will continue in effect`,
    },
    {
      id: "general",
      title: "General Provisions",
      icon: DocumentTextIcon,
      content: `**Governing Law**: These Terms are governed by the laws of Delaware, USA, without regard to conflict of law principles.

**Dispute Resolution**: Any disputes will be resolved through binding arbitration in accordance with AAA rules, except for injunctive relief.

**Entire Agreement**: These Terms, together with the Privacy Policy, constitute the entire agreement between you and ONYX.

**Severability**: If any provision is found unenforceable, the remaining provisions will continue in effect.

**Assignment**: You may not assign these Terms without our consent. We may assign our rights and obligations to affiliates or successors.

**Contact**: For questions about these Terms, contact legal@onyx-security.io`,
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
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-violet-500/10 border border-violet-500/20 mb-6">
              <ScaleIcon className="w-4 h-4 text-violet-400" />
              <span className="text-sm text-violet-400">Legal</span>
            </div>
            <h1 className="text-4xl md:text-5xl font-bold mb-4">Terms of Service</h1>
            <p className="text-gray-400">
              Effective: {effectiveDate} | Last updated: {lastUpdated}
            </p>
          </div>

          {/* Important Notice */}
          <div className="bg-amber-500/10 border border-amber-500/30 rounded-2xl p-6 mb-12">
            <div className="flex items-start gap-4">
              <ExclamationTriangleIcon className="w-6 h-6 text-amber-400 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="font-semibold text-amber-400 mb-2">Important Notice</h3>
                <p className="text-gray-400 text-sm">
                  Please read these Terms carefully before using ONYX. By using our Service, you
                  acknowledge that you have read, understood, and agree to be bound by these Terms.
                  If you do not agree, please do not use the Service.
                </p>
              </div>
            </div>
          </div>

          {/* Table of Contents */}
          <div className="bg-gray-900/50 border border-gray-800/50 rounded-2xl p-6 mb-12">
            <h2 className="text-lg font-semibold mb-4">Table of Contents</h2>
            <ul className="grid md:grid-cols-2 gap-2">
              {sections.map((section, i) => (
                <li key={section.id}>
                  <a
                    href={`#${section.id}`}
                    className="flex items-center gap-2 text-gray-400 hover:text-violet-400 transition-colors text-sm"
                  >
                    <span className="text-violet-500">{i + 1}.</span>
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
                  <div className="p-2 rounded-xl bg-gradient-to-br from-violet-500/20 to-purple-500/20">
                    <section.icon className="w-5 h-5 text-violet-400" />
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
                          .replace(/• /g, "<span class='text-violet-400'>•</span> "),
                      }}
                    />
                  ))}
                </div>
              </section>
            ))}
          </div>

          {/* Contact */}
          <div className="mt-16 p-8 bg-gradient-to-br from-gray-800/50 to-gray-900/50 border border-gray-700/50 rounded-2xl text-center">
            <h3 className="text-xl font-bold mb-2">Questions About Terms?</h3>
            <p className="text-gray-400 mb-6">
              Contact our legal team for any questions about these Terms of Service.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <a
                href="mailto:legal@onyx-security.io"
                className="px-6 py-3 rounded-xl bg-gradient-to-r from-violet-500 to-purple-600 text-white font-semibold hover:shadow-lg hover:shadow-violet-500/25 transition-all"
              >
                Contact Legal Team
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
            <Link to="/terms" className="text-violet-400">
              Terms of Service
            </Link>
            <Link to="/legal" className="text-gray-500 hover:text-gray-300 transition-colors">
              Privacy Policy
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default TermsOfService;
