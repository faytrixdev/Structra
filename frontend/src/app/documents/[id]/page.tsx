"use client";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Navbar } from "@/components/Navbar";
import { PipelineStatus } from "@/components/PipelineStatus";
import { KnowledgeCard } from "@/components/KnowledgeCard";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useMutation, useQueryClient } from "@tanstack/react-query";

export default function DocumentDetailPage() {
  const params = useParams();
  const queryClient = useQueryClient();

  const { data: docData } = useQuery({
    queryKey: ["document", params.id],
    queryFn: () => api.get<any>(`/documents/${params.id}`),
  });

  const { data: knowledgeData } = useQuery({
    queryKey: ["knowledge", params.id],
    queryFn: () => api.get<any>(`/knowledge?document_id=${params.id}`),
  });

  const processMutation = useMutation({
    mutationFn: () => api.post(`/documents/${params.id}/process`),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["document-status", params.id] }); },
  });

  const doc = docData?.data;
  const knowledge = knowledgeData?.data || [];

  if (!doc) return <div className="min-h-screen bg-zinc-950"><Navbar /><main className="p-6"><p className="text-zinc-500">Loading...</p></main></div>;

  return (
    <div className="min-h-screen bg-zinc-950">
      <Navbar />
      <main className="p-6 space-y-6">
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-2xl font-bold">{doc.title}</h1>
            <p className="text-zinc-400 text-sm">{doc.file_type} • {doc.file_size ? Math.round(doc.file_size / 1024) + "KB" : "?"}</p>
          </div>
          <Button onClick={() => processMutation.mutate()} disabled={doc.status !== "uploaded" && doc.status !== "failed"}>
            {processMutation.isPending ? "Starting..." : "Process"}
          </Button>
        </div>

        <Card className="bg-zinc-900 border-zinc-800">
          <CardHeader><CardTitle>Pipeline Status</CardTitle></CardHeader>
          <CardContent><PipelineStatus documentId={params.id as string} /></CardContent>
        </Card>

        <div>
          <h2 className="text-xl font-semibold mb-4">Extracted Knowledge ({knowledge.length})</h2>
          <div className="grid gap-3">
            {knowledge.map((k: any) => <KnowledgeCard key={k.id} knowledge={k} />)}
            {knowledge.length === 0 && <p className="text-zinc-500">No knowledge extracted yet. Run the pipeline.</p>}
          </div>
        </div>
      </main>
    </div>
  );
}
