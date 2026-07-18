"use client";
import { useParams } from "next/navigation";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Navbar } from "@/components/Navbar";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/Skeleton";
import { ArrowLeft } from "lucide-react";

export default function KnowledgeDetailPage() {
  const params = useParams();
  const { data: detailData, isLoading } = useQuery({
    queryKey: ["knowledge-detail", params.id],
    queryFn: () => api.get<any>(`/knowledge/${params.id}`),
  });

  if (isLoading) return (
    <div className="min-h-screen">
      <Navbar />
      <main className="max-w-4xl mx-auto px-6 py-10 space-y-8">
        <div className="space-y-3">
          <Skeleton className="h-4 w-32" />
          <Skeleton className="h-7 w-48" />
          <Skeleton className="h-9 w-full" />
        </div>
        <Card className="bg-white/80 backdrop-blur border-zinc-200/60">
          <CardContent className="p-6">
            <Skeleton className="h-20 w-full" />
          </CardContent>
        </Card>
      </main>
    </div>
  );
  const k = detailData?.data;
  if (!k) return <div className="min-h-screen"><Navbar /><main className="max-w-4xl mx-auto px-6 py-10"><p className="text-zinc-500">Not found</p></main></div>;

  return (
    <div className="min-h-screen">
      <Navbar />
      <main className="max-w-4xl mx-auto px-6 py-10 space-y-10">
        <div className="animate-fade-in">
          <Link href="/knowledge" className="inline-flex items-center gap-1 text-sm text-zinc-500 hover:text-zinc-900 mb-4 transition-colors">
            <ArrowLeft className="w-4 h-4" /> Back to knowledge
          </Link>
          <div className="flex items-center gap-3">
            <span className={`text-xs font-medium px-2.5 py-1 rounded-full border ${typeColor(k.type)}`}>
              {k.type}
            </span>
            <span className="text-sm text-zinc-500">{Math.round(k.confidence * 100)}% confidence</span>
          </div>
          <h1 className="text-3xl font-bold text-zinc-900 mt-3">{k.title || k.statement}</h1>
        </div>

        {/* Statement */}
        <Card className="bg-white/80 backdrop-blur border-zinc-200/60">
          <CardHeader><CardTitle className="text-lg text-zinc-900">Statement</CardTitle></CardHeader>
          <CardContent><p className="text-zinc-700 leading-relaxed">{k.statement}</p></CardContent>
        </Card>

        {/* Entities */}
        {k.entities?.length > 0 && (
          <Card className="bg-white/80 backdrop-blur border-zinc-200/60">
            <CardHeader><CardTitle className="text-lg text-zinc-900">Entities</CardTitle></CardHeader>
            <CardContent>
              <div className="space-y-3">
                {k.entities.map((e: any, i: number) => (
                  <div key={i} className="flex items-center gap-3">
                    <span className="text-xs font-medium px-2 py-0.5 rounded-md bg-zinc-100 text-zinc-500 w-16 text-center">{e.entity_type}</span>
                    <span className="text-zinc-900 font-medium">{e.value}</span>
                    {e.role && <span className="text-xs text-zinc-400">({e.role})</span>}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Conditions */}
        {k.conditions?.length > 0 && (
          <Card className="bg-white/80 backdrop-blur border-zinc-200/60">
            <CardHeader><CardTitle className="text-lg text-zinc-900">Conditions</CardTitle></CardHeader>
            <CardContent>
              <div className="space-y-2">
                {k.conditions.map((c: any, i: number) => (
                  <div key={i} className="flex gap-3 text-sm">
                    <span className="text-xs font-medium px-2 py-0.5 rounded-md bg-amber-50 text-amber-700 border border-amber-200">{c.condition_type}</span>
                    <span className="text-zinc-700">{c.description}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Original text */}
        <Card className="bg-white/80 backdrop-blur border-zinc-200/60">
          <CardHeader><CardTitle className="text-lg text-zinc-900">Original text</CardTitle></CardHeader>
          <CardContent><p className="text-zinc-500 text-sm italic">{k.original_text}</p></CardContent>
        </Card>
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
