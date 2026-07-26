/**
 * Documentation Page - ONYX Security Platform
 * Interactive API documentation and user guides
 */
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  BookOpenIcon,
  CodeBracketIcon,
  RocketLaunchIcon,
  ShieldCheckIcon,
  ArrowLeftIcon,
  ArrowRightIcon,
  PuzzlePieceIcon,
  KeyIcon,
  ClipboardDocumentIcon,
  CheckIcon,
} from "@heroicons/react/24/outline";
import { OnyxLogo } from "../common";

const DocumentationPage = () => {
  const navigate = useNavigate();
  const [copiedCode, setCopiedCode] = useState(null);

  const copyToClipboard = (code, id) => {
    navigator.clipboard.writeText(code);
    setCopiedCode(id);
    setTimeout(() => setCopiedCode(null), 2000);
  };

  const categories = [
    {
      title: "Getting Started",
      icon: RocketLaunchIcon,
      color: "cyan",
      items: [
        { title: "Quick Start Guide", desc: "Get up and running in 5 minutes" },
        { title: "Account Setup", desc: "Configure your account and team" },
        { title: "First Scan", desc: "Run your first security scan" },
        { title: "Understanding Results", desc: "Interpret scan findings" },
      ],
    },
    {
      title: "Security Scanners",
      icon: ShieldCheckIcon,
      color: "violet",
      items: [
        { title: "SAST Scanning", desc: "Static application security testing" },
        { title: "Secret Detection", desc: "Find exposed credentials" },
        { title: "Container Security", desc: "Docker and container scanning" },
        { title: "IaC Analysis", desc: "Infrastructure as Code security" },
      ],
    },
    {
      title: "Integrations",
      icon: PuzzlePieceIcon,
      color: "emerald",
      items: [
        { title: "GitHub Integration", desc: "Connect your GitHub repos" },
        { title: "GitLab Integration", desc: "Connect your GitLab projects" },
        { title: "CI/CD Pipelines", desc: "Integrate with your workflow" },
        { title: "Webhooks", desc: "Real-time notifications" },
      ],
    },
    {
      title: "API Reference",
      icon: CodeBracketIcon,
      color: "amber",
      items: [
        { title: "Authentication", desc: "API keys and OAuth" },
        { title: "Projects API", desc: "Manage projects" },
        { title: "Scans API", desc: "Trigger and manage scans" },
        { title: "Reports API", desc: "Generate reports" },
      ],
    },
  ];

  const codeExamples = {
    curl: `curl -X POST "https://api.onyx-security.io/v1/scans" \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "repository_url": "https://github.com/your-org/your-repo",
    "scan_types": ["sast", "secrets", "container"]
  }'`,
    python: `import requests

API_KEY = "your_api_key"
BASE_URL = "https://api.onyx-security.io/v1"

response = requests.post(
    f"{BASE_URL}/scans",
    headers={"Authorization": f"Bearer {API_KEY}"},
    json={
        "repository_url": "https://github.com/your-org/your-repo",
        "scan_types": ["sast", "secrets", "container"]
    }
)

scan = response.json()
print(f"Scan started: {scan['id']}")`,
    javascript: `const response = await fetch('https://api.onyx-security.io/v1/scans', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer YOUR_API_KEY',
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    repository_url: 'https://github.com/your-org/your-repo',
    scan_types: ['sast', 'secrets', 'container']
  }),
});

const scan = await response.json();
console.log('Scan started:', scan.id);`,
  };

  const [selectedLang, setSelectedLang] = useState("curl");

  const endpoints = [
    { method: "POST", path: "/v1/scans", desc: "Initiate a new security scan" },
    {
      method: "GET",
      path: "/v1/scans/{id}",
      desc: "Get scan status and results",
    },
    { method: "GET", path: "/v1/projects", desc: "List all projects" },
    { method: "POST", path: "/v1/projects", desc: "Create a new project" },
    {
      method: "GET",
      path: "/v1/reports/{id}",
      desc: "Get detailed scan report",
    },
    { method: "DELETE", path: "/v1/scans/{id}", desc: "Cancel a running scan" },
  ];

  const methodColors = {
    GET: "text-emerald-400 bg-emerald-500/10",
    POST: "text-cyan-400 bg-cyan-500/10",
    PUT: "text-amber-400 bg-amber-500/10",
    DELETE: "text-red-400 bg-red-500/10",
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-gray-950/90 backdrop-blur-xl border-b border-gray-800/50">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-3">
            <OnyxLogo className="w-8 h-8" />
            <span className="text-xl font-bold bg-gradient-to-r from-cyan-400 to-violet-400 bg-clip-text text-transparent">
              ONYX
            </span>
            <span className="text-gray-500 text-sm ml-2">Docs</span>
          </Link>
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate(-1)}
              className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors"
            >
              <ArrowLeftIcon className="w-4 h-4" />
              <span>Back</span>
            </button>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="pt-28 pb-16 border-b border-gray-800/50">
        <div className="max-w-6xl mx-auto px-6">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
            <div>
              <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-cyan-500/10 border border-cyan-500/20 mb-4">
                <BookOpenIcon className="w-4 h-4 text-cyan-400" />
                <span className="text-sm text-cyan-400">Documentation</span>
              </div>
              <h1 className="text-3xl md:text-4xl font-bold mb-2">ONYX Documentation</h1>
              <p className="text-gray-400 max-w-xl">
                Everything you need to integrate ONYX into your security workflow. Explore guides,
                API references, and best practices.
              </p>
            </div>
            <div className="flex gap-3">
              <Link
                to="/register"
                className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-violet-600 text-white font-medium hover:shadow-lg hover:shadow-cyan-500/25 transition-all"
              >
                Get API Key
              </Link>
              <a
                href="https://github.com/Sagar4173/ONYX"
                target="_blank"
                rel="noopener noreferrer"
                className="px-5 py-2.5 rounded-xl border border-gray-700 text-gray-300 hover:text-white hover:border-gray-600 transition-all flex items-center gap-2"
              >
                GitHub
                <ArrowRightIcon className="w-4 h-4" />
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* Categories */}
      <section className="py-12 border-b border-gray-800/50">
        <div className="max-w-6xl mx-auto px-6">
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {categories.map((cat, i) => (
              <div
                key={i}
                className="p-6 rounded-2xl bg-gray-900/50 border border-gray-800/50 hover:border-gray-700/50 transition-all group cursor-pointer"
              >
                <cat.icon
                  className={`w-8 h-8 text-${cat.color}-400 mb-4 group-hover:scale-110 transition-transform`}
                />
                <h3 className="text-lg font-semibold mb-3">{cat.title}</h3>
                <ul className="space-y-2">
                  {cat.items.map((item, j) => (
                    <li key={j} className="text-sm">
                      <span className="text-gray-300 hover:text-white cursor-pointer">
                        {item.title}
                      </span>
                      <span className="text-gray-600 ml-1">— {item.desc}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Quick Start */}
      <section className="py-12 border-b border-gray-800/50">
        <div className="max-w-6xl mx-auto px-6">
          <h2 className="text-2xl font-bold mb-6">Quick Start</h2>

          <div className="grid md:grid-cols-3 gap-6">
            <div className="p-6 rounded-2xl bg-gradient-to-br from-cyan-500/10 to-cyan-500/5 border border-cyan-500/20">
              <div className="w-10 h-10 rounded-full bg-cyan-500/20 flex items-center justify-center text-cyan-400 font-bold mb-4">
                1
              </div>
              <h3 className="font-semibold mb-2">Create Account</h3>
              <p className="text-gray-400 text-sm mb-3">
                Sign up for a free account to get your API key.
              </p>
              <Link
                to="/register"
                className="text-cyan-400 text-sm hover:underline flex items-center gap-1"
              >
                Sign Up <ArrowRightIcon className="w-3 h-3" />
              </Link>
            </div>

            <div className="p-6 rounded-2xl bg-gradient-to-br from-violet-500/10 to-violet-500/5 border border-violet-500/20">
              <div className="w-10 h-10 rounded-full bg-violet-500/20 flex items-center justify-center text-violet-400 font-bold mb-4">
                2
              </div>
              <h3 className="font-semibold mb-2">Get API Key</h3>
              <p className="text-gray-400 text-sm mb-3">
                Generate an API key from your dashboard settings.
              </p>
              <span className="text-violet-400 text-sm flex items-center gap-1">
                <KeyIcon className="w-3 h-3" /> Settings → API Keys
              </span>
            </div>

            <div className="p-6 rounded-2xl bg-gradient-to-br from-emerald-500/10 to-emerald-500/5 border border-emerald-500/20">
              <div className="w-10 h-10 rounded-full bg-emerald-500/20 flex items-center justify-center text-emerald-400 font-bold mb-4">
                3
              </div>
              <h3 className="font-semibold mb-2">Start Scanning</h3>
              <p className="text-gray-400 text-sm mb-3">
                Use the API or dashboard to scan your repositories.
              </p>
              <span className="text-emerald-400 text-sm flex items-center gap-1">
                <CheckIcon className="w-3 h-3" /> Ready to go!
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* Code Examples */}
      <section className="py-12 border-b border-gray-800/50">
        <div className="max-w-6xl mx-auto px-6">
          <h2 className="text-2xl font-bold mb-6">Start a Scan</h2>

          <div className="rounded-2xl bg-gray-900/50 border border-gray-800/50 overflow-hidden">
            {/* Language Tabs */}
            <div className="flex items-center gap-1 px-4 pt-4 border-b border-gray-800/50 pb-2">
              {["curl", "python", "javascript"].map((lang) => (
                <button
                  key={lang}
                  onClick={() => setSelectedLang(lang)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                    selectedLang === lang
                      ? "bg-cyan-500/20 text-cyan-400"
                      : "text-gray-400 hover:text-white"
                  }`}
                >
                  {lang.charAt(0).toUpperCase() + lang.slice(1)}
                </button>
              ))}

              <button
                onClick={() => copyToClipboard(codeExamples[selectedLang], selectedLang)}
                className="ml-auto px-3 py-1.5 rounded-lg text-sm text-gray-400 hover:text-white hover:bg-gray-800 transition-all flex items-center gap-2"
              >
                {copiedCode === selectedLang ? (
                  <>
                    <CheckIcon className="w-4 h-4 text-emerald-400" />
                    Copied!
                  </>
                ) : (
                  <>
                    <ClipboardDocumentIcon className="w-4 h-4" />
                    Copy
                  </>
                )}
              </button>
            </div>

            {/* Code Block */}
            <pre className="p-6 overflow-x-auto">
              <code className="text-sm text-gray-300 font-mono">{codeExamples[selectedLang]}</code>
            </pre>
          </div>
        </div>
      </section>

      {/* API Endpoints */}
      <section className="py-12 border-b border-gray-800/50">
        <div className="max-w-6xl mx-auto px-6">
          <h2 className="text-2xl font-bold mb-6">API Endpoints</h2>

          <div className="rounded-2xl bg-gray-900/50 border border-gray-800/50 overflow-hidden">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-800/50">
                  <th className="text-left py-3 px-4 text-gray-400 font-medium text-sm">Method</th>
                  <th className="text-left py-3 px-4 text-gray-400 font-medium text-sm">
                    Endpoint
                  </th>
                  <th className="text-left py-3 px-4 text-gray-400 font-medium text-sm hidden md:table-cell">
                    Description
                  </th>
                </tr>
              </thead>
              <tbody>
                {endpoints.map((ep, i) => (
                  <tr
                    key={i}
                    className="border-b border-gray-800/30 last:border-0 hover:bg-gray-800/30 transition-colors cursor-pointer"
                  >
                    <td className="py-3 px-4">
                      <span
                        className={`px-2 py-1 rounded text-xs font-mono font-semibold ${
                          methodColors[ep.method]
                        }`}
                      >
                        {ep.method}
                      </span>
                    </td>
                    <td className="py-3 px-4 font-mono text-sm text-gray-300">{ep.path}</td>
                    <td className="py-3 px-4 text-gray-400 text-sm hidden md:table-cell">
                      {ep.desc}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <p className="mt-4 text-gray-500 text-sm">
            Base URL: <code className="text-gray-400">https://api.onyx-security.io/v1</code>
          </p>
        </div>
      </section>

      {/* Help */}
      <section className="py-12">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <h2 className="text-2xl font-bold mb-4">Need Help?</h2>
          <p className="text-gray-400 mb-6">
            Can't find what you're looking for? Our team is here to help.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <a
              href="mailto:support@onyx-security.io"
              className="px-6 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-violet-600 text-white font-semibold hover:shadow-lg hover:shadow-cyan-500/25 transition-all"
            >
              Contact Support
            </a>
            <a
              href="https://github.com/Sagar4173/ONYX/issues"
              target="_blank"
              rel="noopener noreferrer"
              className="px-6 py-3 rounded-xl border border-gray-700 text-gray-300 hover:text-white hover:border-gray-600 transition-all"
            >
              Open an Issue
            </a>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-800/50 py-8">
        <div className="max-w-6xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-4">
          <p className="text-gray-500 text-sm">
            © {new Date().getFullYear()} ONYX Security Intelligence
          </p>
          <div className="flex items-center gap-6 text-sm">
            <Link to="/docs" className="text-cyan-400">
              Documentation
            </Link>
            <Link to="/terms" className="text-gray-500 hover:text-gray-300 transition-colors">
              Terms
            </Link>
            <Link to="/legal" className="text-gray-500 hover:text-gray-300 transition-colors">
              Data Policy
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default DocumentationPage;
