import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import MLTrainPanel from "../components/admin/MLTrainPanel";

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
});

const DISABLED_STATUS = {
  isolation_forest_enabled: false,
  min_training_scans: 30,
  training_window_days: 90,
  model_trained: false,
  sklearn_available: false,
  active_model: null,
};

const READY_STATUS = {
  isolation_forest_enabled: true,
  min_training_scans: 30,
  training_window_days: 90,
  model_trained: false,
  sklearn_available: true,
  active_model: null,
};

export default {
  title: "Admin/MLTrainPanel",
  component: MLTrainPanel,
  decorators: [
    (Story) => (
      <QueryClientProvider client={queryClient}>
        <div className="bg-gray-900 p-6">
          <Story />
        </div>
      </QueryClientProvider>
    ),
  ],
};

export const GatedDisabled = {
  args: { status: DISABLED_STATUS },
};

export const Ready = {
  args: { status: READY_STATUS },
};
