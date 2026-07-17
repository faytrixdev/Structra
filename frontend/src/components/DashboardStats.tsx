"use client";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function DashboardStats() {
  const { data: docsData } = useQuery({ queryKey: ["documents"], queryFn: () => api.get<any>("/documents") });
  const { data: knowledgeData } = useQuery({ queryKey: ["knowledge"], queryFn: () => api.get<any>("/knowledge") });
  const docs = docsData?.data || [];
  const knowledge = knowledgeData?.data || [];
  const completedDocs = docs.filter((d: any) => d.status === "completed").length;

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <Card className="bg-zinc-900 border-zinc-800">
        <CardHeader><CardTitle className="text-zinc-400 text-sm font-medium">Total Documents</CardTitle></CardHeader>
        <CardContent><p className="text-3xl font-bold">{docs.length}</p></CardContent>
      </Card>
      <Card className="bg-zinc-900 border-zinc-800">
        <CardHeader><CardTitle className="text-zinc-400 text-sm font-medium">Completed</CardTitle></CardHeader>
        <CardContent><p className="text-3xl font-bold text-green-400">{completedDocs}</p></CardContent>
      </Card>
      <Card className="bg-zinc-900 border-zinc-800">
        <CardHeader><CardTitle className="text-zinc-400 text-sm font-medium">Knowledge Units</CardTitle></CardHeader>
        <CardContent><p className="text-3xl font-bold text-blue-400">{knowledge.length}</p></CardContent>
      </Card>
    </div>
  );
}
