"use client";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

const steps = ["uploaded", "extracting", "cleaning", "segmenting", "extracting_ideas", "classifying", "extracting_entities", "building_relations", "validating", "completed"];

export function PipelineStatus({ documentId }: { documentId: string }) {
  const { data: statusData, isLoading } = useQuery({
    queryKey: ["document-status", documentId],
    queryFn: () => api.get<any>(`/documents/${documentId}/status`),
    refetchInterval: 3000,
  });

  if (isLoading) return <p className="text-zinc-500">Loading status...</p>;
  const status = statusData?.data?.status || "unknown";
  const currentIndex = steps.indexOf(status);

  return (
    <div className="space-y-2">
      <p className="text-sm text-zinc-400">Status: <span className="font-medium text-white">{status}</span></p>
      <div className="flex gap-1 flex-wrap">
        {steps.map((step, i) => (
          <div key={step} className={`h-2 w-6 rounded-full ${i < currentIndex ? "bg-green-500" : i === currentIndex ? "bg-blue-500 animate-pulse" : "bg-zinc-700"}`} />
        ))}
      </div>
    </div>
  );
}
