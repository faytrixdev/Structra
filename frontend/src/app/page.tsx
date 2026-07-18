"use client";
import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function HomePage() {
  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <div className="text-center max-w-xl animate-fade-in">
        <div className="inline-flex w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 items-center justify-center mb-6 shadow-xl">
          <span className="text-white font-bold text-3xl">S</span>
        </div>
        <h1 className="text-5xl md:text-6xl font-bold text-zinc-900 mb-4">
          <span className="text-gradient">Structra</span>
        </h1>
        <p className="text-xl text-zinc-500 mb-10 leading-relaxed">
          Transform unstructured documents into<br />
          structured, AI-ready knowledge bases.
        </p>
        <div className="flex gap-4 justify-center">
          <Link href="/login">
            <Button className="bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white shadow-lg px-8 h-12 text-base">
              Sign in
            </Button>
          </Link>
          <Link href="/register">
            <Button variant="outline" className="border-zinc-200 text-zinc-700 hover:bg-zinc-50 px-8 h-12 text-base">
              Create account
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}
