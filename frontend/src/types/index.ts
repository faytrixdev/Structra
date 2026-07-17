export interface User { id: string; email: string; name: string }

export interface Document {
  id: string; title: string; file_type: string;
  file_size: number | null; status: string;
  page_count: number | null; error_message: string | null;
  created_at: string;
}

export interface KnowledgeEntity { entity_type: string; value: string; role: string | null }
export interface KnowledgeCondition { condition_type: string; description: string }

export interface KnowledgeObject {
  id: string; type: string; title: string | null;
  statement: string; original_text: string;
  confidence: number; created_at: string;
  entities: KnowledgeEntity[]; conditions: KnowledgeCondition[];
}

export interface GraphNode { id: string; type: string; label: string; confidence: number }
export interface GraphEdge { source: string; target: string; type: string }
export interface SearchResult { id: string; statement: string; type: string; confidence: number; score: number; document_title: string }
export interface APIResponse<T> { status: string; data: T; error?: string; meta?: Record<string, unknown> }
