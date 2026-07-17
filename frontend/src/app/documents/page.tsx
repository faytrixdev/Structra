"use client";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Navbar } from "@/components/Navbar";
import { DocumentUploader } from "@/components/DocumentUploader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import Link from "next/link";

export default function DocumentsPage() {
  const { data: docsData, isLoading } = useQuery({ queryKey: ["documents"], queryFn: () => api.get<any>("/documents") });
  const docs = docsData?.data || [];

  return (
    <div className="min-h-screen bg-zinc-950">
      <Navbar />
      <main className="p-6 space-y-6">
        <h1 className="text-2xl font-bold">Documents</h1>
        <DocumentUploader />
        <Card className="bg-zinc-900 border-zinc-800">
          <CardHeader><CardTitle>All Documents</CardTitle></CardHeader>
          <CardContent>
            {isLoading ? <p className="text-zinc-500">Loading...</p> : docs.length === 0 ? (
              <p className="text-zinc-500">No documents uploaded yet.</p>
            ) : (
              <div className="space-y-2">
                {docs.map((doc: any) => (
                  <Link key={doc.id} href={`/documents/${doc.id}`} className="flex justify-between items-center p-3 hover:bg-zinc-800 rounded transition-colors">
                    <div>
                      <p className="font-medium">{doc.title}</p>
                      <p className="text-sm text-zinc-500">{doc.file_type} • {doc.file_size ? Math.round(doc.file_size / 1024) + "KB" : "?"}</p>
                    </div>
                    <span className={`text-xs px-2 py-1 rounded ${doc.status === "completed" ? "bg-green-900 text-green-300" : doc.status === "failed" ? "bg-red-900 text-red-300" : "bg-yellow-900 text-yellow-300"}`}>{doc.status}</span>
                  </Link>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
