"use client";
import { FileText, Brain, Sparkles } from "lucide-react";

interface DashboardStatsProps {
  documents: number;
  knowledge: number;
  processed: number;
}

export function DashboardStats({ documents, knowledge, processed }: DashboardStatsProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 animate-fade-in">
      <StatCard icon={<FileText className="w-5 h-5" />} label="Documents" value={documents} gradient="from-blue-500 to-cyan-500" />
      <StatCard icon={<Brain className="w-5 h-5" />} label="Knowledge units" value={knowledge} gradient="from-purple-500 to-pink-500" />
      <StatCard icon={<Sparkles className="w-5 h-5" />} label="Processed" value={processed} gradient="from-emerald-500 to-teal-500" />
    </div>
  );
}

function StatCard({ icon, label, value, gradient }: any) {
  return (
    <div className="bg-white/80 backdrop-blur rounded-2xl border border-zinc-200/60 p-6 shadow-sm card-hover">
      <div className="flex items-center gap-3">
        <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${gradient} flex items-center justify-center text-white shadow-md`}>
          {icon}
        </div>
        <p className="text-sm font-medium text-zinc-500">{label}</p>
      </div>
      <p className="text-4xl font-bold text-zinc-900 mt-4">{value}</p>
    </div>
  );
}
