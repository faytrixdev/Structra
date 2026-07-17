"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";

export function Navbar() {
  const router = useRouter();
  const handleLogout = () => { api.clearToken(); router.push("/login"); };

  return (
    <nav className="border-b border-zinc-800 bg-zinc-950 px-6 py-3 flex items-center justify-between">
      <div className="flex items-center gap-6">
        <Link href="/dashboard" className="text-xl font-bold text-white">Structra</Link>
        <Link href="/documents" className="text-sm text-zinc-400 hover:text-white transition-colors">Documents</Link>
        <Link href="/knowledge" className="text-sm text-zinc-400 hover:text-white transition-colors">Knowledge</Link>
        <Link href="/search" className="text-sm text-zinc-400 hover:text-white transition-colors">Search</Link>
      </div>
      <Button variant="ghost" onClick={handleLogout} className="text-zinc-400 hover:text-white">Logout</Button>
    </nav>
  );
}
