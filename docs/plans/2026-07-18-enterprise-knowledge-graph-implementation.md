# Enterprise Knowledge Graph Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the raw Canvas KnowledgeGraph with an enterprise-grade interactive graph using ReactFlow, ELK layout, type-based nodes/edges, clustering, search, and a details panel.

**Architecture:** Clean replacement of the existing `KnowledgeGraph.tsx` with a modular component system under `components/knowledge-graph/`. Backend gets an enhanced graph API returning typed, enriched node/edge data with cluster metadata. Frontend uses ReactFlow with custom node/edge components, ELK layout via elkjs, and a slide-in details panel.

**Tech Stack:** ReactFlow 11, elkjs, Lucide icons, Tailwind CSS, Shadcn UI, FastAPI, SQLAlchemy, Pydantic v2

---

## Task 1: Install elkjs dependency

**Files:**
- Modify: `frontend/package.json`

**Step 1: Install elkjs**

Run: `cd frontend && pnpm add elkjs @types/elkjs`

**Step 2: Verify installation**

Run: `cd frontend && pnpm ls elkjs`
Expected: `elkjs` listed with version

**Step 3: Commit**

```bash
git add frontend/package.json frontend/pnpm-lock.yaml
git commit -m "deps: add elkjs for ELK graph layout"
```

---

## Task 2: Add enhanced graph Pydantic schemas (backend)

**Files:**
- Modify: `backend/app/domain/schemas.py`

**Step 1: Add new graph response schemas**

Add after the existing `GraphResponse` class (line 66):

```python
class GraphNodeResponse(BaseModel):
    id: str
    label: str
    type: str
    confidence: float
    document_id: str
    document_title: str
    entity_count: int
    relationship_count: int
    cluster: str

class GraphEdgeResponse(BaseModel):
    id: str
    source: str
    target: str
    type: str
    confidence: float
    label: str

class ClusterInfo(BaseModel):
    name: str
    type: str
    node_count: int
    color: str

class GraphMetadata(BaseModel):
    total_nodes: int
    total_edges: int
    clusters: list[ClusterInfo]
    type_counts: dict[str, int]

class EnhancedGraphResponse(BaseModel):
    nodes: list[GraphNodeResponse]
    edges: list[GraphEdgeResponse]
    metadata: GraphMetadata
```

**Step 2: Verify schemas load**

Run: `cd backend && python -c "from app.domain.schemas import EnhancedGraphResponse; print('OK')"`
Expected: `OK`

**Step 3: Commit**

```bash
git add backend/app/domain/schemas.py
git commit -m "feat: add enhanced graph response schemas"
```

---

## Task 3: Implement enhanced graph service (backend)

**Files:**
- Modify: `backend/app/service/knowledge_service.py`

**Step 1: Add node label generator function**

Add at the top of the file, after imports:

```python
import re
from collections import Counter

NODE_TYPE_COLORS = {
    "Rule": "#EF4444", "Definition": "#6B7280", "Procedure": "#3B82F6",
    "Decision": "#EAB308", "Workflow": "#10B981", "Responsibility": "#F97316",
    "Constraint": "#EC4899", "Exception": "#6B7280", "Requirement": "#14B8A6",
    "Risk": "#DC2626", "Event": "#F59E0B", "Metric": "#6366F1",
    "KPI": "#06B6D4", "Policy": "#1E3A5F", "Concept": "#8B5CF6",
    "Obligation": "#059669", "Prohibition": "#E11D48",
}

RELATION_LABELS = {
    "depends_on": "depends on", "requires": "requires", "references": "references",
    "extends": "extends", "contradicts": "contradicts", "causes": "causes",
    "blocks": "blocks", "exception_of": "exception of", "workflow_step": "workflow step",
    "parent": "parent of", "child": "child of",
}


def _generate_node_label(statement: str, knowledge_type: str, index: int) -> str:
    if not statement:
        return f"{knowledge_type} #{index}"
    sentence = statement.strip()
    sentence = re.sub(r'^(the|a|an|les|le|la|un|une|des)\s+', '', sentence, flags=re.IGNORECASE)
    sentence = re.sub(r'^(il|elle|ils|elles|on|we|they|he|she|it)\s+', '', sentence, flags=re.IGNORECASE)
    words = sentence.split()[:5]
    label = " ".join(words)
    if len(label) > 40:
        label = label[:37] + "..."
    return label if label else f"{knowledge_type} #{index}"
```

**Step 2: Replace get_knowledge_graph function**

Replace the existing `get_knowledge_graph` function (lines 22-29) with:

```python
def get_knowledge_graph(db: Session, organization_id: str) -> dict:
    knowledge_list = db.query(KnowledgeObject).filter(
        KnowledgeObject.organization_id == organization_id
    ).all()
    
    if not knowledge_list:
        return {
            "nodes": [], "edges": [],
            "metadata": {
                "total_nodes": 0, "total_edges": 0,
                "clusters": [], "type_counts": {},
            }
        }

    knowledge_ids = [k.id for k in knowledge_list]
    relations = db.query(KnowledgeRelation).filter(
        KnowledgeRelation.source_id.in_(knowledge_ids)
    ).all() if knowledge_list else []

    type_counts = Counter(k.type for k in knowledge_list)

    nodes = []
    for i, k in enumerate(knowledge_list):
        entity_count = len(k.entities) if hasattr(k, 'entities') else 0
        rel_count = len(k.source_relations) + len(k.target_relations) if hasattr(k, 'source_relations') else 0
        doc_title = k.document.title if hasattr(k, 'document') and k.document else ""
        nodes.append({
            "id": str(k.id),
            "label": _generate_node_label(k.statement, k.type, i + 1),
            "type": k.type,
            "confidence": k.confidence or 0.0,
            "document_id": str(k.document_id),
            "document_title": doc_title,
            "entity_count": entity_count,
            "relationship_count": rel_count,
            "cluster": k.type,
        })

    edges = []
    for r in relations:
        rel_label = RELATION_LABELS.get(r.relation_type, r.relation_type.replace("_", " "))
        edges.append({
            "id": str(r.id),
            "source": str(r.source_id),
            "target": str(r.target_id),
            "type": r.relation_type,
            "confidence": r.confidence or 0.0,
            "label": rel_label,
        })

    clusters = [
        {
            "name": f"{t}s" if not t.endswith("s") else t,
            "type": t,
            "node_count": count,
            "color": NODE_TYPE_COLORS.get(t, "#6B7280"),
        }
        for t, count in type_counts.items()
    ]

    return {
        "nodes": nodes,
        "edges": edges,
        "metadata": {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "clusters": clusters,
            "type_counts": dict(type_counts),
        },
    }
```

**Step 3: Verify syntax**

Run: `cd backend && python -c "from app.service.knowledge_service import get_knowledge_graph; print('OK')"`
Expected: `OK`

**Step 4: Commit**

```bash
git add backend/app/service/knowledge_service.py
git commit -m "feat: enhance graph API with typed nodes, edges, clusters, and short labels"
```

---

## Task 4: Update API endpoint to use enhanced response (backend)

**Files:**
- Modify: `backend/app/api/v1/knowledge.py`

**Step 1: Update the graph endpoint**

Replace the `knowledge_graph` function (lines 24-28) with:

```python
@router.get("/graph")
async def knowledge_graph(user=Depends(get_current_user), db: Session = Depends(get_db)):
    _, org_id = user
    graph = get_knowledge_graph(db, org_id)
    return APIResponse(data=graph)
```

(This is actually the same — the service now returns the enhanced format, and we pass it through as `data`.)

**Step 2: Verify the endpoint loads**

Run: `cd backend && python -c "from app.api.v1.knowledge import router; print('OK')"`
Expected: `OK`

**Step 3: Commit**

```bash
git add backend/app/api/v1/knowledge.py
git commit -m "feat: wire enhanced graph API endpoint"
```

---

## Task 5: Update frontend TypeScript types

**Files:**
- Modify: `frontend/src/types/index.ts`

**Step 1: Replace GraphNode and GraphEdge interfaces**

Replace lines 20-21 with:

```typescript
export interface GraphNode {
  id: string;
  label: string;
  type: string;
  confidence: number;
  document_id: string;
  document_title: string;
  entity_count: number;
  relationship_count: number;
  cluster: string;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  type: string;
  confidence: number;
  label: string;
}

export interface ClusterInfo {
  name: string;
  type: string;
  node_count: number;
  color: string;
}

export interface GraphMetadata {
  total_nodes: number;
  total_edges: number;
  clusters: ClusterInfo[];
  type_counts: Record<string, number>;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
  metadata: GraphMetadata;
}
```

**Step 2: Commit**

```bash
git add frontend/src/types/index.ts
git commit -m "feat: add enhanced graph TypeScript types"
```

---

## Task 6: Create graph constants (colors, icons, type mappings)

**Files:**
- Create: `frontend/src/components/knowledge-graph/constants.ts`

**Step 1: Create constants file**

```typescript
import {
  Shield, ListOrdered, Lightbulb, GitBranch, Users, GitCommit,
  CheckCircle, Lock, AlertTriangle, AlertOctagon, BarChart2,
  TrendingUp, BookOpen, Calendar, ShieldCheck, Ban,
} from "lucide-react";

export const NODE_TYPE_CONFIG: Record<string, { color: string; bgColor: string; icon: typeof Shield; label: string }> = {
  Rule:          { color: "#EF4444", bgColor: "#FEF2F2", icon: Shield,         label: "Rules" },
  Definition:    { color: "#6B7280", bgColor: "#F9FAFB", icon: BookOpen,        label: "Definitions" },
  Procedure:     { color: "#3B82F6", bgColor: "#EFF6FF", icon: ListOrdered,    label: "Procedures" },
  Decision:      { color: "#EAB308", bgColor: "#FEFCE8", icon: GitCommit,      label: "Decisions" },
  Workflow:      { color: "#10B981", bgColor: "#ECFDF5", icon: GitBranch,      label: "Workflows" },
  Responsibility:{ color: "#F97316", bgColor: "#FFF7ED", icon: Users,          label: "Responsibilities" },
  Constraint:    { color: "#EC4899", bgColor: "#FDF2F8", icon: Lock,           label: "Constraints" },
  Exception:     { color: "#6B7280", bgColor: "#F9FAFB", icon: AlertTriangle,  label: "Exceptions" },
  Requirement:   { color: "#14B8A6", bgColor: "#F0FDFA", icon: CheckCircle,    label: "Requirements" },
  Risk:          { color: "#DC2626", bgColor: "#FEF2F2", icon: AlertOctagon,   label: "Risks" },
  Event:         { color: "#F59E0B", bgColor: "#FFFBEB", icon: Calendar,       label: "Events" },
  Metric:        { color: "#6366F1", bgColor: "#EEF2FF", icon: TrendingUp,     label: "Metrics" },
  KPI:           { color: "#06B6D4", bgColor: "#ECFEFF", icon: BarChart2,      label: "KPIs" },
  Policy:        { color: "#1E3A5F", bgColor: "#EFF6FF", icon: BookOpen,       label: "Policies" },
  Concept:       { color: "#8B5CF6", bgColor: "#F5F3FF", icon: Lightbulb,      label: "Concepts" },
  Obligation:    { color: "#059669", bgColor: "#ECFDF5", icon: ShieldCheck,    label: "Obligations" },
  Prohibition:   { color: "#E11D48", bgColor: "#FFF1F2", icon: Ban,            label: "Prohibitions" },
};

export const EDGE_TYPE_CONFIG: Record<string, { color: string; label: string }> = {
  depends_on:     { color: "#6366F1", label: "depends on" },
  requires:       { color: "#EF4444", label: "requires" },
  references:     { color: "#6B7280", label: "references" },
  extends:        { color: "#10B981", label: "extends" },
  contradicts:    { color: "#E11D48", label: "contradicts" },
  causes:         { color: "#F97316", label: "causes" },
  blocks:         { color: "#DC2626", label: "blocks" },
  exception_of:   { color: "#6B7280", label: "exception of" },
  workflow_step:  { color: "#14B8A6", label: "workflow step" },
  parent:         { color: "#3B82F6", label: "parent of" },
  child:          { color: "#3B82F6", label: "child of" },
  owned_by:       { color: "#8B5CF6", label: "owned by" },
  executed_by:    { color: "#F59E0B", label: "executed by" },
  measured_by:    { color: "#06B6D4", label: "measured by" },
  validates:      { color: "#059669", label: "validates" },
  triggers:       { color: "#EC4899", label: "triggers" },
  affects:        { color: "#6366F1", label: "affects" },
};
```

**Step 2: Commit**

```bash
git add frontend/src/components/knowledge-graph/constants.ts
git commit -m "feat: add graph node/edge type color and icon constants"
```

---

## Task 7: Create useGraphData hook

**Files:**
- Create: `frontend/src/components/knowledge-graph/hooks/useGraphData.ts`

**Step 1: Create the hook**

```typescript
"use client";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { GraphData } from "@/types";

interface GraphAPIResponse {
  status: string;
  data: GraphData;
}

export function useGraphData() {
  return useQuery<GraphAPIResponse>({
    queryKey: ["knowledge-graph"],
    queryFn: () => api.get<GraphAPIResponse>("/knowledge/graph"),
    staleTime: 30_000,
  });
}
```

**Step 2: Commit**

```bash
git add frontend/src/components/knowledge-graph/hooks/useGraphData.ts
git commit -m "feat: add useGraphData hook for fetching graph data"
```

---

## Task 8: Create useGraphLayout hook (ELK integration)

**Files:**
- Create: `frontend/src/components/knowledge-graph/hooks/useGraphLayout.ts`

**Step 1: Create the ELK layout hook**

```typescript
"use client";
import { useCallback, useState } from "react";
import ELK from "elkjs";
import type { GraphNode, GraphEdge } from "@/types";
import type { Node, Edge } from "reactflow";

const elk = new ELK();

const ELK_OPTIONS = {
  "elk.algorithm": "layered",
  "elk.direction": "DOWN",
  "elk.layered.spacing.nodeNodeBetweenLayers": "100",
  "elk.spacing.nodeNode": "80",
  "elk.layered.edgeRouting": "POLYLINE",
  "elk.layered.mergeEdges": "true",
  "elk.layered.nodePlacement": "BRANDES_KOEPF",
};

function getSpacing(nodeCount: number) {
  if (nodeCount > 200) return { h: 40, v: 80 };
  if (nodeCount > 50) return { h: 60, v: 100 };
  return { h: 80, v: 120 };
}

export function useGraphLayout() {
  const [isLayouting, setIsLayouting] = useState(false);

  const applyLayout = useCallback(async (
    nodes: GraphNode[],
    edges: GraphEdge[]
  ): Promise<{ nodes: Node[]; edges: Edge[] }> => {
    if (nodes.length === 0) return { nodes: [], edges: [] };

    setIsLayouting(true);
    const spacing = getSpacing(nodes.length);

    const elkNodes = nodes.map((n) => ({
      id: n.id,
      width: 200,
      height: 60,
    }));

    const elkEdges = edges.map((e) => ({
      id: e.id,
      sources: [e.source],
      targets: [e.target],
    }));

    const graph = {
      id: "root",
      children: elkNodes,
      edges: elkEdges,
      layoutOptions: {
        ...ELK_OPTIONS,
        "elk.layered.spacing.nodeNodeBetweenLayers": String(spacing.v),
        "elk.spacing.nodeNode": String(spacing.h),
      },
    };

    try {
      const layouted = await elk.layout(graph);

      const positionedNodes: Node[] = nodes.map((n) => {
        const elkNode = layouted.children?.find((c) => c.id === n.id);
        return {
          id: n.id,
          type: "knowledgeNode",
          position: {
            x: (elkNode?.x ?? 0),
            y: (elkNode?.y ?? 0),
          },
          data: n,
        };
      });

      const positionedEdges: Edge[] = edges.map((e) => ({
        id: e.id,
        source: e.source,
        target: e.target,
        type: "knowledgeEdge",
        data: e,
      }));

      return { nodes: positionedNodes, edges: positionedEdges };
    } finally {
      setIsLayouting(false);
    }
  }, []);

  return { applyLayout, isLayouting };
}
```

**Step 2: Commit**

```bash
git add frontend/src/components/knowledge-graph/hooks/useGraphLayout.ts
git commit -m "feat: add ELK layout hook for automatic graph positioning"
```

---

## Task 9: Create useGraphSearch hook

**Files:**
- Create: `frontend/src/components/knowledge-graph/hooks/useGraphSearch.ts`

**Step 1: Create the search hook**

```typescript
"use client";
import { useState, useCallback, useMemo } from "react";
import type { GraphNode } from "@/types";

export function useGraphSearch(nodes: GraphNode[]) {
  const [query, setQuery] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);

  const results = useMemo(() => {
    if (!query.trim()) return [];
    const q = query.toLowerCase();
    return nodes.filter(
      (n) =>
        n.label.toLowerCase().includes(q) ||
        n.type.toLowerCase().includes(q)
    );
  }, [query, nodes]);

  const highlightedIds = useMemo(() => {
    if (results.length === 0) return new Set<string>();
    return new Set(results.map((r) => r.id));
  }, [results]);

  const centerOnNode = useCallback((nodeId: string) => {
    const event = new CustomEvent("graph:centerOnNode", { detail: { nodeId } });
    window.dispatchEvent(event);
  }, []);

  const selectNext = useCallback(() => {
    if (results.length === 0) return;
    setSelectedIndex((i) => (i + 1) % results.length);
    centerOnNode(results[(selectedIndex + 1) % results.length].id);
  }, [results, selectedIndex, centerOnNode]);

  const clearSearch = useCallback(() => {
    setQuery("");
    setSelectedIndex(0);
  }, []);

  return {
    query,
    setQuery,
    results,
    highlightedIds,
    selectedIndex,
    selectNext,
    centerOnNode,
    clearSearch,
  };
}
```

**Step 2: Commit**

```bash
git add frontend/src/components/knowledge-graph/hooks/useGraphSearch.ts
git commit -m "feat: add useGraphSearch hook for filtering and highlighting"
```

---

## Task 10: Create KnowledgeNode component

**Files:**
- Create: `frontend/src/components/knowledge-graph/KnowledgeNode.tsx`

**Step 1: Create the custom node**

```typescript
"use client";
import { memo } from "react";
import { Handle, Position, type NodeProps } from "reactflow";
import type { GraphNode } from "@/types";
import { NODE_TYPE_CONFIG } from "./constants";

function KnowledgeNodeComponent({ data, selected }: NodeProps<GraphNode>) {
  const config = NODE_TYPE_CONFIG[data.type] || NODE_TYPE_CONFIG.Concept;
  const Icon = config.icon;
  const label = data.label.length > 30 ? data.label.substring(0, 27) + "..." : data.label;

  return (
    <div
      className="group relative"
      style={{ filter: selected ? "drop-shadow(0 0 8px rgba(99,102,241,0.4))" : "none" }}
    >
      <Handle type="target" position={Position.Top} className="!bg-transparent !border-0 !w-2 !h-2" />
      <div
        className="flex items-center gap-2.5 px-3.5 py-2.5 rounded-xl border transition-all duration-200 cursor-pointer hover:scale-105"
        style={{
          backgroundColor: config.bgColor,
          borderColor: selected ? config.color : `${config.color}33`,
          borderWidth: selected ? 2 : 1,
          minWidth: 140,
          maxWidth: 220,
        }}
      >
        <div
          className="flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center"
          style={{ backgroundColor: `${config.color}20` }}
        >
          <Icon size={16} style={{ color: config.color }} />
        </div>
        <div className="flex flex-col min-w-0">
          <span className="text-xs font-semibold text-zinc-800 truncate leading-tight">
            {label}
          </span>
          <span className="text-[10px] text-zinc-400 leading-tight">
            {config.label.replace(/s$/, "")}
          </span>
        </div>
        {data.confidence >= 0.8 && (
          <div className="flex-shrink-0 w-2 h-2 rounded-full bg-emerald-400" title="High confidence" />
        )}
      </div>
      <Handle type="source" position={Position.Bottom} className="!bg-transparent !border-0 !w-2 !h-2" />
    </div>
  );
}

export const KnowledgeNode = memo(KnowledgeNodeComponent);
```

**Step 2: Commit**

```bash
git add frontend/src/components/knowledge-graph/KnowledgeNode.tsx
git commit -m "feat: add KnowledgeNode custom ReactFlow node with type-based styling"
```

---

## Task 11: Create KnowledgeEdge component

**Files:**
- Create: `frontend/src/components/knowledge-graph/KnowledgeEdge.tsx`

**Step 1: Create the custom edge**

```typescript
"use client";
import { memo } from "react";
import { BaseEdge, EdgeLabelRenderer, getBezierPath, type EdgeProps } from "reactflow";
import type { GraphEdge } from "@/types";
import { EDGE_TYPE_CONFIG } from "./constants";

function KnowledgeEdgeComponent({
  id, sourceX, sourceY, targetX, targetY, sourcePosition, targetPosition, data, selected, style,
}: EdgeProps<GraphEdge>) {
  const config = EDGE_TYPE_CONFIG[data?.type || "references"] || { color: "#6B7280", label: "" };
  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX, sourceY, targetX, targetY, sourcePosition, targetPosition,
  });

  const label = data?.label || "";
  const showLabel = label.length > 0;

  return (
    <>
      <BaseEdge
        id={id}
        path={edgePath}
        style={{
          ...style,
          stroke: config.color,
          strokeWidth: selected ? 2.5 : 1.5,
          opacity: selected ? 1 : 0.6,
        }}
      />
      {showLabel && (
        <EdgeLabelRenderer>
          <div
            style={{
              position: "absolute",
              transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
              pointerEvents: "all",
            }}
            className="px-1.5 py-0.5 rounded bg-white/90 border border-zinc-200/60 text-[10px] font-medium text-zinc-500 shadow-sm"
          >
            {label}
          </div>
        </EdgeLabelRenderer>
      )}
    </>
  );
}

export const KnowledgeEdge = memo(KnowledgeEdgeComponent);
```

**Step 2: Commit**

```bash
git add frontend/src/components/knowledge-graph/KnowledgeEdge.tsx
git commit -m "feat: add KnowledgeEdge custom ReactFlow edge with labels"
```

---

## Task 12: Create KnowledgeDetailsPanel component

**Files:**
- Create: `frontend/src/components/knowledge-graph/KnowledgeDetailsPanel.tsx`

**Step 1: Create the details panel**

```typescript
"use client";
import { X, FileText, Users, Zap, Box, GitBranch, Clock, Shield } from "lucide-react";
import type { GraphNode } from "@/types";
import { NODE_TYPE_CONFIG } from "./constants";

interface Props {
  node: GraphNode | null;
  onClose: () => void;
}

export function KnowledgeDetailsPanel({ node, onClose }: Props) {
  if (!node) return null;

  const config = NODE_TYPE_CONFIG[node.type] || NODE_TYPE_CONFIG.Concept;
  const Icon = config.icon;

  return (
    <div className="w-[420px] h-full border-l border-zinc-200/60 bg-white flex flex-col animate-slide-in-right">
      {/* Header */}
      <div className="flex items-start gap-3 p-5 border-b border-zinc-100">
        <div
          className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
          style={{ backgroundColor: `${config.color}15` }}
        >
          <Icon size={20} style={{ color: config.color }} />
        </div>
        <div className="flex-1 min-w-0">
          <h2 className="text-base font-bold text-zinc-900 truncate">{node.label}</h2>
          <div className="flex items-center gap-2 mt-0.5">
            <span
              className="text-[10px] font-semibold px-1.5 py-0.5 rounded"
              style={{ backgroundColor: `${config.color}15`, color: config.color }}
            >
              {node.type}
            </span>
            <span className="text-[10px] text-zinc-400">
              Confidence: {Math.round(node.confidence * 100)}%
            </span>
          </div>
        </div>
        <button onClick={onClose} className="p-1 rounded-lg hover:bg-zinc-100 transition-colors">
          <X size={18} className="text-zinc-400" />
        </button>
      </div>

      {/* Body */}
      <div className="flex-1 overflow-y-auto p-5 space-y-5">
        {/* Summary */}
        <Section title="Summary" icon={<FileText size={14} />}>
          <p className="text-sm text-zinc-600 leading-relaxed">
            {node.label} — extracted from {node.document_title || "unknown document"}.
          </p>
        </Section>

        {/* Entities */}
        <Section title="Entities" icon={<Users size={14} />}>
          <div className="space-y-1.5">
            <EntityRow label="Document" value={node.document_title || "—"} />
            <EntityRow label="Entity count" value={String(node.entity_count)} />
            <EntityRow label="Relationships" value={String(node.relationship_count)} />
          </div>
        </Section>

        {/* Source */}
        <Section title="Source" icon={<Clock size={14} />}>
          <div className="space-y-1.5">
            <EntityRow label="Document" value={node.document_title || "—"} />
            <EntityRow label="Node ID" value={node.id.substring(0, 8) + "..."} />
          </div>
        </Section>

        {/* Metadata */}
        <Section title="Metadata" icon={<Shield size={14} />}>
          <div className="space-y-1.5">
            <EntityRow label="Confidence" value={`${Math.round(node.confidence * 100)}%`} />
            <EntityRow label="Cluster" value={node.cluster} />
          </div>
        </Section>
      </div>
    </div>
  );
}

function Section({ title, icon, children }: { title: string; icon: React.ReactNode; children: React.ReactNode }) {
  return (
    <div>
      <div className="flex items-center gap-1.5 mb-2">
        <span className="text-zinc-400">{icon}</span>
        <h3 className="text-xs font-bold text-zinc-500 uppercase tracking-wider">{title}</h3>
      </div>
      {children}
    </div>
  );
}

function EntityRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between text-xs">
      <span className="text-zinc-400">{label}</span>
      <span className="text-zinc-700 font-medium truncate ml-4">{value}</span>
    </div>
  );
}
```

**Step 2: Add slide-in animation to globals.css**

Read `frontend/src/app/globals.css` and add at the end:

```css
@keyframes slide-in-right {
  from { transform: translateX(100%); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}

.animate-slide-in-right {
  animation: slide-in-right 200ms ease-out;
}
```

**Step 3: Commit**

```bash
git add frontend/src/components/knowledge-graph/KnowledgeDetailsPanel.tsx frontend/src/app/globals.css
git commit -m "feat: add KnowledgeDetailsPanel with slide-in animation"
```

---

## Task 13: Create GraphToolbar component

**Files:**
- Create: `frontend/src/components/knowledge-graph/GraphToolbar.tsx`

**Step 1: Create the toolbar**

```typescript
"use client";
import { Network, Maximize2, ZoomIn, ZoomOut, RotateCcw } from "lucide-react";

interface Props {
  nodeCount: number;
  edgeCount: number;
  onFitView: () => void;
  onZoomIn: () => void;
  onZoomOut: () => void;
  onReset: () => void;
}

export function GraphToolbar({ nodeCount, edgeCount, onFitView, onZoomIn, onZoomOut, onReset }: Props) {
  return (
    <div className="flex items-center justify-between px-4 py-2.5 bg-white border-b border-zinc-200/60">
      <div className="flex items-center gap-3">
        <Network size={18} className="text-zinc-400" />
        <div>
          <h3 className="text-sm font-bold text-zinc-800">Knowledge Graph</h3>
          <p className="text-[10px] text-zinc-400">
            {nodeCount} nodes · {edgeCount} edges
          </p>
        </div>
      </div>
      <div className="flex items-center gap-1">
        <ToolbarButton icon={<ZoomIn size={14} />} onClick={onZoomIn} tooltip="Zoom in" />
        <ToolbarButton icon={<ZoomOut size={14} />} onClick={onZoomOut} tooltip="Zoom out" />
        <ToolbarButton icon={<Maximize2 size={14} />} onClick={onFitView} tooltip="Fit to view" />
        <ToolbarButton icon={<RotateCcw size={14} />} onClick={onReset} tooltip="Reset" />
      </div>
    </div>
  );
}

function ToolbarButton({ icon, onClick, tooltip }: { icon: React.ReactNode; onClick: () => void; tooltip: string }) {
  return (
    <button
      onClick={onClick}
      title={tooltip}
      className="p-1.5 rounded-lg hover:bg-zinc-100 text-zinc-500 hover:text-zinc-700 transition-colors"
    >
      {icon}
    </button>
  );
}
```

**Step 2: Commit**

```bash
git add frontend/src/components/knowledge-graph/GraphToolbar.tsx
git commit -m "feat: add GraphToolbar with zoom controls"
```

---

## Task 14: Create GraphSearch component

**Files:**
- Create: `frontend/src/components/knowledge-graph/GraphSearch.tsx`

**Step 1: Create the search component**

```typescript
"use client";
import { useRef, useEffect } from "react";
import { Search, X, ArrowRight } from "lucide-react";
import type { GraphNode } from "@/types";
import { NODE_TYPE_CONFIG } from "./constants";

interface Props {
  query: string;
  onQueryChange: (q: string) => void;
  results: GraphNode[];
  selectedIndex: number;
  onSelect: (node: GraphNode) => void;
  onNext: () => void;
  onClear: () => void;
}

export function GraphSearch({ query, onQueryChange, results, selectedIndex, onSelect, onNext, onClear }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "/" && document.activeElement?.tagName !== "INPUT") {
        e.preventDefault();
        inputRef.current?.focus();
      }
      if (e.key === "Escape") {
        onClear();
        inputRef.current?.blur();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClear]);

  return (
    <div className="relative">
      <div className="flex items-center gap-2 px-3 py-2 bg-zinc-50 border border-zinc-200/60 rounded-xl focus-within:border-zinc-400 focus-within:bg-white transition-colors w-72">
        <Search size={14} className="text-zinc-400 flex-shrink-0" />
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => onQueryChange(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter") onNext(); }}
          placeholder="Search nodes... ( / )"
          className="flex-1 bg-transparent text-sm text-zinc-700 placeholder:text-zinc-400 outline-none"
        />
        {query && (
          <button onClick={onClear} className="p-0.5 rounded hover:bg-zinc-200">
            <X size={12} className="text-zinc-400" />
          </button>
        )}
      </div>

      {query && results.length > 0 && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-zinc-200/60 rounded-xl shadow-lg overflow-hidden z-50 max-h-64 overflow-y-auto">
          {results.slice(0, 10).map((node, i) => {
            const config = NODE_TYPE_CONFIG[node.type] || NODE_TYPE_CONFIG.Concept;
            return (
              <button
                key={node.id}
                onClick={() => onSelect(node)}
                className={`w-full flex items-center gap-2.5 px-3 py-2 text-left transition-colors ${
                  i === selectedIndex ? "bg-zinc-50" : "hover:bg-zinc-50"
                }`}
              >
                <div
                  className="w-6 h-6 rounded flex items-center justify-center flex-shrink-0"
                  style={{ backgroundColor: `${config.color}15` }}
                >
                  <config.icon size={12} style={{ color: config.color }} />
                </div>
                <span className="text-xs font-medium text-zinc-700 truncate">{node.label}</span>
                <span className="text-[10px] text-zinc-400 ml-auto">{node.type}</span>
              </button>
            );
          })}
          {results.length > 10 && (
            <div className="px-3 py-1.5 text-[10px] text-zinc-400 border-t border-zinc-100">
              +{results.length - 10} more results
            </div>
          )}
        </div>
      )}

      {query && results.length === 0 && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-zinc-200/60 rounded-xl shadow-lg p-3 text-center z-50">
          <p className="text-xs text-zinc-400">No matching nodes</p>
        </div>
      )}
    </div>
  );
}
```

**Step 2: Commit**

```bash
git add frontend/src/components/knowledge-graph/GraphSearch.tsx
git commit -m "feat: add GraphSearch with autocomplete and keyboard shortcuts"
```

---

## Task 15: Create KnowledgeGraphView main component

**Files:**
- Create: `frontend/src/components/knowledge-graph/KnowledgeGraphView.tsx`

**Step 1: Create the main graph view**

```typescript
"use client";
import { useState, useCallback, useEffect, useMemo } from "react";
import ReactFlow, {
  ReactFlowProvider, useReactFlow, Background, MiniMap,
  type Node, type Edge, type OnNodesChange, type OnEdgesChange,
  applyNodeChanges, applyEdgeChanges,
} from "reactflow";
import "reactflow/dist/style.css";

import { useGraphData } from "./hooks/useGraphData";
import { useGraphLayout } from "./hooks/useGraphLayout";
import { useGraphSearch } from "./hooks/useGraphSearch";
import { KnowledgeNode } from "./KnowledgeNode";
import { KnowledgeEdge } from "./KnowledgeEdge";
import { KnowledgeDetailsPanel } from "./KnowledgeDetailsPanel";
import { GraphToolbar } from "./GraphToolbar";
import { GraphSearch } from "./GraphSearch";
import { NODE_TYPE_CONFIG } from "./constants";
import type { GraphNode } from "@/types";

const nodeTypes = { knowledgeNode: KnowledgeNode };
const edgeTypes = { knowledgeEdge: KnowledgeEdge };

function GraphInner() {
  const { data: graphResponse, isLoading } = useGraphData();
  const { applyLayout, isLayouting } = useGraphLayout();
  const { fitView, setCenter, getZoom } = useReactFlow();

  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);

  const graphNodes = graphResponse?.data?.nodes || [];
  const graphEdges = graphResponse?.data?.edges || [];
  const metadata = graphResponse?.data?.metadata;

  const { query, setQuery, results, highlightedIds, selectedIndex, selectNext, centerOnNode, clearSearch } = useGraphSearch(graphNodes);

  // Apply layout when data loads
  useEffect(() => {
    if (graphNodes.length > 0 && nodes.length === 0) {
      applyLayout(graphNodes, graphEdges).then(({ nodes: layoutedNodes, edges: layoutedEdges }) => {
        setNodes(layoutedNodes);
        setEdges(layoutedEdges);
        setTimeout(() => fitView({ padding: 0.2, duration: 300 }), 50);
      });
    }
  }, [graphNodes, graphEdges, applyLayout, fitView, nodes.length]);

  // Listen for center-on-node events
  useEffect(() => {
    const handler = (e: Event) => {
      const { nodeId } = (e as CustomEvent).detail;
      const node = nodes.find((n) => n.id === nodeId);
      if (node) {
        setCenter(node.position.x + 100, node.position.y + 30, { duration: 300, zoom: 1.2 });
      }
    };
    window.addEventListener("graph:centerOnNode", handler);
    return () => window.removeEventListener("graph:centerOnNode", handler);
  }, [nodes, setCenter]);

  const onNodesChange: OnNodesChange = useCallback(
    (changes) => setNodes((nds) => applyNodeChanges(changes, nds)),
    []
  );
  const onEdgesChange: OnEdgesChange = useCallback(
    (changes) => setEdges((eds) => applyEdgeChanges(changes, eds)),
    []
  );

  const onNodeClick = useCallback((_: React.MouseEvent, node: Node) => {
    setSelectedNode(node.data as GraphNode);
  }, []);

  const onPaneClick = useCallback(() => {
    setSelectedNode(null);
  }, []);

  // Apply search highlighting
  const displayNodes = useMemo(() => {
    if (highlightedIds.size === 0) return nodes;
    return nodes.map((n) => ({
      ...n,
      style: {
        ...n.style,
        opacity: highlightedIds.has(n.id) ? 1 : 0.2,
        transition: "opacity 200ms ease",
      },
    }));
  }, [nodes, highlightedIds]);

  const displayEdges = useMemo(() => {
    if (highlightedIds.size === 0) return edges;
    return edges.map((e) => ({
      ...e,
      style: {
        ...e.style,
        opacity: highlightedIds.has(e.source) && highlightedIds.has(e.target) ? 0.8 : 0.1,
      },
    }));
  }, [edges, highlightedIds]);

  const handleSelectResult = useCallback((node: GraphNode) => {
    centerOnNode(node.id);
    setSelectedNode(node);
    clearSearch();
  }, [centerOnNode, clearSearch]);

  if (isLoading || isLayouting) {
    return (
      <div className="h-[600px] bg-zinc-50 rounded-xl animate-pulse flex items-center justify-center">
        <span className="text-sm text-zinc-400">Loading graph...</span>
      </div>
    );
  }

  if (graphNodes.length === 0) {
    return (
      <div className="h-[600px] bg-zinc-50 rounded-xl flex flex-col items-center justify-center text-zinc-400">
        <span className="text-sm">No knowledge graph data yet.</span>
      </div>
    );
  }

  return (
    <div className="flex h-[600px] bg-white rounded-xl border border-zinc-200/60 overflow-hidden">
      {/* Graph area */}
      <div className="flex-1 flex flex-col">
        {/* Toolbar */}
        <GraphToolbar
          nodeCount={metadata?.total_nodes ?? 0}
          edgeCount={metadata?.total_edges ?? 0}
          onFitView={() => fitView({ padding: 0.2, duration: 300 })}
          onZoomIn={() => setCenter(0, 0, { zoom: getZoom() * 1.3, duration: 200 })}
          onZoomOut={() => setCenter(0, 0, { zoom: getZoom() * 0.7, duration: 200 })}
          onReset={() => {
            setNodes([]);
            setEdges([]);
          }}
        />

        {/* Search bar overlay */}
        <div className="absolute top-14 left-4 z-10">
          <GraphSearch
            query={query}
            onQueryChange={setQuery}
            results={results}
            selectedIndex={selectedIndex}
            onSelect={handleSelectResult}
            onNext={selectNext}
            onClear={clearSearch}
          />
        </div>

        {/* ReactFlow canvas */}
        <div className="flex-1">
          <ReactFlow
            nodes={displayNodes}
            edges={displayEdges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onNodeClick={onNodeClick}
            onPaneClick={onPaneClick}
            nodeTypes={nodeTypes}
            edgeTypes={edgeTypes}
            fitView
            fitViewOptions={{ padding: 0.2 }}
            minZoom={0.05}
            maxZoom={3}
            defaultEdgeOptions={{ type: "knowledgeEdge" }}
          >
            <Background gap={20} size={1} color="#e5e7eb" />
            <MiniMap
              nodeColor={(n) => {
                const config = NODE_TYPE_CONFIG[n.data?.type] || NODE_TYPE_CONFIG.Concept;
                return config.color;
              }}
              maskColor="rgba(255,255,255,0.7)"
              className="!bottom-4 !right-4"
              pannable
              zoomable
            />
          </ReactFlow>
        </div>
      </div>

      {/* Details panel */}
      {selectedNode && (
        <KnowledgeDetailsPanel node={selectedNode} onClose={() => setSelectedNode(null)} />
      )}
    </div>
  );
}

export function KnowledgeGraphView() {
  return (
    <ReactFlowProvider>
      <GraphInner />
    </ReactFlowProvider>
  );
}
```

**Step 2: Commit**

```bash
git add frontend/src/components/knowledge-graph/KnowledgeGraphView.tsx
git commit -m "feat: add KnowledgeGraphView main component with ReactFlow"
```

---

## Task 16: Wire KnowledgeGraphView into the knowledge page

**Files:**
- Modify: `frontend/src/app/knowledge/page.tsx`

**Step 1: Replace KnowledgeGraph import**

Replace line 8:
```typescript
import { KnowledgeGraph } from "@/components/KnowledgeGraph";
```
with:
```typescript
import { KnowledgeGraphView } from "@/components/knowledge-graph/KnowledgeGraphView";
```

**Step 2: Replace the component usage**

Replace line 71:
```typescript
<KnowledgeGraph />
```
with:
```typescript
<KnowledgeGraphView />
```

**Step 3: Commit**

```bash
git add frontend/src/app/knowledge/page.tsx
git commit -m "feat: wire KnowledgeGraphView into knowledge page"
```

---

## Task 17: Update knowledge-detail page for enhanced data

**Files:**
- Modify: `frontend/src/app/knowledge/[id]/page.tsx`

**Step 1: Check the current detail page**

Read the file and verify it uses `KnowledgeObject` type. If it uses `GraphEdge` for relationships, update to use the new `GraphEdge` type with `label` field.

(This task may be a no-op if the detail page doesn't use graph types directly.)

**Step 2: Commit if changes needed**

```bash
git add frontend/src/app/knowledge/[id]/page.tsx
git commit -m "fix: update knowledge detail page for enhanced graph types"
```

---

## Task 18: Build and verify

**Step 1: Install dependencies**

Run: `cd frontend && pnpm install`

**Step 2: Run TypeScript check**

Run: `cd frontend && pnpm exec tsc --noEmit`
Expected: No errors (or only pre-existing ones)

**Step 3: Run build**

Run: `cd frontend && pnpm build`
Expected: Build succeeds

**Step 4: Run backend check**

Run: `cd backend && python -c "from app.main import app; print('Backend OK')"`
Expected: `Backend OK`

**Step 5: Final commit**

```bash
git add -A
git commit -m "feat: Enterprise Knowledge Graph - ReactFlow, ELK layout, typed nodes/edges, search, details panel"
```

---

## Summary

| Task | Description | Files |
|------|-------------|-------|
| 1 | Install elkjs | package.json |
| 2 | Backend graph schemas | schemas.py |
| 3 | Enhanced graph service | knowledge_service.py |
| 4 | Wire API endpoint | knowledge.py |
| 5 | Frontend types | types/index.ts |
| 6 | Graph constants | constants.ts |
| 7 | useGraphData hook | hooks/useGraphData.ts |
| 8 | useGraphLayout hook | hooks/useGraphLayout.ts |
| 9 | useGraphSearch hook | hooks/useGraphSearch.ts |
| 10 | KnowledgeNode | KnowledgeNode.tsx |
| 11 | KnowledgeEdge | KnowledgeEdge.tsx |
| 12 | DetailsPanel | KnowledgeDetailsPanel.tsx |
| 13 | GraphToolbar | GraphToolbar.tsx |
| 14 | GraphSearch | GraphSearch.tsx |
| 15 | KnowledgeGraphView | KnowledgeGraphView.tsx |
| 16 | Wire to page | knowledge/page.tsx |
| 17 | Update detail page | knowledge/[id]/page.tsx |
| 18 | Build & verify | — |
