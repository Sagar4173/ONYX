import { StarIcon } from "@heroicons/react/24/solid";
import { platformHighlights } from "../landingPageData";

const WhyOnyxSection = ({ currentTestimonial, setCurrentTestimonial }) => (
  <section id="why-onyx" className="py-32 relative overflow-hidden">
    <div className="absolute inset-0 bg-gradient-to-b from-gray-950 via-gray-900/50 to-gray-950" />
    <div className="max-w-7xl mx-auto px-6 relative">
      <div className="text-center mb-16">
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-amber-500/10 border border-amber-500/20 mb-6">
          <StarIcon className="w-4 h-4 text-amber-400" />
          <span className="text-sm text-amber-400">Why Choose ONYX</span>
        </div>
        <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
          Built for <span className="text-cyan-400">Modern</span> Security Teams
        </h2>
        <p className="text-xl text-gray-400 max-w-2xl mx-auto">
          Everything you need to secure your code, all in one platform
        </p>
      </div>

      <div className="grid md:grid-cols-3 gap-8">
        {platformHighlights.map((highlight, index) => (
          <div
            key={highlight.title}
            onClick={() => setCurrentTestimonial(index)}
            className={`relative p-8 rounded-3xl transition-all duration-500 cursor-pointer ${
              currentTestimonial === index
                ? "bg-gradient-to-br from-gray-800/80 to-gray-900/80 border border-cyan-500/30 scale-105 shadow-2xl shadow-cyan-500/10"
                : "bg-gray-900/30 border border-gray-800/30 hover:border-gray-700/50 hover:bg-gray-900/50"
            }`}
          >
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-cyan-500 to-violet-600 flex items-center justify-center text-white font-bold mb-6">
              {highlight.highlight}
            </div>
            <span className="inline-block px-3 py-1 rounded-full bg-cyan-500/20 text-cyan-400 text-xs font-medium mb-4">
              {highlight.category}
            </span>
            <h3 className="text-xl font-bold text-white mb-3">{highlight.title}</h3>
            <p className="text-gray-400 leading-relaxed">{highlight.description}</p>
            {currentTestimonial === index && (
              <div className="absolute top-4 right-4 w-3 h-3 rounded-full bg-cyan-400 animate-pulse" />
            )}
          </div>
        ))}
      </div>

      <div className="flex justify-center gap-2 mt-8">
        {platformHighlights.map((_, index) => (
          <button
            key={index}
            onClick={() => setCurrentTestimonial(index)}
            aria-label={`Go to testimonial ${index + 1}`}
            className={`w-2 h-2 rounded-full transition-all ${currentTestimonial === index ? "w-8 bg-cyan-400" : "bg-gray-700 hover:bg-gray-600"}`}
          />
        ))}
      </div>
    </div>
  </section>
);

export default WhyOnyxSection;
