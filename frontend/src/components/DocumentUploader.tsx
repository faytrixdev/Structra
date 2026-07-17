"use client";
import { useState, useRef } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";

export function DocumentUploader() {
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();
  const [uploading, setUploading] = useState(false);

  const mutation = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append("file", file);
      return api.upload("/documents", formData);
    },
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["documents"] }); setUploading(false); },
    onError: () => setUploading(false),
  });

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault(); setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) { setUploading(true); mutation.mutate(file); }
  };

  return (
    <div
      className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${dragOver ? "border-blue-500 bg-blue-500/10" : "border-zinc-700 hover:border-zinc-500"}`}
      onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
      onDragLeave={() => setDragOver(false)}
      onDrop={handleDrop}
      onClick={() => fileInputRef.current?.click()}
    >
      <input ref={fileInputRef} type="file" className="hidden" onChange={(e) => { if (e.target.files?.[0]) { setUploading(true); mutation.mutate(e.target.files[0]); } }} />
      <p className="text-zinc-400 mb-2">Drop a document here or click to browse</p>
      <p className="text-zinc-600 text-sm">PDF, DOCX, XLSX, PPTX, TXT, MD, HTML, XML, CSV</p>
      {uploading && <p className="text-blue-400 mt-2">Uploading...</p>}
    </div>
  );
}
