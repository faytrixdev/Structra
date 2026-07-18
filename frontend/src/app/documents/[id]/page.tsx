"use client";
import { useParams } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Navbar } from "@/components/Navbar";
import { PipelineStatus } from "@/components/PipelineStatus";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/Skeleton";
import { Button } from "@/components/ui/button";
import { FileText, ArrowLeft, Play } from "lucide-react";
import Link from "next/link";

export default function DocumentDetailPage() {
  const params = useParams();
  const queryClient = useQueryClient();

  const { data: docData } = useQuery({
    queryKey: ["document", params.id],
    queryFn: () => api.get<any>(`/documents/${params.id}`),
    refetchInterval: (query) => {
      const status = query.state.data?.data?.status;
      if (status === "completed" || status === "failed") return false;
      return 2000;
    },
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

  if (!doc) return (
    <div className="min-h-screen">
      <Navbar />
      <main className="max-w-4xl mx-auto px-6 py-10 space-y-8">
        <div className="space-y-3">
          <Skeleton className="h-4 w-32" />
          <div className="flex items-center gap-4">
            <Skeleton className="w-14 h-14 rounded-2xl" />
            <div className="space-y-2">
              <Skeleton className="h-7 w-64" />
              <Skeleton className="h-4 w-40" />
            </div>
          </div>
        </div>
        <Card className="bg-white/80 backdrop-blur border-zinc-200/60">
          <CardContent className="p-6">
            <Skeleton className="h-40 w-full" />
          </CardContent>
        </Card>
      </main>
    </div>
  );

  return (
    <div className="min-h-screen">
      <Navbar />
      <main className="max-w-4xl mx-auto px-6 py-10 space-y-10">
        {/* Header */}
        <div className="animate-fade-in">
          <Link href="/documents" className="inline-flex items-center gap-1 text-sm text-zinc-500 hover:text-zinc-900 mb-4 transition-colors">
            <ArrowLeft className="w-4 h-4" /> Back to documents
          </Link>
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 rounded-2xl bg-indigo-50 flex items-center justify-center">
                <FileText className="w-7 h-7 text-indigo-600" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-zinc-900">{doc.title}</h1>
                <p className="text-zinc-500 text-sm">
                  {doc.file_type.split(".").pop().toUpperCase()} • {Math.round((doc.file_size || 0) / 1024)} KB
                  {doc.page_count ? ` • ${doc.page_count} pages` : ""}
                </p>
              </div>
            </div>
            <Button
              onClick={() => processMutation.mutate()}
              disabled={doc.status !== "uploaded" && doc.status !== "failed"}
              className="bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white shadow-md"
            >
              <Play className="w-4 h-4 mr-2" />
              {processMutation.isPending ? "Starting..." : "Process"}
            </Button>
          </div>
        </div>

        {/* Pipeline */}
        <Card className="bg-white/80 backdrop-blur border-zinc-200/60">
          <CardHeader>
            <CardTitle className="text-lg text-zinc-900">Pipeline</CardTitle>
          </CardHeader>
          <CardContent>
            <PipelineStatus documentId={params.id as string} />
          </CardContent>
        </Card>

        {/* Knowledge */}
        <div>
          <h2 className="text-xl font-semibold text-zinc-900 mb-4">Extracted knowledge ({knowledge.length})</h2>
          <div className="space-y-3">
            {knowledge.map((k: any) => (
              <Link key={k.id} href={`/knowledge/${k.id}`} className="block">
                <Card className="bg-white/80 backdrop-blur border-zinc-200/60 card-hover cursor-pointer">
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <span className={`text-xs font-medium px-2 py-0.5 rounded-full border ${typeColor(k.type)}`}>
                          {k.type}
                        </span>
                        <p className="text-zinc-900 mt-2">{k.statement}</p>
                      </div>
                      <span className="text-sm font-medium text-zinc-500 shrink-0 ml-4">
                        {Math.round(k.confidence * 100)}%
                      </span>
                    </div>
                  </CardContent>
                </Card>
              </Link>
            ))}
            {knowledge.length === 0 && (
              <Card className="bg-white/80 backdrop-blur border-zinc-200/60">
                <CardContent className="p-10 text-center">
                  <p className="text-zinc-500">No knowledge extracted yet. Click Process to start.</p>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

function typeColor(type: string) {
  const map: Record<string, string> = {
    Rule: "bg-blue-50 text-blue-700 border-blue-200",
    Definition: "bg-emerald-50 text-emerald-700 border-emerald-200",
    Procedure: "bg-amber-50 text-amber-700 border-amber-200",
    Responsibility: "bg-purple-50 text-purple-700 border-purple-200",
    Constraint: "bg-red-50 text-red-700 border-red-200",
    Requirement: "bg-cyan-50 text-cyan-700 border-cyan-200",
    Policy: "bg-pink-50 text-pink-700 border-pink-200",
    Concept: "bg-violet-50 text-violet-700 border-violet-200",
  };
  return map[type] || "bg-zinc-50 text-zinc-600 border-zinc-200";
}
