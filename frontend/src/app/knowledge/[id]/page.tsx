"use client";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Navbar } from "@/components/Navbar";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function KnowledgeDetailPage() {
  const params = useParams();
  const { data: detailData, isLoading } = useQuery({
    queryKey: ["knowledge-detail", params.id],
    queryFn: () => api.get<any>(`/knowledge/${params.id}`),
  });

  if (isLoading) return <div className="min-h-screen bg-zinc-950"><Navbar /><main className="p-6"><p className="text-zinc-500">Loading...</p></main></div>;
  const k = detailData?.data;
  if (!k) return <div className="min-h-screen bg-zinc-950"><Navbar /><main className="p-6"><p className="text-zinc-500">Not found</p></main></div>;

  return (
    <div className="min-h-screen bg-zinc-950">
      <Navbar />
      <main className="p-6 space-y-6 max-w-4xl">
        <div>
          <span className="text-xs font-medium px-2 py-0.5 rounded bg-zinc-800 text-zinc-300">{k.type}</span>
          <h1 className="text-2xl font-bold mt-2">{k.title || k.statement}</h1>
        </div>
        <Card className="bg-zinc-900 border-zinc-800">
          <CardHeader><CardTitle>Statement</CardTitle></CardHeader>
          <CardContent><p>{k.statement}</p></CardContent>
        </Card>
        {k.entities?.length > 0 && (
          <Card className="bg-zinc-900 border-zinc-800">
            <CardHeader><CardTitle>Entities</CardTitle></CardHeader>
            <CardContent>
              <div className="space-y-2">
                {k.entities.map((e: any, i: number) => (
                  <div key={i} className="flex gap-2 text-sm">
                    <span className="text-zinc-500 w-16">{e.entity_type}</span>
                    <span>{e.value}</span>
                    {e.role && <span className="text-zinc-600">({e.role})</span>}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
        {k.conditions?.length > 0 && (
          <Card className="bg-zinc-900 border-zinc-800">
            <CardHeader><CardTitle>Conditions</CardTitle></CardHeader>
            <CardContent>
              {k.conditions.map((c: any, i: number) => (
                <p key={i} className="text-sm"><span className="text-zinc-500">{c.condition_type}:</span> {c.description}</p>
              ))}
            </CardContent>
          </Card>
        )}
        <Card className="bg-zinc-900 border-zinc-800">
          <CardHeader><CardTitle>Metadata</CardTitle></CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <span className="text-zinc-500">Confidence</span>
              <span>{Math.round(k.confidence * 100)}%</span>
              <span className="text-zinc-500">Original text</span>
              <span className="text-zinc-300 text-xs">{k.original_text}</span>
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
