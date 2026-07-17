"use client";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Navbar } from "@/components/Navbar";
import { KnowledgeCard } from "@/components/KnowledgeCard";
import { KnowledgeFilters } from "@/components/KnowledgeFilters";
import { KnowledgeGraph } from "@/components/KnowledgeGraph";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

export default function KnowledgePage() {
  const [typeFilter, setTypeFilter] = useState("");
  const [search, setSearch] = useState("");

  const { data: knowledgeData } = useQuery({
    queryKey: ["knowledge", typeFilter],
    queryFn: () => api.get<any>(`/knowledge${typeFilter && typeFilter !== "all" ? `?type=${typeFilter}` : ""}`),
  });

  const knowledge = knowledgeData?.data || [];
  const filtered = search
    ? knowledge.filter((k: any) => k.statement.toLowerCase().includes(search.toLowerCase()))
    : knowledge;

  return (
    <div className="min-h-screen bg-zinc-950">
      <Navbar />
      <main className="p-6 space-y-6">
        <h1 className="text-2xl font-bold">Knowledge Explorer</h1>
        <Tabs defaultValue="list">
          <TabsList className="bg-zinc-900">
            <TabsTrigger value="list">List</TabsTrigger>
            <TabsTrigger value="graph">Graph</TabsTrigger>
          </TabsList>
          <TabsContent value="list" className="space-y-4">
            <KnowledgeFilters onTypeChange={setTypeFilter} onSearchChange={setSearch} />
            <div className="grid gap-3">
              {filtered.map((k: any) => <KnowledgeCard key={k.id} knowledge={k} />)}
              {filtered.length === 0 && <p className="text-zinc-500">No knowledge found.</p>}
            </div>
          </TabsContent>
          <TabsContent value="graph">
            <KnowledgeGraph />
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}
