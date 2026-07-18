"use client";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { KnowledgeCard } from "@/components/KnowledgeCard";
import { Card, CardContent } from "@/components/ui/card";
import { Search, Sparkles } from "lucide-react";

export function SemanticSearch() {
  const [query, setQuery] = useState("");
  const [searchQuery, setSearchQuery] = useState("");

  const { data: results, isFetching } = useQuery({
    queryKey: ["semantic-search", searchQuery],
    queryFn: () => api.get<any>(`/search?q=${encodeURIComponent(searchQuery)}`),
    enabled: !!searchQuery,
  });

  const handleSearch = () => {
    if (query.trim()) setSearchQuery(query.trim());
  };

  return (
    <div className="space-y-6">
      <div className="flex gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
          <Input
            placeholder="Search knowledge semantically..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            className="bg-white border-zinc-200 focus:border-indigo-400 focus:ring-indigo-100 pl-10"
          />
        </div>
        <Button
          onClick={handleSearch}
          disabled={!query.trim() || isFetching}
          className="bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white shadow-md"
        >
          {isFetching ? "Searching..." : "Search"}
        </Button>
      </div>

      {results?.data && (
        <div className="space-y-4 animate-fade-in">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-indigo-500" />
            <p className="text-sm text-zinc-500">
              {results.data.total} result{results.data.total !== 1 ? "s" : ""} for &ldquo;{results.data.query}&rdquo;
            </p>
          </div>
          <div className="space-y-3">
            {results.data.knowledge?.map((k: any) => (
              <KnowledgeCard key={k.id} knowledge={k} />
            ))}
          </div>
          {results.data.knowledge?.length === 0 && (
            <Card className="bg-white/80 backdrop-blur border-zinc-200/60">
              <CardContent className="p-10 text-center">
                <Search className="w-10 h-10 text-zinc-300 mx-auto mb-3" />
                <p className="text-zinc-500">No results found.</p>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}
