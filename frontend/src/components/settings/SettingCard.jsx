const SettingCard = ({ title, description, children, type = "default" }) => (
  <div
    className={`bg-gray-900/50 backdrop-blur-sm border rounded-xl p-6 ${
      type === "warning"
        ? "border-yellow-500/30"
        : type === "danger"
          ? "border-red-500/30"
          : "border-gray-700/50"
    }`}
  >
    <div className="flex items-start justify-between">
      <div className="flex-1">
        <h4 className="text-white font-medium mb-1">{title}</h4>
        {description && <p className="text-gray-400 text-sm mb-4">{description}</p>}
      </div>
      <div className="ml-4">{children}</div>
    </div>
  </div>
);

export default SettingCard;
