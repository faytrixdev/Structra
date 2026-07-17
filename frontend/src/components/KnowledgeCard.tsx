"use client";
import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";

const typeColors: Record<string, string> = {
  Rule: "border-l-blue-500", Definition: "border-l-green-500", Procedure: "border-l-yellow-500",
  Responsibility: "border-l-purple-500", Constraint: "border-l-red-500", Exception: "border-l-orange-500",
  Requirement: "border-l-cyan-500", Policy: "border-l-pink-500",
};

export function KnowledgeCard({ knowledge }: { knowledge: any }) {
  const borderColor = typeColors[knowledge.type] || "border-l-zinc-500";
  return (
    <Link href={`/knowledge/${knowledge.id}`}>
      <Card className={`bg-zinc-900 border-zinc-800 border-l-4 ${borderColor} hover:bg-zinc-800 transition-colors`}>
        <CardContent className="p-4">
          <div className="flex justify-between items-start mb-2">
            <span className="text-xs font-medium px-2 py-0.5 rounded bg-zinc-800 text-zinc-300">{knowledge.type}</span>
            <span className="text-xs text-zinc-500">{Math.round(knowledge.confidence * 100)}%</span>
          </div>
          <p className="text-sm">{knowledge.statement}</p>
          {knowledge.entities?.length > 0 && (
            <div className="flex gap-1 mt-2 flex-wrap">
              {knowledge.entities.map((e: any, i: number) => (
                <span key={i} className="text-xs px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-400">{e.value}</span>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </Link>
  );
}
