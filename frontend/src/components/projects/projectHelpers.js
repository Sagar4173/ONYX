export const getPriorityColor = (priority) => {
  switch (priority) {
    case "critical":
      return "text-red-400 bg-red-500/20";
    case "high":
      return "text-orange-400 bg-orange-500/20";
    case "medium":
      return "text-yellow-400 bg-yellow-500/20";
    case "low":
      return "text-green-400 bg-green-500/20";
    default:
      return "text-gray-400 bg-gray-500/20";
  }
};

export const getStatusColor = (status) => {
  switch (status) {
    case "active":
      return "text-green-400 bg-green-500/20";
    case "inactive":
      return "text-yellow-400 bg-yellow-500/20";
    case "archived":
      return "text-gray-400 bg-gray-500/20";
    default:
      return "text-gray-400 bg-gray-500/20";
  }
};
