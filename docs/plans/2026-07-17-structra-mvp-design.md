# Structra MVP — Architecture Design

Date: 2026-07-17
Status: Approved

---

## Architecture globale

```
┌─────────────────────────────────────────────────┐
│                   User Browser                    │
│               Next.js + Tailwind + Shadcn        │
└──────────────────────┬──────────────────────────┘
                       │ HTTPS
┌──────────────────────▼──────────────────────────┐
│              FastAPI Backend (Python)             │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────┐  │
│  │ Auth API │ │ Doc API  │ │ Knowledge API    │  │
│  └──────────┘ └──────────┘ └──────────────────┘  │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────┐  │
│  │ Pipeline │ │ Search   │ │ Export           │  │
│  └──────────┘ └──────────┘ └──────────────────┘  │
└──────┬─────────────────────────────┬─────────────┘
       │                             │
┌──────▼──────────┐     ┌───────────▼───────────┐
│   Supabase      │     │   Qdrant Cloud         │
│   PostgreSQL    │     │   Vector DB            │
│   + Storage     │     │                        │
│   + Auth        │     │                        │
└─────────────────┘     └───────────────────────┘
```

### Structure du projet

```
structra/
├── frontend/              # Next.js App
│   ├── src/
│   │   ├── app/           # Pages (App Router)
│   │   ├── components/    # Composants réutilisables
│   │   ├── lib/           # Utilitaires, API client
│   │   └── types/         # Types TypeScript
│   ├── package.json
│   └── next.config.js
├── backend/               # FastAPI
│   ├── app/
│   │   ├── api/           # Routes FastAPI
│   │   ├── service/       # Business logic
│   │   ├── pipeline/      # Pipeline IA
│   │   ├── provider/      # LLM providers
│   │   ├── repository/    # Accès données
│   │   └── domain/        # Modèles métier
│   ├── migrations/        # Alembic
│   ├── requirements.txt
│   └── main.py
├── docs/
│   └── plans/
└── README.md
```

---

## Schéma Supabase PostgreSQL

### Users & Organizations

```sql
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    avatar_url TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE organization_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('owner', 'admin', 'member')),
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(user_id, organization_id)
);
```

### Documents

```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    file_type TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_size BIGINT,
    page_count INT,
    status TEXT NOT NULL DEFAULT 'uploaded',
    metadata JSONB DEFAULT '{}',
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    page_number INT,
    section TEXT,
    position INT NOT NULL
);

CREATE TABLE document_errors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    pipeline_step TEXT NOT NULL,
    message TEXT NOT NULL,
    details JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

### Knowledge

```sql
CREATE TABLE knowledge_objects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    type TEXT NOT NULL,
    title TEXT,
    statement TEXT NOT NULL,
    original_text TEXT NOT NULL,
    confidence FLOAT DEFAULT 0.0,
    version INT DEFAULT 1,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE knowledge_entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    knowledge_id UUID REFERENCES knowledge_objects(id) ON DELETE CASCADE,
    entity_type TEXT NOT NULL CHECK (entity_type IN ('actor', 'action', 'object')),
    value TEXT NOT NULL,
    role TEXT
);

CREATE TABLE knowledge_conditions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    knowledge_id UUID REFERENCES knowledge_objects(id) ON DELETE CASCADE,
    condition_type TEXT NOT NULL CHECK (condition_type IN ('condition', 'constraint', 'exception')),
    description TEXT NOT NULL
);

CREATE TABLE knowledge_relations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID REFERENCES knowledge_objects(id) ON DELETE CASCADE,
    target_id UUID REFERENCES knowledge_objects(id) ON DELETE CASCADE,
    relation_type TEXT NOT NULL,
    confidence FLOAT DEFAULT 0.0,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(source_id, target_id, relation_type)
);
```

### Audit & Pipeline

```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    resource_id UUID,
    details JSONB DEFAULT '{}',
    ip_address TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE pipeline_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    step TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('running', 'completed', 'failed')),
    duration_ms INT,
    tokens_used INT,
    model TEXT,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

---

## API REST

### Auth

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| POST | `/api/v1/auth/register` | Inscription |
| POST | `/api/v1/auth/login` | Connexion |
| GET | `/api/v1/auth/me` | Profil courant |

### Documents

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/v1/documents` | Liste documents |
| POST | `/api/v1/documents` | Upload document |
| GET | `/api/v1/documents/{id}` | Détail document |
| DELETE | `/api/v1/documents/{id}` | Suppression |
| POST | `/api/v1/documents/{id}/process` | Lancer pipeline |
| GET | `/api/v1/documents/{id}/status` | Statut pipeline |

### Knowledge

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/v1/knowledge` | Liste + filtres |
| GET | `/api/v1/knowledge/{id}` | Détail |
| GET | `/api/v1/knowledge/{id}/relations` | Relations |
| GET | `/api/v1/knowledge/graph` | Graphe complet |

### Search & Export

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/v1/search?q=` | Recherche sémantique |
| GET | `/api/v1/export/json` | Export JSON |
| GET | `/api/v1/export/csv` | Export CSV |

---

## Pipeline IA

```
upload → extract_text → clean → segment
  → extract_ideas → classify → extract_entities
  → build_relations → validate → store
```

### Provider LLM : NVIDIA NIM

- API : `https://api.nvcf.nvidia.com/v2/chat/completions`
- Modèle : configurable (Llama 3.1 Nemotron, Llama 3.1 405B, etc.)
- JSON mode pour sortie structurée
- Clé API via variable d'environnement `NVIDIA_API_KEY`

### Prompts spécialisés

Chaque étape du pipeline utilise un system prompt dédié avec :
- Instructions précises
- Few-shot examples du domaine
- Format JSON de sortie

### Validation

1. **Validation structurelle** : Pydantic schema → champs requis, types
2. **Validation LLM** : Second appel NVIDIA NIM pour qualité (score 0-1)

---

## Frontend (Next.js)

### Pages

| Route | Page |
|-------|------|
| `/` | Redirection vers dashboard |
| `/login` | Connexion |
| `/register` | Inscription |
| `/dashboard` | Dashboard |
| `/documents` | Liste documents |
| `/documents/{id}` | Détail document |
| `/knowledge` | Knowledge Explorer |
| `/knowledge/{id}` | Détail connaissance |
| `/settings` | Paramètres |

### Composants

- `DocumentUploader` — Drag & drop
- `PipelineStatus` — Progression pipeline
- `KnowledgeCard` — Carte de connaissance
- `KnowledgeGraph` — Graphe (React Flow)
- `KnowledgeFilters` — Filtres
- `SemanticSearch` — Recherche sémantique

### Stack

- Next.js 14+ App Router
- Shadcn UI + Tailwind CSS
- TanStack Query (React Query)
- Lucide React (icônes)
- React Flow (graphe)

---

## Sécurité

- Authentification via Supabase Auth
- Tenant isolation : `organization_id` filtre toutes les requêtes
- Audit logs : toutes les actions sont tracées
- Validation des entrées : Pydantic (backend), Zod (frontend)
- Protection fichiers : validation MIME, taille max, scan
- CORS configuré pour le frontend uniquement
- Clés API en variables d'environnement
