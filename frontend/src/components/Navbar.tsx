"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";

export function Navbar() {
  const router = useRouter();
  const handleLogout = () => { api.clearToken(); router.push("/login"); };

  return (
    <nav className="sticky top-0 z-50 glass border-b border-zinc-200/60">
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        <div className="flex items-center gap-8">
          <Link href="/dashboard" className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
              <span className="text-white font-bold text-sm">S</span>
            </div>
            <span className="text-lg font-bold text-gradient">Structra</span>
          </Link>
          <div className="hidden md:flex items-center gap-1">
            <NavLink href="/dashboard">Dashboard</NavLink>
            <NavLink href="/documents">Documents</NavLink>
            <NavLink href="/knowledge">Knowledge</NavLink>
            <NavLink href="/search">Search</NavLink>
          </div>
        </div>
        <Button variant="ghost" onClick={handleLogout} className="text-zinc-600 hover:text-zinc-900">
          Logout
        </Button>
      </div>
    </nav>
  );
}

function NavLink({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <Link
      href={href}
      className="px-3 py-1.5 text-sm font-medium text-zinc-600 rounded-md hover:text-zinc-900 hover:bg-zinc-100/80 transition-colors"
    >
      {children}
    </Link>
  );
}
