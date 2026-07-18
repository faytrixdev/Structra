"use client";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useRef, useEffect } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Network } from "lucide-react";

export function KnowledgeGraph() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const { data: graphData, isLoading } = useQuery({
    queryKey: ["knowledge-graph"],
    queryFn: () => api.get<any>("/knowledge/graph"),
  });

  useEffect(() => {
    if (!graphData?.data || !canvasRef.current) return;
    const { nodes, edges } = graphData.data;
    if (!nodes || nodes.length === 0) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    canvas.width = canvas.offsetWidth * dpr;
    canvas.height = 500 * dpr;
    ctx.scale(dpr, dpr);

    const centerX = canvas.offsetWidth / 2;
    const centerY = 250;
    const radius = Math.min(200, centerX - 60);

    const positions: Record<string, { x: number; y: number }> = {};
    nodes.forEach((n: any, i: number) => {
      const angle = (2 * Math.PI * i) / nodes.length - Math.PI / 2;
      positions[n.id] = {
        x: centerX + radius * Math.cos(angle),
        y: centerY + radius * Math.sin(angle),
      };
    });

    ctx.clearRect(0, 0, canvas.offsetWidth, 500);

    // Draw edges
    edges.forEach((e: any) => {
      const src = positions[e.source];
      const tgt = positions[e.target];
      if (src && tgt) {
        ctx.beginPath();
        ctx.moveTo(src.x, src.y);
        ctx.lineTo(tgt.x, tgt.y);
        ctx.strokeStyle = "rgba(99, 102, 241, 0.15)";
        ctx.lineWidth = 1;
        ctx.stroke();
      }
    });

    // Draw nodes
    nodes.forEach((n: any) => {
      const pos = positions[n.id];
      if (!pos) return;

      const confidence = n.confidence || 0.5;
      const size = 4 + confidence * 6;

      // Glow
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, size + 4, 0, 2 * Math.PI);
      ctx.fillStyle = confidence > 0.8 ? "rgba(16,185,129,0.1)" : "rgba(234,179,8,0.1)";
      ctx.fill();

      // Node
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, size, 0, 2 * Math.PI);
      ctx.fillStyle = confidence > 0.8 ? "#10b981" : "#eab308";
      ctx.fill();

      // Label
      ctx.fillStyle = "#71717a";
      ctx.font = "11px Inter, sans-serif";
      ctx.textAlign = "left";
      const label = n.label.length > 30 ? n.label.substring(0, 30) + "..." : n.label;
      ctx.fillText(label, pos.x + size + 6, pos.y + 4);
    });
  }, [graphData]);

  const nodes = graphData?.data?.nodes || [];

  return (
    <Card className="bg-white/80 backdrop-blur border-zinc-200/60">
      <CardContent className="p-6">
        {isLoading ? (
          <div className="h-[500px] bg-zinc-50 rounded-xl animate-pulse" />
        ) : nodes.length === 0 ? (
          <div className="h-[500px] flex flex-col items-center justify-center text-zinc-400">
            <Network className="w-12 h-12 mb-3" />
            <p>No knowledge graph data yet.</p>
          </div>
        ) : (
          <canvas ref={canvasRef} style={{ width: "100%", height: "500px" }} className="rounded-xl" />
        )}
      </CardContent>
    </Card>
  );
}
