"use client";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { api } from "@/lib/api";
import { Navbar } from "@/components/Navbar";
import { DocumentUploader } from "@/components/DocumentUploader";
import { Card, CardContent } from "@/components/ui/card";
import { DocumentRowSkeleton } from "@/components/Skeleton";
import { FileText, Trash2 } from "lucide-react";

export default function DocumentsPage() {
  const [refreshKey, setRefreshKey] = useState(0);
  const { data: docsData, isLoading: docsLoading } = useQuery({
    queryKey: ["documents", refreshKey],
    queryFn: () => api.get<any>("/documents"),
  });

  const documents = docsData?.data || [];

  return (
    <div className="min-h-screen">
      <Navbar />
      <main className="max-w-7xl mx-auto px-6 py-10 space-y-10">
        <div className="animate-fade-in">
          <h1 className="text-3xl font-bold text-zinc-900">Documents</h1>
          <p className="text-zinc-500 mt-1">Upload and manage your source documents</p>
        </div>

        <DocumentUploader onUploaded={() => setRefreshKey(k => k + 1)} />

        <div>
          <h2 className="text-lg font-semibold text-zinc-900 mb-4">Your documents ({documents.length})</h2>
          {docsLoading ? (
            <div className="space-y-4">
              <DocumentRowSkeleton />
              <DocumentRowSkeleton />
              <DocumentRowSkeleton />
            </div>
          ) : documents.length === 0 ? (
            <Card className="bg-white/80 backdrop-blur border-zinc-200/60">
              <CardContent className="p-10 text-center">
                <FileText className="w-10 h-10 text-zinc-300 mx-auto mb-3" />
                <p className="text-zinc-500">No documents yet. Upload one above.</p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {documents.map((d: any) => (
                <Link key={d.id} href={`/documents/${d.id}`} className="block">
                  <Card className="bg-white/80 backdrop-blur border-zinc-200/60 card-hover cursor-pointer">
                    <CardContent className="p-4 flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <div className="w-11 h-11 rounded-xl bg-indigo-50 flex items-center justify-center">
                          <FileText className="w-5 h-5 text-indigo-600" />
                        </div>
                        <div>
                          <p className="font-medium text-zinc-900">{d.title}</p>
                          <p className="text-xs text-zinc-500">
                            {d.file_type.split(".").pop().toUpperCase()} • {Math.round((d.file_size || 0) / 1024)} KB • {new Date(d.created_at).toLocaleDateString()}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <StatusBadge status={d.status} />
                        <button
                          onClick={async (e) => {
                            e.preventDefault();
                            if (confirm("Delete this document?")) {
                              await api.delete(`/documents/${d.id}`);
                              setRefreshKey(k => k + 1);
                            }
                          }}
                          className="p-2 text-zinc-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
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

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    completed: "bg-emerald-50 text-emerald-700 border-emerald-200",
    failed: "bg-red-50 text-red-700 border-red-200",
    uploaded: "bg-zinc-50 text-zinc-600 border-zinc-200",
  };
  const labels: Record<string, string> = {
    completed: "Done",
    failed: "Failed",
    uploaded: "Ready",
  };
  return (
    <span className={`text-xs font-medium px-2.5 py-1 rounded-full border ${styles[status] || styles.uploaded}`}>
      {labels[status] || status}
    </span>
  );
}
