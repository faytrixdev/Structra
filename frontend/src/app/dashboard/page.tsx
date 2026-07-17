"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Navbar } from "@/components/Navbar";
import { DashboardStats } from "@/components/DashboardStats";
import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function DashboardPage() {
  const router = useRouter();
  useEffect(() => { try { api.get("/auth/me"); } catch { router.push("/login"); } }, [router]);
  const { data: docsData } = useQuery({ queryKey: ["documents"], queryFn: () => api.get<any>("/documents") });
  const recentDocs = (docsData?.data || []).slice(0, 5);

  return (
    <div className="min-h-screen bg-zinc-950">
      <Navbar />
      <main className="p-6 space-y-6">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <DashboardStats />
        <Card className="bg-zinc-900 border-zinc-800">
          <CardHeader><CardTitle>Recent Documents</CardTitle></CardHeader>
          <CardContent>
            {recentDocs.length === 0 ? (
              <p className="text-zinc-500">No documents yet. <a href="/documents" className="text-blue-400 hover:underline">Upload one</a></p>
            ) : (
              <div className="space-y-2">
                {recentDocs.map((doc: any) => (
                  <div key={doc.id} className="flex justify-between items-center p-2 hover:bg-zinc-800 rounded">
                    <span>{doc.title}</span>
                    <span className={`text-xs px-2 py-1 rounded ${doc.status === "completed" ? "bg-green-900 text-green-300" : "bg-yellow-900 text-yellow-300"}`}>{doc.status}</span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
