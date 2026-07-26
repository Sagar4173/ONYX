import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import {
  PlusIcon,
  PlayIcon,
  DocumentChartBarIcon,
  ChartBarIcon,
} from "@heroicons/react/24/outline";

const actions = [
  {
    name: "New Project",
    description: "Add repository",
    icon: PlusIcon,
    gradient: "from-blue-500 to-purple-600",
    to: "/projects?action=new",
    shortcut: "N",
  },
  {
    name: "Run Scan",
    description: "Start security scan",
    icon: PlayIcon,
    gradient: "from-emerald-500 to-green-500",
    to: "/projects",
    shortcut: "S",
  },
  {
    name: "View Reports",
    description: "See all findings",
    icon: DocumentChartBarIcon,
    gradient: "from-orange-500 to-amber-500",
    to: "/reports",
    shortcut: "R",
  },
  {
    name: "Analytics",
    description: "Explore trends",
    icon: ChartBarIcon,
    gradient: "from-pink-500 to-rose-500",
    to: "/analytics",
    shortcut: "A",
  },
];

const container = {
  hidden: {},
  show: { transition: { staggerChildren: 0.08 } },
};
const itemAnim = { hidden: { opacity: 0, y: 20 }, show: { opacity: 1, y: 0 } };

const QuickActions = () => (
  <motion.div
    className="grid grid-cols-2 gap-4"
    variants={container}
    initial="hidden"
    animate="show"
  >
    {actions.map((action) => (
      <motion.div key={action.name} variants={itemAnim}>
        <Link
          to={action.to}
          className="group relative flex flex-col items-center justify-center p-5 rounded-xl bg-gray-800/30 border border-gray-700/30 hover:border-cyan-500/30 transition-all duration-300 hover:-translate-y-1 hover:shadow-lg hover:shadow-cyan-500/10 text-center min-h-[120px] focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500"
        >
          <div
            className={`absolute inset-0 rounded-xl bg-gradient-to-br ${action.gradient} opacity-0 group-hover:opacity-10 transition-opacity`}
          />
          <div
            className={`p-3 rounded-xl bg-gradient-to-br ${action.gradient} shadow-lg mb-3 group-hover:scale-110 transition-transform`}
          >
            <action.icon className="h-5 w-5 text-white" />
          </div>
          <span className="text-sm font-medium text-white">{action.name}</span>
          <span className="text-xs text-gray-500 mt-1">{action.description}</span>
          <span className="absolute top-2 right-2 px-1.5 py-0.5 bg-gray-700/50 text-gray-500 rounded text-[10px] font-mono">
            {action.shortcut}
          </span>
        </Link>
      </motion.div>
    ))}
  </motion.div>
);

export default QuickActions;
