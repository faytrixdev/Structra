"use client";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Navbar } from "@/components/Navbar";
import { KnowledgeCard } from "@/components/KnowledgeCard";
import { KnowledgeFilters } from "@/components/KnowledgeFilters";
import { KnowledgeGraph } from "@/components/KnowledgeGraph";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent } from "@/components/ui/card";
import { KnowledgeCardSkeleton } from "@/components/Skeleton";
import { Brain, Network } from "lucide-react";

export default function KnowledgePage() {
  const [typeFilter, setTypeFilter] = useState("");
  const [search, setSearch] = useState("");

  const { data: knowledgeData, isLoading: knowledgeLoading } = useQuery({
    queryKey: ["knowledge", typeFilter],
    queryFn: () => api.get<any>(`/knowledge${typeFilter && typeFilter !== "all" ? `?type=${typeFilter}` : ""}`),
  });

  const knowledge = knowledgeData?.data || [];
  const filtered = search
    ? knowledge.filter((k: any) => k.statement.toLowerCase().includes(search.toLowerCase()))
    : knowledge;

  return (
    <div className="min-h-screen">
      <Navbar />
      <main className="max-w-7xl mx-auto px-6 py-10 space-y-10">
        <div className="animate-fade-in">
          <h1 className="text-3xl font-bold text-zinc-900">Knowledge Explorer</h1>
          <p className="text-zinc-500 mt-1">{knowledge.length} knowledge units extracted</p>
        </div>

        <Tabs defaultValue="list" className="space-y-6">
          <TabsList className="bg-white/80 backdrop-blur border border-zinc-200/60 p-1 rounded-xl">
            <TabsTrigger value="list" className="rounded-lg data-[state=active]:bg-zinc-900 data-[state=active]:text-white">
              <Brain className="w-4 h-4 mr-2" /> List
            </TabsTrigger>
            <TabsTrigger value="graph" className="rounded-lg data-[state=active]:bg-zinc-900 data-[state=active]:text-white">
              <Network className="w-4 h-4 mr-2" /> Graph
            </TabsTrigger>
          </TabsList>

          <TabsContent value="list" className="space-y-4">
            <KnowledgeFilters activeType={typeFilter} onTypeChange={setTypeFilter} onSearchChange={setSearch} />
            {knowledgeLoading ? (
              <div className="space-y-6">
                <KnowledgeCardSkeleton />
                <KnowledgeCardSkeleton />
                <KnowledgeCardSkeleton />
              </div>
            ) : (
              <div className="space-y-6">
                {filtered.map((k: any) => <KnowledgeCard key={k.id} knowledge={k} />)}
                {filtered.length === 0 && (
                  <Card className="bg-white/80 backdrop-blur border-zinc-200/60">
                    <CardContent className="p-10 text-center">
                      <Brain className="w-10 h-10 text-zinc-300 mx-auto mb-3" />
                      <p className="text-zinc-500">No knowledge found.</p>
                    </CardContent>
                  </Card>
                )}
              </div>
            )}
          </TabsContent>

          <TabsContent value="graph">
            <KnowledgeGraph />
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}
