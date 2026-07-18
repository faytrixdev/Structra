"use client";
import { useState } from "react";
import { Upload, FileText, CheckCircle } from "lucide-react";
import { api } from "@/lib/api";

export function DocumentUploader({ onUploaded }: { onUploaded?: () => void }) {
  const [uploading, setUploading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState("");
  const [drag, setDrag] = useState(false);

  const handleFile = async (file: File) => {
    setUploading(true);
    setError("");
    setSuccess(false);
    try {
      const formData = new FormData();
      formData.append("file", file);
      await api.upload("/documents", formData);
      setSuccess(true);
      onUploaded?.();
      setTimeout(() => setSuccess(false), 3000);
    } catch (err: any) {
      setError(err.message || "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
      onDragLeave={() => setDrag(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDrag(false);
        const file = e.dataTransfer.files[0];
        if (file) handleFile(file);
      }}
      className={`
        relative border-2 border-dashed rounded-2xl p-10 text-center transition-all
        ${drag ? "border-indigo-400 bg-indigo-50/50" : "border-zinc-200 bg-white/50"}
        ${uploading ? "opacity-60 pointer-events-none" : ""}
      `}
    >
      <input
        type="file"
        accept=".pdf,.docx,.xlsx,.pptx,.txt,.md,.html,.xml"
        className="absolute inset-0 opacity-0 cursor-pointer"
        disabled={uploading}
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) handleFile(file);
        }}
      />

      {success ? (
        <div className="text-emerald-600 animate-fade-in">
          <CheckCircle className="w-10 h-10 mx-auto mb-2" />
          <p className="font-medium">Upload successful</p>
        </div>
      ) : uploading ? (
        <div className="text-indigo-600">
          <div className="w-10 h-10 mx-auto mb-2 border-2 border-indigo-200 border-t-indigo-600 rounded-full animate-spin" />
          <p className="font-medium">Uploading...</p>
        </div>
      ) : (
        <>
          <Upload className="w-10 h-10 text-zinc-400 mx-auto mb-3" />
          <p className="text-zinc-700 font-medium">Drop your document here</p>
          <p className="text-sm text-zinc-500 mt-1">or click to browse</p>
          <p className="text-xs text-zinc-400 mt-4">PDF, DOCX, XLSX, PPTX, TXT, MD, HTML, XML</p>
        </>
      )}

      {error && (
        <div className="mt-4 bg-red-50 border border-red-200 rounded-lg px-3 py-2 max-w-md mx-auto">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}
    </div>
  );
}
