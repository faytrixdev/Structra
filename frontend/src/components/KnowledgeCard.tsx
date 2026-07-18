"use client";
import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";

const typeColor: Record<string, string> = {
  Rule: "bg-blue-50 text-blue-700 border-blue-200",
  Definition: "bg-emerald-50 text-emerald-700 border-emerald-200",
  Procedure: "bg-amber-50 text-amber-700 border-amber-200",
  Responsibility: "bg-purple-50 text-purple-700 border-purple-200",
  Constraint: "bg-red-50 text-red-700 border-red-200",
  Exception: "bg-orange-50 text-orange-700 border-orange-200",
  Requirement: "bg-cyan-50 text-cyan-700 border-cyan-200",
  Policy: "bg-pink-50 text-pink-700 border-pink-200",
  Concept: "bg-violet-50 text-violet-700 border-violet-200",
};

export function KnowledgeCard({ knowledge }: { knowledge: any }) {
  return (
    <Link href={`/knowledge/${knowledge.id}`} className="block">
      <Card className="bg-white/80 backdrop-blur border-zinc-200/60 card-hover cursor-pointer">
        <CardContent className="p-6">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <span className={`text-xs font-medium px-2.5 py-1 rounded-full border ${typeColor[knowledge.type] || "bg-zinc-50 text-zinc-600 border-zinc-200"}`}>
                {knowledge.type}
              </span>
              <p className="text-zinc-900 font-medium mt-2 line-clamp-3">{knowledge.statement}</p>
            </div>
            <span className="text-sm font-semibold text-zinc-500 shrink-0 ml-4">
              {Math.round(knowledge.confidence * 100)}%
            </span>
          </div>
          {knowledge.entities?.length > 0 && (
            <div className="flex gap-1.5 mt-3 flex-wrap">
              {knowledge.entities.slice(0, 4).map((e: any, i: number) => (
                <span key={i} className="text-xs px-2 py-0.5 rounded-md bg-zinc-50 text-zinc-500 border border-zinc-100">
                  {e.value}
                </span>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </Link>
  );
}
