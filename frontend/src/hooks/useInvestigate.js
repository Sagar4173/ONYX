import { useQuery } from "@tanstack/react-query";
import { runInvestigate } from "../services/aiClient";

export function useInvestigate({ scanId, findingId, question }) {
  return useQuery({
    queryKey: ["investigate", scanId, findingId, question],
    queryFn: () => runInvestigate({ scanId, findingId, question }),
    enabled: Boolean(scanId && findingId) && question !== null,
    retry: false,
    staleTime: Infinity,
    refetchInterval: false,
  });
}
