"use client";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

const types = ["All", "Rule", "Definition", "Procedure", "Decision", "Workflow", "Responsibility", "Constraint", "Exception", "Requirement", "Policy", "Concept"];

export function KnowledgeFilters({ onTypeChange, onSearchChange }: { onTypeChange: (t: string) => void; onSearchChange: (s: string) => void }) {
  return (
    <div className="flex gap-4 mb-4">
      <Input placeholder="Search knowledge..." onChange={(e) => onSearchChange(e.target.value)} className="bg-zinc-800 border-zinc-700 max-w-md" />
      <Select onValueChange={onTypeChange}>
        <SelectTrigger className="w-[180px] bg-zinc-800 border-zinc-700">
          <SelectValue placeholder="All Types" />
        </SelectTrigger>
        <SelectContent className="bg-zinc-900 border-zinc-800">
          {types.map((t) => <SelectItem key={t} value={t === "All" ? "" : t}>{t}</SelectItem>)}
        </SelectContent>
      </Select>
    </div>
  );
}
