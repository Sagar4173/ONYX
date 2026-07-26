const CONFIGURE_BUTTON_CLASS =
  "rounded-full bg-gradient-to-r from-cyan-400 via-violet-500 to-cyan-400 text-white font-semibold hover:from-cyan-300 hover:via-violet-400 hover:to-cyan-300 shadow-lg hover:shadow-xl hover:shadow-cyan-500/20 transition-all duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900 text-sm px-4 py-2";

const UserSettingsTab = () => (
  <div className="space-y-6">
    <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-800/50 rounded-xl p-6">
      <h3 className="text-xl font-bold text-white mb-4">User Management Settings</h3>
      <div className="space-y-4">
        {[
          { title: "Allow User Registration", desc: "Allow users to register new accounts" },
          { title: "Password Policy", desc: "Configure password requirements" },
          { title: "Session Management", desc: "Configure session timeout and security" },
        ].map((item) => (
          <div key={item.title} className="flex items-center justify-between">
            <div>
              <h4 className="text-white font-medium">{item.title}</h4>
              <p className="text-gray-400 text-sm">{item.desc}</p>
            </div>
            <button className={CONFIGURE_BUTTON_CLASS}>Configure</button>
          </div>
        ))}
      </div>
    </div>
  </div>
);

export default UserSettingsTab;
