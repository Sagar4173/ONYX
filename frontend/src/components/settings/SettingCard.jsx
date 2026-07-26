import { motion } from "framer-motion";

const accentBorders = {
  warning: "border-l-yellow-500",
  danger: "border-l-red-500",
};

const SettingCard = ({ title, description, children, type = "default" }) => (
  <motion.div
    initial={{ opacity: 0, y: 10 }}
    whileInView={{ opacity: 1, y: 0 }}
    viewport={{ once: true }}
    transition={{ duration: 0.3 }}
    className={`bg-gray-800/40 backdrop-blur-sm border border-gray-700/50 rounded-xl p-6 ${
      accentBorders[type] || "border-l-cyan-500/50"
    } border-l-4`}
  >
    <div className="flex items-start justify-between">
      <div className="flex-1">
        <h4 className="text-white font-medium mb-1">{title}</h4>
        {description && <p className="text-gray-400 text-sm mb-4">{description}</p>}
      </div>
      <div className="ml-4 flex-shrink-0">{children}</div>
    </div>
  </motion.div>
);

export default SettingCard;
