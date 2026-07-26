import { motion } from "framer-motion";

const stagger = { hidden: {}, show: { transition: { staggerChildren: 0.06 } } };
const item = { hidden: { opacity: 0, y: 10 }, show: { opacity: 1, y: 0 } };

const UserSettingsTab = () => (
  <motion.div className="space-y-6" variants={stagger} initial="hidden" animate="show">
    <motion.div variants={item} className="bg-gray-800/40 backdrop-blur-sm border border-gray-700/50 rounded-xl p-6">
      <h3 className="text-xl font-bold text-white mb-4">User Management Settings</h3>
      <div className="space-y-4">
        {[
          { title: "Allow User Registration", desc: "Allow users to register new accounts" },
          { title: "Password Policy", desc: "Configure password requirements" },
          { title: "Session Management", desc: "Configure session timeout and security" },
        ].map((setting) => (
          <div
            key={setting.title}
            className="flex items-center justify-between p-4 bg-gray-800/30 rounded-xl border border-gray-700/30 border-l-4 border-l-cyan-500/50"
          >
            <div>
              <h4 className="text-white font-medium">{setting.title}</h4>
              <p className="text-gray-400 text-sm">{setting.desc}</p>
            </div>
            <button className="rounded-full bg-gradient-to-r from-cyan-400 via-violet-500 to-cyan-400 text-white font-semibold hover:from-cyan-300 hover:via-violet-400 hover:to-cyan-300 shadow-lg hover:shadow-xl hover:shadow-cyan-500/20 transition-all duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900 text-sm px-4 py-2">
              Configure
            </button>
          </div>
        ))}
      </div>
    </motion.div>
  </motion.div>
);

export default UserSettingsTab;
