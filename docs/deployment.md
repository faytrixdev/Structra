# Structra — Deployment Guide

> Architecture : **Vercel** (frontend) + **Render** (backend) + **Supabase** (DB + Auth + Storage) + **Qdrant Cloud** (vector) + **NVIDIA NIM** (LLM)
>
> Coût estimé : **~7 €/mois** (Render starter = seul service payant)

---

## 1. Prérequis

| Service | Compte requis | Usage |
|---------|--------------|-------|
| [GitHub](https://github.com) | Oui | Code source |
| [Vercel](https://vercel.com) | Gratuit | Frontend Next.js |
| [Render](https://render.com) | Gratuit (starter payant) | Backend FastAPI |
| [Supabase](https://supabase.com) | Gratuit | PostgreSQL, Auth, Storage |
| [Qdrant Cloud](https://cloud.qdrant.io) | Gratuit (1 GB) | Base vectorielle |
| [NVIDIA NIM](https://build.nvidia.com) | Gratuit (quota limité) | LLM meta/llama-3.1-70b-instruct |

---

## 2. Supabase — Base de données + Storage

### 2.1 Créer le projet

1. Aller sur [supabase.com](https://supabase.com) → **New project**
2. Choisir un nom de projet, un mot de passe root, et une région proche de tes utilisateurs
3. Noter le **Database URL** au format :

```
postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres
```

### 2.2 Créer le bucket Storage

1. Dashboard → **Storage** → **New bucket**
2. Nom : `documents`
3. **Public** : non (les fichiers ne doivent pas être accessibles sans auth)
4. **File size limit** : 50 Mo
5. Allowed MIME types : laisser vide (le backend valide lui-même)

### 2.3 Exécuter les migrations

Deux options :

**Option A — Script SQL manuel (recommandé pour le premier déploiement)**

Le script ci-dessous crée toutes les tables. Il suffit de l'exécuter dans le **SQL Editor** du dashboard Supabase.

```sql
-- Voir backend/alembic/versions/ pour les migrations individuelles
-- Ou exécuter :
-- alembic upgrade head (via le backend local avec DATABASE_URL pointant vers Supabase)
```

**Option B — Alembic depuis le backend local**

```bash
cd backend
export DATABASE_URL="postgresql://postgres:[PASSWORD]@db.[REF].supabase.co:5432/postgres"
.\venv\Scripts\alembic upgrade head    # Windows
alembic upgrade head                    # Linux/Mac
```

> Astuce : Render exécute `alembic upgrade head` au démarrage (voir étape 5).

---

## 3. Qdrant Cloud — Base vectorielle

1. Aller sur [cloud.qdrant.io](https://cloud.qdrant.io) → **Create cluster**
2. Choisir le **Free tier** (1 GB, suffisant pour commencer)
3. Noter :
   - `QDRANT_URL` : `https://[CLUSTER_ID].qdrant.io:6333`
   - `QDRANT_API_KEY` : généré automatiquement

---

## 4. NVIDIA NIM — LLM

1. Aller sur [build.nvidia.com](https://build.nvidia.com) → **Sign in**
2. **NIM API Keys** → **Generate API Key**
3. Noter la clé : `nvapi-...`
4. Modèle : `meta/llama-3.1-70b-instruct` (inclus dans le free tier)
5. Rate limit free tier : ~1000 requêtes/jour, ~10 requêtes/minute

---

## 5. Backend — Render

### 5.1 Créer le Web Service

1. Aller sur [render.com](https://render.com) → **New** → **Web Service**
2. Connecter le repository GitHub
3. Configurer :

| Champ | Valeur |
|-------|--------|
| **Name** | `structra-backend` |
| **Region** | Frankfurt (ou la plus proche) |
| **Branch** | `main` |
| **Root Directory** | `backend` |
| **Runtime** | Python 3 |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port $PORT` |

> **Note** : Render passe le port via `$PORT`. uvicorn l'utilise automatiquement.

### 5.2 Variables d'environnement

Ajouter dans **Environment** → **Environment Variables** :

```env
# ── Database ────────────────────────────────────────────────────────────
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[REF].supabase.co:5432/postgres

# ── Supabase ────────────────────────────────────────────────────────────
SUPABASE_URL=https://[REF].supabase.co
SUPABASE_KEY=eyJ... (la clé "anon" dans Settings → API)
SUPABASE_STORAGE_BUCKET=documents

# ── Vector DB ───────────────────────────────────────────────────────────
QDRANT_URL=https://[CLUSTER].qdrant.io:6333
QDRANT_API_KEY=...

# ── LLM ─────────────────────────────────────────────────────────────────
NVIDIA_API_KEY=nvapi-...
NVIDIA_MODEL=meta/llama-3.1-70b-instruct

# ── Auth ────────────────────────────────────────────────────────────────
JWT_SECRET=[générer avec : python -c "import secrets; print(secrets.token_urlsafe(64))"]

# ── CORS ────────────────────────────────────────────────────────────────
CORS_ORIGINS=https://[NOM].vercel.app

# ── Pipeline ────────────────────────────────────────────────────────────
PIPELINE_MODE=high_accuracy
PIPELINE_MAX_CONCURRENCY=2
PIPELINE_REQUEST_PACING_MS=1500
PIPELINE_COMBINED_DEFAULT=true

# ── Limits ──────────────────────────────────────────────────────────────
MAX_FILE_SIZE_MB=50
```

### 5.3 Générer le JWT_SECRET

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

### 5.4 Vérification

Après le déploiement, Render affiche l'URL du service (ex: `https://structra-backend.onrender.com`).

Tester :

```bash
curl https://structra-backend.onrender.com/api/health
# → {"status":"ok","version":"0.1.0"}
```

---

## 6. Frontend — Vercel

### 6.1 Importer le projet

1. Aller sur [vercel.com](https://vercel.com) → **New Project**
2. Importer le repository GitHub
3. Configurer :

| Champ | Valeur |
|-------|--------|
| **Framework** | Next.js (auto-detected) |
| **Root Directory** | `frontend` |
| **Build Command** | `next build` (default) |
| **Output Directory** | `.next` (default) |

### 6.2 Variable d'environnement

Dans **Settings → Environment Variables** :

```env
NEXT_PUBLIC_API_URL=https://structra-backend.onrender.com/api/v1
```

> **Important** : `NEXT_PUBLIC_` est requis pour que Next.js injecte la variable côté client au build.

### 6.3 Déploiement

Vercel détecte automatiquement les pushes sur `main` et redéploie.

---

## 7. Adaptations backend pour la production

### 7.1 CORS dynamique

Le CORS est géré par la variable `CORS_ORIGINS` (séparée par virgules).
Déjà implémenté dans `main.py` :

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,  # Liste depuis CORS_ORIGINS env
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 7.2 Fichiers uploadés

**⚠️ Important** : Render utilise un disque **ephemeral**. Les fichiers dans `uploads/` sont perdus après redémarrage.

Pour le MVP, c'est acceptable car :
- Les fichiers sont traités pendant le pipeline
- Les résultats (knowledge objects) sont persistés en base PostgreSQL
- Les fichiers uploadés ne servent plus après traitement

Si tu veux conserver les fichiers, il faudra migrer vers **Supabase Storage** (voir section 8).

### 7.3 Health check

Render vérifie `/api/health` automatiquement. Le endpoint existe déjà dans `main.py`.

---

## 8. (Optionnel) Migrer les uploads vers Supabase Storage

Si tu veux conserver les fichiers uploadés de manière persistante, remplace le stockage local par Supabase Storage.

**`app/service/document_service.py`** — modifications à faire :

```python
# Remplacer le stockage local :
#   with open(file_path, "wb") as f:
#       f.write(content)
# Par :
from app.supabase_client import supabase

supabase.storage.from_("documents").upload(
    path=f"{file_id}-{file.filename}",
    file=content,
    file_options={"content-type": file.content_type},
)
file_path = f"{file_id}-{file.filename}"  # Stocker le nom, pas le chemin local
```

**`app/provider/supabase_client.py`** — nouveau fichier :

```python
from supabase import create_client
from app.config import settings

supabase = create_client(settings.supabase_url, settings.supabase_key)
```

---

## 9. Vérification post-déploiement

### 9.1 Backend

```bash
# Health check
curl https://structra-backend.onrender.com/api/health

# Inscription
curl -X POST https://structra-backend.onrender.com/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"securepass123","name":"Test User"}'

# Login
curl -X POST https://structra-backend.onrender.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"securepass123"}'
```

### 9.2 Frontend

1. Ouvrir `https://[NOM].vercel.app`
2. S'inscrire / se connecter
3. Uploader un document (PDF, DOCX, MD…)
4. Cliquer **Process**
5. Vérifier que les knowledge objects apparaissent

---

## 10. Variables d'environnement — Résumé

### Backend (Render)

| Variable | Description | Exemple |
|----------|-------------|---------|
| `DATABASE_URL` | URL PostgreSQL Supabase | `postgresql://postgres:...@db.xxx.supabase.co:5432/postgres` |
| `SUPABASE_URL` | URL du projet Supabase | `https://xxx.supabase.co` |
| `SUPABASE_KEY` | Clé anon Supabase | `eyJ...` |
| `SUPABASE_STORAGE_BUCKET` | Nom du bucket | `documents` |
| `QDRANT_URL` | URL du cluster Qdrant | `https://xxx.qdrant.io:6333` |
| `QDRANT_API_KEY` | Clé API Qdrant | `...` |
| `NVIDIA_API_KEY` | Clé API NVIDIA NIM | `nvapi-...` |
| `NVIDIA_MODEL` | Modèle LLM | `meta/llama-3.1-70b-instruct` |
| `JWT_SECRET` | Secret pour les JWT | `[64 chars aléatoires]` |
| `CORS_ORIGINS` | Origines autorisées (virgules) | `https://xxx.vercel.app` |
| `PIPELINE_MODE` | Mode d'extraction | `high_accuracy` |
| `PIPELINE_MAX_CONCURRENCY` | Appels LLM simultanés | `2` |
| `PIPELINE_REQUEST_PACING_MS` | Délai entre appels LLM | `1500` |
| `PIPELINE_COMBINED_DEFAULT` | Classify+entities en 1 appel | `true` |
| `MAX_FILE_SIZE_MB` | Taille max upload (Mo) | `50` |

### Frontend (Vercel)

| Variable | Description | Exemple |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | URL du backend API | `https://xxx.onrender.com/api/v1` |

---

## 11. Coût mensuel estimé

| Service | Tier | Coût |
|---------|------|------|
| Vercel | Hobby | 0 € |
| Render | Starter | ~7 €/mois |
| Supabase | Free | 0 € |
| Qdrant Cloud | Free | 0 € |
| NVIDIA NIM | Free | 0 € |
| **Total** | | **~7 €/mois** |

---

## 12. Déploiement continu

Une fois configuré, le workflow est automatique :

1. `git push origin main`
2. Render détecte le push → rebuild + `alembic upgrade head` + restart
3. Vercel détecte le push → `next build` + deploy
4. L'application est à jour en ~2-3 minutes
