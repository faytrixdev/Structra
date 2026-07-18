"use client";
export function Skeleton({ className = "" }: { className?: string }) {
  return <div className={`bg-zinc-100 rounded-md animate-pulse ${className}`} />;
}

export function StatCardSkeleton() {
  return (
    <div className="bg-white/80 backdrop-blur rounded-2xl border border-zinc-200/60 p-6 shadow-sm">
      <div className="flex items-center gap-3">
        <Skeleton className="w-10 h-10 rounded-lg" />
        <Skeleton className="h-4 w-24" />
      </div>
      <Skeleton className="h-10 w-16 mt-4" />
    </div>
  );
}

export function KnowledgeCardSkeleton() {
  return (
    <div className="bg-white/80 backdrop-blur rounded-2xl border border-zinc-200/60 p-5">
      <div className="flex items-start justify-between">
        <div className="flex-1 space-y-2">
          <Skeleton className="h-5 w-16" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-3/4" />
        </div>
        <Skeleton className="h-5 w-10" />
      </div>
    </div>
  );
}

export function DocumentRowSkeleton() {
  return (
    <div className="bg-white/80 backdrop-blur rounded-2xl border border-zinc-200/60 p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Skeleton className="w-11 h-11 rounded-xl" />
          <div className="space-y-2">
            <Skeleton className="h-4 w-48" />
            <Skeleton className="h-3 w-32" />
          </div>
        </div>
        <Skeleton className="h-6 w-16 rounded-full" />
      </div>
    </div>
  );
}
