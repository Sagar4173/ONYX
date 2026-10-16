import { useQuery } from "@tanstack/react-query";
import { getAIFeatures } from "../services/aiClient";

export function useAIFeatures() {
  return useQuery({
    queryKey: ["ai-features"],
    queryFn: getAIFeatures,
    staleTime: 5 * 60 * 1000,
  });
}
