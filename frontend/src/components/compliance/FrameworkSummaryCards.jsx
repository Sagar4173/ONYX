import { Card } from "../../styles/components";
import { frameworks, getScoreGradient } from "./complianceHelpers";

const FrameworkSummaryCards = ({ summaryData }) => {
  if (!summaryData) return null;

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
      {frameworks.slice(0, 3).map((framework) => {
        const summary = summaryData.frameworks?.find((f) => f.framework === framework.id);
        return (
          <Card key={framework.id} padding="lg" className="shadow-xl">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <span className="text-3xl">{framework.icon}</span>
                <div>
                  <h3 className="text-lg font-semibold text-white">{framework.name}</h3>
                  <p className="text-sm text-gray-400">
                    {summary?.total_assessments || 0} assessments
                  </p>
                </div>
              </div>
            </div>
            {summary && (
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">Avg Score:</span>
                  <span
                    className={`font-semibold ${summary.average_score >= 70 ? "text-green-400" : "text-yellow-400"}`}
                  >
                    {summary.average_score?.toFixed(1)}%
                  </span>
                </div>
                <div className="w-full bg-gray-700/50 rounded-full h-2">
                  <div
                    className={`bg-gradient-to-r ${getScoreGradient(summary.average_score)} h-2 rounded-full transition-all`}
                    style={{ width: `${summary.average_score}%` }}
                  />
                </div>
              </div>
            )}
          </Card>
        );
      })}
    </div>
  );
};

export default FrameworkSummaryCards;
