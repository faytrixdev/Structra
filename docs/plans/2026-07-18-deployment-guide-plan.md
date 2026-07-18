# Plan: docs/deployment.md

## Fichier cible
`C:\Users\PC\Documents\Structra\docs\deployment.md`

## Architecture cible

| Couche | Service | Rôle |
|--------|---------|------|
| **Frontend** | Vercel | Next.js 16 (SSR + static), déploiement automatique sur push main |
| **Backend** | Render (Web Service) | FastAPI + uvicorn, Python 3.11 |
| **Base de données** | Supabase (PostgreSQL) | Users, docs, knowledge, relations, audit |
| **Auth** | Supabase Auth | JWT-based, le frontend gère le token |
| **Storage** | Supabase Storage | Fichiers uploadés (PDF, DOCX…) |
| **LLM** | NVIDIA NIM | Appels API pour extraction/classification |
| **Vector DB** | Qdrant Cloud (gratuit 1GB) | Embeddings pour recherche sémantique |

## Contenu du guide

### 1. Prérequis
- Comptes : Vercel, Render, Supabase, NVIDIA NIM, GitHub
- Clés API : `NVIDIA_API_KEY`, `SUPABASE_URL`, `SUPABASE_KEY`, JWT secret

### 2. Étape Supabase (base de données + storage)
- Créer le projet Supabase
- Récupérer `DATABASE_URL` (format `postgresql://postgres:[PASSWORD]@db.[REF].supabase.co:5432/postgres`)
- Créer le bucket Storage `documents` (public ou private ?)
- Exécuter Alembic migrations via CI ou manuellement

### 3. Étape Qdrant Cloud
- Créer un cluster gratuit
- Récupérer `QDRANT_URL` et `QDRANT_API_KEY`

### 4. Étape NVIDIA NIM
- Créer un compte NVIDIA
- Générer une API key pour `meta/llama-3.1-70b-instruct`
- Vérifier les rate limits (gratuit : ~1000 req/jour)

### 5. Étape Backend (Render)
- Créer un "Web Service" sur Render
- Branche : `main`, dossier : `backend`
- **Build command :** `pip install -r requirements.txt && alembic upgrade head`
- **Start command :** `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Variables d'environnement à définir :
  - `DATABASE_URL`
  - `SUPABASE_URL`
  - `SUPABASE_KEY`
  - `SUPABASE_STORAGE_BUCKET=documents`
  - `NVIDIA_API_KEY`
  - `NVIDIA_MODEL=meta/llama-3.1-70b-instruct`
  - `JWT_SECRET` (générer avec `python -c "import secrets; print(secrets.token_urlsafe(64))"`)
  - `QDRANT_URL`
  - `QDRANT_API_KEY`
  - `PIPELINE_MODE=high_accuracy`
  - `CORS_ORIGINS=https://ton-app.vercel.app`

### 6. Étape Frontend (Vercel)
- Importer le repo sur Vercel
- Framework : Next.js (auto-detected)
- Root directory : `frontend`
- Variable d'environnement : `NEXT_PUBLIC_API_URL=https://ton-backend.onrender.com/api/v1`
- Le build se fait automatiquement

### 7. Adaptations backend nécessaires (à implémenter)
- **CORS dynamique** : remplacer `"http://localhost:3000"` par `settings.cors_origins` (env var séparée par virgules)
- **Uploads** : les fichiers locaux dans `uploads/` ne persistent pas sur Render (ephemeral disk). Il faut soit :
  - Supprimer la gestion locale (fichiers volatils après traitement), soit
  - Uploader directement dans Supabase Storage au lieu du disque local
- **Health check** : Render utilise `/api/health` → déjà fait

### 8. Variables d'environnement (résumé)

**Backend (Render) :**
```
DATABASE_URL=postgresql://postgres:...@db.xxx.supabase.co:5432/postgres
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJ...
SUPABASE_STORAGE_BUCKET=documents
QDRANT_URL=https://xxx.qdrant.io:6333
QDRANT_API_KEY=xxx
NVIDIA_API_KEY=nvapi-...
NVIDIA_MODEL=meta/llama-3.1-70b-instruct
JWT_SECRET=xxx
CORS_ORIGINS=https://xxx.vercel.app
```

**Frontend (Vercel) :**
```
NEXT_PUBLIC_API_URL=https://xxx.onrender.com/api/v1
```

### 9. Vérification post-déploiement
- `GET /api/health` → `{"status":"ok"}`
- Créer un compte via `/api/v1/auth/register`
- Uploader un document
- Lancer le pipeline
- Vérifier l'extraction dans la liste knowledge

### 10. Coût mensuel estimé
- Vercel : 0€ (hobby tier, 100GB bandwidth)
- Render : ~7$/mois (Web Service starter)
- Supabase : 0€ (free tier, 500MB DB + 1GB storage)
- Qdrant : 0€ (free tier, 1GB)
- NVIDIA NIM : 0€ (free tier, quota limité)
- **Total : ~7$/mois**
