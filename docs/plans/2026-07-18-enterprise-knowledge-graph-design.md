# Enterprise Knowledge Graph Design

## Vision

Transform the current graph visualization into a true Enterprise Knowledge Graph that represents business knowledge, not connected sentences. Users should feel like they are exploring the brain of their organization.

## Current State

- Raw HTML5 Canvas with circular layout, no interactivity
- ReactFlow `^11.11.4` installed but completely unused
- Backend returns flat `{nodes, edges}` with `statement[:80]` labels
- No node types, no edge labels, no clustering, no search
- Naive relation building (all same-type objects linked with REFERENCES at 0.5)

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Graph library | ReactFlow | Already installed, excellent for custom nodes, minimap, controls, strong ecosystem |
| Layout algorithm | ELK (elkjs) | Best for hierarchical/knowledge layouts, automatic edge routing, minimal crossings |
| Clustering | Type-based (KnowledgeType) | Leverages existing type system, collapsible groups |
| Search | Graph search + highlight | Filter by name/type, highlight matches, fade non-matches |
| Details panel | Full (420px slide-in) | Enterprise-grade inspector with all knowledge fields |
| Architecture | Clean replacement | Replace raw Canvas entirely with ReactFlow component system |
| Backend | Enhanced graph API | Typed nodes/edges, short labels, cluster metadata |

---

## Section 1: Data Layer

### Backend Graph API Enhancement

**Endpoint:** `GET /api/v1/knowledge/graph`

**New response schema:**

```
GraphResponse:
  nodes: GraphNode[]
    - id: string (UUID)
    - label: string (short, business-friendly title, max 40 chars)
    - type: KnowledgeType (enum)
    - confidence: number (0-1)
    - documentId: string
    - documentTitle: string
    - entityCount: number
    - relationshipCount: number
    - cluster: string (type-based grouping label)

  edges: GraphEdge[]
    - id: string (UUID)
    - source: string
    - target: string
    - type: RelationType (enum)
    - confidence: number (0-1)
    - label: string (human-readable relationship)

  metadata:
    - totalNodes: number
    - totalEdges: number
    - clusters: ClusterInfo[]
      - name: string (e.g., "Rules", "Procedures")
      - type: KnowledgeType
      - nodeCount: number
      - color: string (hex)
    - typeCounts: Record<KnowledgeType, number>
```

### Node Label Generation

Instead of `statement[:80]`, generate short titles:

1. Extract first sentence
2. Remove leading articles/conjunctions
3. Cap at 5 words
4. If still > 40 chars, truncate with ellipsis
5. Fallback: use KnowledgeType label (e.g., "Rule #1")

Examples:
- "The manager must approve or reject expense requests within three business days" → "Manager Approval"
- "HR validates requests above a threshold of 500 euros" → "HR Validation Threshold"
- "Payment is processed within 10 business days after approval" → "Payment Processing"

### Pydantic Schemas

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

class GraphResponse(BaseModel):
    nodes: list[GraphNodeResponse]
    edges: list[GraphEdgeResponse]
    metadata: GraphMetadata
```

---

## Section 2: Component Architecture

### New Component Tree

```
KnowledgeGraphView          # Main container (ReactFlow provider)
├── GraphToolbar            # Top bar: search, layout switch, zoom controls
├── ReactFlow               # Core graph canvas
│   ├── KnowledgeNode       # Custom node per KnowledgeType
│   │   ├── NodeIcon        # Type-specific icon
│   │   ├── NodeLabel       # Short title (truncated at 30 chars)
│   │   └── ConfidenceBadge # Optional confidence indicator
│   ├── KnowledgeEdge       # Custom edge with label + arrow
│   └── ClusterGroup        # Visual grouping boundary per type
├── GraphMinimap            # Bottom-right minimap
├── GraphControls           # Zoom in/out/fit controls
├── GraphSearch             # Search bar with autocomplete
└── KnowledgeDetailsPanel   # Right sidebar (slide-in on node click)
    ├── PanelHeader         # Title, type badge, close button
    ├── SummarySection      # Normalized statement, original text
    ├── EntitiesSection     # Actors, actions, objects
    ├── ConditionsSection   # Conditions, constraints, exceptions
    ├── RelationshipsSection# Incoming/outgoing edges with links
    ├── SourceSection       # Document, page, section, timestamp
    └── MetadataSection     # Confidence, version, extraction date
```

### Files to Create/Modify

**New files:**
```
frontend/src/components/knowledge-graph/
├── KnowledgeGraphView.tsx      # Main container
├── KnowledgeNode.tsx           # Custom ReactFlow node
├── KnowledgeEdge.tsx           # Custom ReactFlow edge
├── GraphToolbar.tsx            # Top toolbar
├── GraphSearch.tsx             # Search component
├── GraphMinimap.tsx            # Minimap wrapper
├── GraphControls.tsx           # Zoom controls
├── KnowledgeDetailsPanel.tsx   # Right sidebar
├── types.ts                    # Graph-specific types
├── constants.ts                # Colors, icons, type mappings
├── hooks/
│   ├── useGraphData.ts         # Fetch and transform graph data
│   ├── useGraphLayout.ts       # ELK layout computation
│   └── useGraphSearch.ts       # Search and highlight logic
└── utils/
    ├── nodeLabelGenerator.ts   # Short title generation
    └── layoutHelpers.ts        # ELK configuration
```

**Modified files:**
```
frontend/src/app/knowledge/page.tsx  # Replace KnowledgeGraph import
frontend/src/types/index.ts          # Enhanced GraphNode/GraphEdge types
backend/app/domain/schemas.py        # New Pydantic schemas
backend/app/service/knowledge_service.py  # Enhanced get_knowledge_graph
```

### Knowledge Type Visual Mapping

| Type | Color | Icon |
|------|-------|------|
| Rule | #EF4444 (Red) | Shield |
| Procedure | #3B82F6 (Blue) | ListOrdered |
| Concept | #8B5CF6 (Purple) | Lightbulb |
| Workflow | #10B981 (Green) | GitBranch |
| Responsibility | #F97316 (Orange) | Users |
| Decision | #EAB308 (Yellow) | GitCommit |
| Requirement | #14B8A6 (Teal) | CheckCircle |
| Constraint | #EC4899 (Pink) | Lock |
| Exception | #6B7280 (Gray) | AlertTriangle |
| Risk | #DC2626 (Dark Red) | AlertOctagon |
| KPI | #06B6D4 (Cyan) | BarChart2 |
| Metric | #6366F1 (Indigo) | TrendingUp |
| Policy | #1E3A5F (Navy) | BookOpen |
| Event | #F59E0B (Amber) | Calendar |
| Obligation | #059669 (Emerald) | ShieldCheck |
| Prohibition | #E11D48 (Rose) | Ban |

### Relation Type Visual Mapping

| Relation | Color | Arrow |
|----------|-------|-------|
| depends_on | #6366F1 | → |
| requires | #EF4444 | → |
| references | #6B7280 | → |
| causes | #F97316 | → |
| blocks | #DC2626 | → |
| extends | #10B981 | → |
| contradicts | #E11D48 | ↔ |
| parent | #3B82F6 | ↓ |
| child | #3B82F6 | ↑ |
| workflow_step | #14B8A6 | → |
| owned_by | #8B5CF6 | → |
| executed_by | #F59E0B | → |
| measured_by | #06B6D4 | → |
| validates | #059669 | → |
| triggers | #EC4899 | → |
| affects | #6366F1 | → |

---

## Section 3: Layout & Clustering

### ELK Layout Integration

Using `elkjs` for automatic hierarchical layout:

- **Direction:** Top-to-bottom (TB) for process/policy graphs
- **Edge routing:** ELK automatic routing with minimal crossings
- **Node spacing:** Dynamic based on node count
  - < 50 nodes: 80px horizontal, 120px vertical
  - 50-200 nodes: 60px horizontal, 100px vertical
  - > 200 nodes: 40px horizontal, 80px vertical
- **Cluster layout:** Nodes within same type cluster are grouped with visible boundaries
- **Edge separation:** 20px minimum between parallel edges

### ELK Configuration

```typescript
const elkOptions = {
  'elk.algorithm': 'layered',
  'elk.direction': 'DOWN',
  'elk.layered.spacing.nodeNodeBetweenLayers': 100,
  'elk.spacing.nodeNode': 80,
  'elk.layered.edgeRouting': 'POLYLINE',
  'elk.layered.mergeEdges': true,
  'elk.layered.nodePlacement': 'BRANDES_KOEPF',
};
```

### Type-Based Clustering

Each `KnowledgeType` becomes a collapsible cluster:

- **Visual:** Subtle background rectangle with rounded corners (12px radius)
- **Color:** 10% opacity of the type's primary color
- **Border:** 1px solid, 20% opacity of type color
- **Label:** Top-left, shows type name + count (e.g., "Rules (12)")
- **Collapsible:** Click cluster header to collapse/expand
- **Auto-sizing:** Container grows/shrinks with its nodes
- **Padding:** 20px internal padding

### Layout Behavior

- **Initial load:** Auto-layout with ELK, fit to viewport with 50ms delay
- **Node drag:** Only dragged node moves (no re-layout)
- **Add/remove node:** Subtle 300ms animation, no full re-layout
- **Zoom-dependent rendering:**
  - Below 0.3x: Hide edge labels
  - Below 0.1x: Hide node labels, show only colored dots
  - Above 0.5x: Show full node labels and edge labels

---

## Section 4: Interaction & Navigation

### Node Interactions

- **Click:** Opens KnowledgeDetailsPanel on the right (slide-in animation, 200ms ease)
- **Hover:** Shows tooltip with type, confidence, and document source
- **Double-click:** Centers and zooms to node, expands its immediate neighbors (1-hop)
- **Drag:** Repositions the node (no re-layout triggered)

### Edge Interactions

- **Hover:** Highlights the edge (increases opacity to 1.0), shows relationship label
- **Click:** No action (future: opens edge details)

### Graph Navigation

- **Zoom:** Mouse wheel + pinch gesture (range: 0.05x to 3x)
- **Pan:** Click-drag on empty canvas background
- **Minimap:** Bottom-right corner, 200x150px, shows full graph thumbnail, click to navigate
- **Fit to viewport:** Button (or `F` key) to zoom out and show all nodes
- **Center on node:** After search, smoothly animate (300ms) to center on found node
- **Zoom controls:** Bottom-right, above minimap: +/- buttons, fit button, fullscreen toggle

### Search

- **Input:** Top toolbar search bar (280px wide)
- **Behavior:** As user types, filter nodes by label (case-insensitive contains) and type
- **Highlight:** Matching nodes get full opacity + blue border. Non-matching nodes fade to 0.2 opacity.
- **Center:** After pressing Enter or clicking a result, center viewport on the first match
- **Keyboard:** Enter to cycle through results, Escape to clear search
- **Autocomplete:** Dropdown shows top 10 matching nodes with type badge and label

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `/` | Focus search bar |
| `Escape` | Close details panel / clear search |
| `F` | Fit graph to viewport |
| `+` / `-` | Zoom in / out |
| `0` | Reset zoom to 1.0 |
| `Space` + drag | Pan (alternative to drag on background) |

---

## Section 5: Details Panel

### Panel Layout

```
┌─────────────────────────────────────────┐
│ [Icon] Manager Approval          [×]   │
│ Rule · Confidence: 92%                  │
│                                         │
│ ── Summary ──────────────────────────   │
│ The manager must approve or reject      │
│ expense requests within three           │
│ business days.                          │
│                                         │
│ ── Original Text ───────────────────   │
│ "Le manager doit approuver ou rejeter   │
│ les demandes de dépenses dans les       │
│ trois jours ouvrables."                 │
│                                         │
│ ── Entities ────────────────────────   │
│ 👤 Actors: Manager                      │
│ ⚡ Actions: approve, reject             │
│ 📦 Objects: expense request             │
│                                         │
│ ── Conditions ──────────────────────   │
│ 📋 Condition: Within 3 business days    │
│ 🔒 Constraint: Amount > €1000           │
│                                         │
│ ── Relationships (6) ───────────────   │
│ → requires [HR Approval]                │
│ → depends_on [Expense Request]          │
│ → measured_by [Approval Time KPI]       │
│ ← triggers [Late Submission]            │
│                                         │
│ ── Source ──────────────────────────   │
│ 📄 Expense Policy v2.pdf                │
│ Page 3 · Section 4.2                    │
│ Extracted: 2026-07-15 · v1              │
└─────────────────────────────────────────┘
```

### Panel Behavior

- **Width:** 420px fixed (resizable in future)
- **Animation:** Slide-in from right, 200ms ease-out
- **Close:** × button in header or Escape key
- **Scroll:** Independent scroll within panel body
- **Relationships:** Click any relationship node name to navigate to that node (center + highlight)
- **Empty state:** When no node selected, show "Click a node to view details"

---

## Section 6: Performance Strategy

### For This Build

- ReactFlow handles rendering optimization automatically (only renders visible nodes)
- ELK layout computation runs in a Web Worker (non-blocking)
- Graph data is cached in React state (no refetch on every interaction)
- Edge labels hidden below 0.3x zoom
- Node labels hidden below 0.1x zoom

### Future Scaling (100k+ nodes)

- Virtual rendering (ReactFlow supports this)
- Progressive loading (load visible area first)
- Clustering at zoom levels (collapse distant clusters to single nodes)
- Graph partitioning for very large datasets
- WebSocket for real-time graph updates

---

## Section 7: Dependencies to Install

### Frontend

```bash
cd frontend
pnpm add elkjs @types/elkjs
# dagre is optional backup: pnpm add dagre @types/dagre
```

### Backend

No new Python dependencies needed. The enhanced graph API uses existing SQLAlchemy models.

---

## Implementation Order

1. **Backend: Enhanced graph API** — New Pydantic schemas, label generation, cluster detection
2. **Frontend: Types & constants** — Graph-specific types, color/icon mappings
3. **Frontend: Core graph** — KnowledgeGraphView with ReactFlow, basic custom nodes/edges
4. **Frontend: ELK layout** — Layout hook with elkjs integration
5. **Frontend: Custom nodes** — KnowledgeNode with type-based styling
6. **Frontend: Custom edges** — KnowledgeEdge with labels and arrows
7. **Frontend: Clustering** — Type-based cluster groups
8. **Frontend: Details panel** — KnowledgeDetailsPanel with all sections
9. **Frontend: Search** — GraphSearch with filter/highlight/center
10. **Frontend: Toolbar & controls** — GraphToolbar, GraphControls, GraphMinimap
11. **Integration: Wire everything** — Connect to knowledge page, test end-to-end
12. **Polish: Animations, transitions, empty states**
