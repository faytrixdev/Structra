"use client";
import { Navbar } from "@/components/Navbar";
import { SemanticSearch } from "@/components/SemanticSearch";

export default function SearchPage() {
  return (
    <div className="min-h-screen bg-zinc-950">
      <Navbar />
      <main className="p-6 space-y-6">
        <h1 className="text-2xl font-bold">Semantic Search</h1>
        <SemanticSearch />
      </main>
    </div>
  );
}
