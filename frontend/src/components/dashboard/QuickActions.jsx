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
  },
  {
    name: "Run Scan",
    description: "Start security scan",
    icon: PlayIcon,
    gradient: "from-emerald-500 to-green-500",
    to: "/projects",
  },
  {
    name: "View Reports",
    description: "See all findings",
    icon: DocumentChartBarIcon,
    gradient: "from-orange-500 to-amber-500",
    to: "/reports",
  },
  {
    name: "Analytics",
    description: "Explore trends",
    icon: ChartBarIcon,
    gradient: "from-pink-500 to-rose-500",
    to: "/analytics",
  },
];

const QuickActions = () => (
  <div className="grid grid-cols-2 gap-4">
    {actions.map((action, index) => (
      <Link
        key={action.name}
        to={action.to}
        className="group relative flex flex-col items-center justify-center p-5 rounded-xl bg-gray-800/30
          border border-gray-700/30 hover:border-cyan-500/30 transition-all duration-300
          hover:-translate-y-1 hover:shadow-lg hover:shadow-cyan-500/10 text-center flex-1 min-h-[120px]"
        style={{ animationDelay: `${index * 0.05}s` }}
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
      </Link>
    ))}
  </div>
);

export default QuickActions;
