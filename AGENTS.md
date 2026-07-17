# Project: Structra

## Overview

Structra is an AI-powered SaaS platform that transforms unstructured enterprise documents into structured knowledge bases.

The goal is not document summarization.

The goal is knowledge extraction, normalization and modeling.

Core principle:

> One idea = One JSON object.

Every technical decision must support this principle.

---

# Product Vision

Structra converts:

- PDF
- DOCX
- XLSX
- PPTX
- TXT
- Markdown
- HTML
- XML
- Emails
- Enterprise documentation

into:

- atomic knowledge units
- semantic relationships
- knowledge graphs
- structured JSON
- AI-ready knowledge bases

The final output should allow small specialized LLMs or AI agents to reason over business knowledge without rereading original documents.

---

# Tech Stack

## Frontend

- Next.js
- TypeScript
- React
- Tailwind CSS
- Shadcn UI

## Backend

- FastAPI
- Python
- Pydantic
- SQLAlchemy

## Database

Main database:
- Supabase PostgreSQL

Used for:
- users
- organizations
- projects
- documents
- extracted knowledge
- permissions
- metadata
- audit logs


Vector database:
- Qdrant Cloud

Used for:
- embeddings
- semantic search
- similarity detection
- duplicate detection


Storage:
- Supabase Storage

Used for:
- uploaded documents
- processed files


Authentication:
- Supabase Auth


No Docker.

Services must run directly on the host machine.

---

# Architecture Principles

Follow clean architecture.

Separate:

- API layer
- Business logic
- AI services
- Database layer
- External integrations


Never put business logic inside API routes.

---

# AI Pipeline Rules

The AI pipeline is the core of Structra.

Pipeline:

Document

↓

Extraction

↓

Cleaning

↓

Segmentation

↓

Idea extraction

↓

Classification

↓

Entity extraction

↓

Relationship extraction

↓

Validation

↓

Knowledge storage


---

# Knowledge Extraction Rules

Never summarize documents.

Never merge unrelated concepts.

Each knowledge object represents exactly one idea.

Bad:

{
"content":"Manager validates requests and HR validates expensive requests"
}


Good:

Idea 1:

Manager validates requests.


Idea 2:

HR validates requests above a threshold.


---

# JSON Knowledge Object Requirements

Every object should contain:

- id
- type
- title
- normalized_statement
- original_text
- entities
- actors
- actions
- conditions
- constraints
- exceptions
- relationships
- confidence_score
- source_reference


---

# AI Safety

Never trust raw LLM outputs.

Every AI response must:

- validate schema
- pass quality checks
- contain traceability information


Always keep:

- original text
- generated interpretation
- confidence score

---

# Code Standards

## TypeScript

- Strict mode enabled
- Never use any
- Use interfaces/types
- Validate external data


## Python

- Type hints required
- Pydantic models required
- Async when possible
- Small functions


---

# Security Rules

Never expose:

- API keys
- secrets
- environment variables


Always implement:

- authentication
- authorization
- tenant isolation
- input validation
- file security checks


---

# Database Rules

Use Supabase PostgreSQL as the source of truth.

Store:

- users
- organizations
- documents
- knowledge objects
- relationships
- audit events


Do not store important business data only in vector databases.

---

# Development Rules

Before creating a feature:

1. Understand existing architecture.
2. Reuse existing components.
3. Avoid unnecessary dependencies.
4. Update documentation.


---

# Testing

Every important feature requires:

- unit tests
- validation tests
- AI evaluation examples


AI extraction quality must be measurable.

---

# Documentation

Keep documentation updated.

Important files:

- README.md
- docs/architecture.md
- docs/json-schema.md
- docs/ai-pipeline.md

---

# Main Objective

Build Structra into an enterprise-grade knowledge extraction engine capable of powering secure AI assistants.
