"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function RegisterPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [orgName, setOrgName] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res: any = await api.post("/auth/register", { email, password, name, organization_name: orgName });
      api.setToken(res.data.token);
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message || "Registration failed");
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen">
      <Card className="w-[400px] bg-zinc-900 border-zinc-800">
        <CardHeader>
          <CardTitle className="text-2xl font-bold">Create Account</CardTitle>
          <CardDescription>Join Structra</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-sm text-zinc-400">Name</label>
              <Input value={name} onChange={(e) => setName(e.target.value)} required className="bg-zinc-800 border-zinc-700" />
            </div>
            <div>
              <label className="text-sm text-zinc-400">Email</label>
              <Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required className="bg-zinc-800 border-zinc-700" />
            </div>
            <div>
              <label className="text-sm text-zinc-400">Password</label>
              <Input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required className="bg-zinc-800 border-zinc-700" />
            </div>
            <div>
              <label className="text-sm text-zinc-400">Organization</label>
              <Input value={orgName} onChange={(e) => setOrgName(e.target.value)} required className="bg-zinc-800 border-zinc-700" />
            </div>
            {error && <p className="text-red-400 text-sm">{error}</p>}
            <Button type="submit" className="w-full">Create Account</Button>
            <p className="text-sm text-zinc-500 text-center">
              Already have an account? <a href="/login" className="text-blue-400 hover:underline">Sign in</a>
            </p>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
