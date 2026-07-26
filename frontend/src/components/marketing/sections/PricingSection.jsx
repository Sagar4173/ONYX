import { useNavigate } from "react-router-dom";
import { SparklesIcon, CheckCircleIcon } from "@heroicons/react/24/outline";
import { pricingPlans } from "../landingPageData";

const PricingSection = () => {
  const navigate = useNavigate();

  return (
    <section id="pricing" className="py-32 bg-gradient-to-b from-gray-950 via-gray-900 to-gray-950">
      <div className="max-w-7xl mx-auto px-6">
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-emerald-500/10 border border-emerald-500/20 mb-6">
            <SparklesIcon className="w-4 h-4 text-emerald-400" />
            <span className="text-sm text-emerald-400">Pricing</span>
          </div>
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
            Simple, Transparent Pricing
          </h2>
          <p className="text-xl text-gray-400 max-w-2xl mx-auto">
            Start free, scale as you grow. No hidden fees, no surprises.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
          {pricingPlans.map((plan) => (
            <div
              key={plan.name}
              className={`relative p-8 rounded-3xl transition-all ${
                plan.popular
                  ? "bg-gradient-to-br from-gray-800/80 to-gray-900/80 border-2 border-cyan-500/50 scale-105 shadow-2xl shadow-cyan-500/20"
                  : "bg-gray-900/30 border border-gray-800/50 hover:border-gray-700/50"
              }`}
            >
              {plan.popular && (
                <div className="absolute -top-4 left-1/2 -translate-x-1/2">
                  <div className="px-4 py-1 rounded-full bg-gradient-to-r from-cyan-500 to-violet-500 text-white text-sm font-semibold">
                    Most Popular
                  </div>
                </div>
              )}
              <div className="text-center mb-8">
                <h3 className="text-xl font-bold text-white mb-2">{plan.name}</h3>
                <div className="flex items-baseline justify-center gap-2 mb-2">
                  <span className="text-4xl font-black text-white">{plan.price}</span>
                  <span className="text-gray-500">/{plan.period}</span>
                </div>
                <p className="text-sm text-gray-400">{plan.description}</p>
              </div>
              <ul className="space-y-4 mb-8">
                {plan.features.map((feature) => (
                  <li key={feature} className="flex items-center gap-3">
                    <CheckCircleIcon className="w-5 h-5 text-cyan-400 flex-shrink-0" />
                    <span className="text-gray-300 text-sm">{feature}</span>
                  </li>
                ))}
              </ul>
              <button
                onClick={() => navigate("/register")}
                className={`w-full py-3 rounded-xl font-semibold transition-all ${
                  plan.popular
                    ? "bg-gradient-to-r from-cyan-500 to-violet-600 text-white hover:shadow-lg hover:shadow-cyan-500/25"
                    : "bg-gray-800 text-gray-300 hover:bg-gray-700 border border-gray-700"
                }`}
              >
                {plan.cta}
              </button>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default PricingSection;
