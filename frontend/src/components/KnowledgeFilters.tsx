"use client";
import { Input } from "@/components/ui/input";
import { Search } from "lucide-react";

const types = ["All", "Rule", "Definition", "Procedure", "Decision", "Workflow", "Responsibility", "Constraint", "Exception", "Requirement", "Policy", "Concept"];

export function KnowledgeFilters({ activeType, onTypeChange, onSearchChange }: { activeType: string; onTypeChange: (t: string) => void; onSearchChange: (s: string) => void }) {
  return (
    <div className="flex flex-col sm:flex-row gap-3">
      <div className="relative flex-1">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
        <Input
          placeholder="Search knowledge..."
          onChange={(e) => onSearchChange(e.target.value)}
          className="bg-white border-zinc-200 focus:border-indigo-400 focus:ring-indigo-100 pl-10"
        />
      </div>
      <div className="flex gap-1.5 overflow-x-auto pb-1">
        {types.map((t) => {
          const value = t === "All" ? "" : t;
          const isActive = activeType === value;
          return (
            <button
              key={t}
              onClick={() => onTypeChange(value)}
              className={`px-3 py-1.5 text-sm font-medium rounded-full whitespace-nowrap transition-all ${
                isActive
                  ? "bg-zinc-900 text-white shadow-sm"
                  : "bg-zinc-100 text-zinc-600 hover:bg-zinc-200"
              }`}
            >
              {t}
            </button>
          );
        })}
      </div>
    </div>
  );
}
