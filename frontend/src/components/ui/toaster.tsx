"use client"

import { useToast } from "@/components/ui/use-toast"

export function Toaster() {
  const { toasts } = useToast()

  return (
    <div className="fixed bottom-4 right-4 z-[100] flex flex-col gap-2">
      {toasts.map((t) => (
        <div
          key={t.id}
          className={`rounded-md border p-4 shadow-lg bg-zinc-900 border-zinc-800 text-sm ${
            t.variant === "destructive" ? "border-red-800 text-red-200" : ""
          }`}
        >
          {t.title && <p className="font-medium">{t.title}</p>}
          {t.description && <p className="text-zinc-400 mt-1">{t.description}</p>}
        </div>
      ))}
    </div>
  )
}
