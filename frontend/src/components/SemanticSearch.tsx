"use client";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { KnowledgeCard } from "@/components/KnowledgeCard";

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
        <Input
          placeholder="Search knowledge semantically..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSearch()}
          className="bg-zinc-800 border-zinc-700"
        />
        <Button onClick={handleSearch} disabled={!query.trim() || isFetching}>
          {isFetching ? "Searching..." : "Search"}
        </Button>
      </div>

      {results?.data && (
        <div className="space-y-3">
          <p className="text-sm text-zinc-400">
            {results.data.total} result{results.data.total !== 1 ? "s" : ""} for &ldquo;{results.data.query}&rdquo;
          </p>
          {results.data.knowledge?.map((k: any) => (
            <KnowledgeCard key={k.id} knowledge={k} />
          ))}
          {results.data.knowledge?.length === 0 && (
            <p className="text-zinc-500">No results found.</p>
          )}
        </div>
      )}
    </div>
  );
}
