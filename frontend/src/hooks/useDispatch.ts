import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { dispatchApi } from "@/lib/api";

export function useDispatchRecommendations() {
  return useQuery({
    queryKey: ["dispatch-recommendations"],
    queryFn: () => dispatchApi.getRecommendations().then((r) => r.data),
  });
}

export function useAcknowledgeRecommendation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => dispatchApi.acknowledge(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["dispatch-recommendations"] }),
  });
}
