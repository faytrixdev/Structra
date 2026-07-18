"use client";
import { Navbar } from "@/components/Navbar";
import { SemanticSearch } from "@/components/SemanticSearch";
import { Search } from "lucide-react";

export default function SearchPage() {
  return (
    <div className="min-h-screen">
      <Navbar />
      <main className="max-w-4xl mx-auto px-6 py-10 space-y-10">
        <div className="animate-fade-in">
          <h1 className="text-3xl font-bold text-zinc-900">Semantic Search</h1>
          <p className="text-zinc-500 mt-1">Find knowledge using natural language</p>
        </div>
        <SemanticSearch />
      </main>
    </div>
  );
}
