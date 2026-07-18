"use client";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Navbar } from "@/components/Navbar";
import { DashboardStats } from "@/components/DashboardStats";
import { Skeleton, StatCardSkeleton, DocumentRowSkeleton } from "@/components/Skeleton";
import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";
import { ArrowUpRight, FileText, Brain, Sparkles } from "lucide-react";

export default function DashboardPage() {
  const { data: docsData, isLoading: docsLoading } = useQuery({
    queryKey: ["documents"],
    queryFn: () => api.get<any>("/documents"),
    staleTime: 30000,
  });

  const { data: knowledgeData, isLoading: knowledgeLoading } = useQuery({
    queryKey: ["knowledge-stats"],
    queryFn: () => api.get<any>("/knowledge"),
    staleTime: 30000,
  });

  const documents = docsData?.data || [];
  const knowledge = knowledgeData?.data || [];

  return (
    <div className="min-h-screen">
      <Navbar />
      <main className="max-w-7xl mx-auto px-6 py-10 space-y-12">
        {/* Hero */}
        <div className="animate-fade-in">
          <h1 className="text-4xl md:text-5xl font-bold text-zinc-900">
            Welcome to <span className="text-gradient">Structra</span>
          </h1>
          <p className="text-zinc-500 mt-2 text-lg">
            Transform unstructured documents into structured knowledge.
          </p>
        </div>

        {/* Stats */}
        {docsLoading && knowledgeLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <StatCardSkeleton />
            <StatCardSkeleton />
            <StatCardSkeleton />
          </div>
        ) : (
          <DashboardStats
            documents={documents.length}
            knowledge={knowledge.length}
            processed={documents.filter((d: any) => d.status === "completed").length}
          />
        )}

        {/* Quick actions */}
        <div className="grid md:grid-cols-3 gap-6">
          <ActionCard
            href="/documents"
            icon={<FileText className="w-6 h-6" />}
            title="Upload documents"
            desc="Add PDFs, DOCX, or any text document to extract knowledge from."
            gradient="from-blue-500 to-cyan-500"
          />
          <ActionCard
            href="/knowledge"
            icon={<Brain className="w-6 h-6" />}
            title="Explore knowledge"
            desc="Browse your extracted atomic knowledge units."
            gradient="from-purple-500 to-pink-500"
          />
          <ActionCard
            href="/search"
            icon={<Sparkles className="w-6 h-6" />}
            title="Semantic search"
            desc="Find knowledge using natural language queries."
            gradient="from-amber-500 to-orange-500"
          />
        </div>

        {/* Recent documents */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-zinc-900">Recent documents</h2>
            <Link href="/documents" className="text-sm text-indigo-600 hover:underline flex items-center gap-1">
              View all <ArrowUpRight className="w-4 h-4" />
            </Link>
          </div>
          {documents.length === 0 ? (
            <Card className="bg-white/80 backdrop-blur border-zinc-200/60">
              <CardContent className="p-10 text-center">
                <FileText className="w-10 h-10 text-zinc-300 mx-auto mb-3" />
                <p className="text-zinc-500">No documents yet. Upload your first document to get started.</p>
              </CardContent>
            </Card>
          ) : docsLoading ? (
            <div className="space-y-4">
              <DocumentRowSkeleton />
              <DocumentRowSkeleton />
              <DocumentRowSkeleton />
            </div>
          ) : (
            <div className="space-y-4">
              {documents.slice(0, 5).map((d: any) => (
                <Link key={d.id} href={`/documents/${d.id}`} className="block">
                  <Card className="bg-white/80 backdrop-blur border-zinc-200/60 card-hover cursor-pointer">
                    <CardContent className="p-4 flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-lg bg-indigo-50 flex items-center justify-center">
                          <FileText className="w-5 h-5 text-indigo-600" />
                        </div>
                        <div>
                          <p className="font-medium text-zinc-900">{d.title}</p>
                          <p className="text-xs text-zinc-500">{new Date(d.created_at).toLocaleDateString()}</p>
                        </div>
                      </div>
                      <StatusBadge status={d.status} />
                    </CardContent>
                  </Card>
                </Link>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

function ActionCard({ href, icon, title, desc, gradient }: any) {
  return (
    <Link href={href}>
      <Card className="bg-white/80 backdrop-blur border-zinc-200/60 card-hover group cursor-pointer h-full">
        <CardContent className="p-6">
          <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${gradient} flex items-center justify-center text-white shadow-md mb-4 group-hover:scale-110 transition-transform`}>
            {icon}
          </div>
          <h3 className="font-semibold text-zinc-900 text-lg">{title}</h3>
          <p className="text-sm text-zinc-500 mt-1">{desc}</p>
        </CardContent>
      </Card>
    </Link>
  );
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    completed: "bg-emerald-50 text-emerald-700 border-emerald-200",
    failed: "bg-red-50 text-red-700 border-red-200",
    uploaded: "bg-zinc-50 text-zinc-600 border-zinc-200",
  };
  return (
    <span className={`text-xs font-medium px-2.5 py-1 rounded-full border ${styles[status] || styles.uploaded}`}>
      {status}
    </span>
  );
}
