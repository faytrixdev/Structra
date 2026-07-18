"use client";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Check, Loader2, AlertCircle } from "lucide-react";

const stages = [
  { key: "uploaded", label: "Uploaded", status: "uploaded" },
  { key: "extracting", label: "Extract", status: "extracting" },
  { key: "cleaning", label: "Clean", status: "cleaning" },
  { key: "segmenting", label: "Segment", status: "segmenting" },
  { key: "extracting_ideas", label: "Ideas", status: "extracting_ideas" },
  { key: "classifying", label: "Classify", status: "classifying" },
  { key: "extracting_entities", label: "Entities", status: "extracting_entities" },
  { key: "building_relations", label: "Relations", status: "building_relations" },
  { key: "completed", label: "Done", status: "completed" },
];

const order = stages.map(s => s.status);

export function PipelineStatus({ documentId }: { documentId: string }) {
  const { data } = useQuery({
    queryKey: ["document-status", documentId],
    queryFn: () => api.get<any>(`/documents/${documentId}/status`),
    refetchInterval: (query) => {
      const status = query.state.data?.data?.status;
      if (status === "completed" || status === "failed") return false;
      return 2000;
    },
  });

  if (!data?.data) return <div className="h-2 bg-zinc-100 rounded-full animate-pulse" />;

  const status = data.data.status;
  const idx = order.indexOf(status);
  const isFailed = status === "failed";
  const isCompleted = status === "completed";

  if (isFailed) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-xl p-4 flex items-center gap-3">
        <AlertCircle className="w-5 h-5 text-red-600" />
        <div>
          <p className="font-medium text-red-900">Pipeline failed</p>
          <p className="text-sm text-red-700">{data.data.error_message || "Unknown error"}</p>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <p className="text-sm font-medium text-zinc-700 capitalize">{status.replace(/_/g, " ")}</p>
        {isCompleted && <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">Completed</span>}
      </div>
      <div className="space-y-2">
        {stages.map((stage, i) => {
          const passed = isCompleted ? true : i < idx;
          const current = isCompleted ? false : i === idx;
          return (
            <div key={stage.key} className="flex items-center gap-3">
              <div className={`
                w-7 h-7 rounded-full flex items-center justify-center shrink-0
                ${passed ? "bg-emerald-500 text-white" :
                  current ? "bg-indigo-500 text-white" :
                  "bg-zinc-100 text-zinc-400"}
              `}>
                {passed ? <Check className="w-4 h-4" /> :
                 current ? <Loader2 className="w-4 h-4 animate-spin" /> :
                 <span className="text-xs">{i + 1}</span>}
              </div>
              <span className={`text-sm ${current ? "font-medium text-indigo-700" : passed ? "text-emerald-700" : "text-zinc-400"}`}>
                {stage.label}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
