import { InformationCircleIcon } from "@heroicons/react/24/outline";
import toast from "react-hot-toast";
import { Button } from "../../styles/components";
import SettingCard from "./SettingCard";
import Toggle from "./Toggle";
import SystemInfo from "./SystemInfo";

const SystemTab = ({ user }) => (
  <div className="space-y-6">
    <h2 className="text-xl font-semibold text-white">System Information</h2>

    <div className="bg-cyan-500/10 border border-cyan-500/30 rounded-xl p-6">
      <div className="flex items-start space-x-3">
        <InformationCircleIcon className="h-5 w-5 text-cyan-400 mt-0.5" />
        <div>
          <p className="text-cyan-400 font-medium">Platform Information</p>
          <SystemInfo />
        </div>
      </div>
    </div>

    <SettingCard
      title="Maintenance Mode"
      description="Temporarily disable new scans for system maintenance"
      type="danger"
    >
      <Toggle
        label="Maintenance Mode"
        enabled={false}
        onChange={() => toast("Maintenance mode requires admin privileges", { icon: "ℹ️" })}
        disabled={user?.role !== "admin"}
      />
    </SettingCard>

    <SettingCard title="Export Data" description="Download your security scan data and reports">
      <Button
        onClick={() => toast.success("Data export initiated! You'll receive an email when ready.")}
        variant="success"
      >
        Export Data
      </Button>
    </SettingCard>
  </div>
);

export default SystemTab;
