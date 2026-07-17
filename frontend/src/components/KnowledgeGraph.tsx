"use client";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useRef, useEffect } from "react";

export function KnowledgeGraph() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const { data: graphData, isLoading } = useQuery({
    queryKey: ["knowledge-graph"],
    queryFn: () => api.get<any>("/knowledge/graph"),
  });

  useEffect(() => {
    if (!graphData?.data || !canvasRef.current) return;
    const { nodes, edges } = graphData.data;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    canvas.width = canvas.offsetWidth * 2;
    canvas.height = 500 * 2;
    ctx.scale(2, 2);

    const positions: Record<string, { x: number; y: number }> = {};
    const centerX = canvas.offsetWidth / 2;
    const centerY = 250;

    nodes.forEach((n: any, i: number) => {
      const angle = (2 * Math.PI * i) / nodes.length;
      positions[n.id] = { x: centerX + 200 * Math.cos(angle), y: centerY + 200 * Math.sin(angle) };
    });

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    edges.forEach((e: any) => {
      const src = positions[e.source];
      const tgt = positions[e.target];
      if (src && tgt) {
        ctx.beginPath();
        ctx.moveTo(src.x, src.y);
        ctx.lineTo(tgt.x, tgt.y);
        ctx.strokeStyle = "rgba(99, 102, 241, 0.3)";
        ctx.lineWidth = 1;
        ctx.stroke();
      }
    });

    nodes.forEach((n: any) => {
      const pos = positions[n.id];
      if (!pos) return;
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, 6, 0, 2 * Math.PI);
      ctx.fillStyle = n.confidence > 0.8 ? "#22c55e" : "#eab308";
      ctx.fill();
      ctx.fillStyle = "#a1a1aa";
      ctx.font = "10px sans-serif";
      ctx.fillText(n.label.substring(0, 30), pos.x + 10, pos.y + 4);
    });
  }, [graphData]);

  if (isLoading) return <p className="text-zinc-500">Loading graph...</p>;

  return (
    <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-4">
      <canvas ref={canvasRef} style={{ width: "100%", height: "500px" }} />
      {(!graphData?.data?.nodes || graphData.data.nodes.length === 0) && (
        <p className="text-zinc-500 text-center py-20">No knowledge graph data yet.</p>
      )}
    </div>
  );
}
