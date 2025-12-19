# Longevity Protocol Validator 🧬

A **Retrieval-Augmented Generation (RAG)** engine for validating longevity interventions against scientific literature. Built to demonstrate **hallucination-resistant** AI architecture in the Biotech domain.

**Live Demo:** [https://longevity-protocol-validator-1.onrender.com/](https://longevity-protocol-validator-1.onrender.com/)

## The Problem

Generic LLMs (ChatGPT) often "hallucinate" scientific facts or reference non-existent studies. In the field of Human Longevity (e.g., Rapamycin, Metformin), accuracy is critical. Researchers need tools that **synthesize** conflict and consensus rather than just summarizing text.

## Architecture

This application utilizes a **Split-Screen Insight Engine**:

- **Left Panel:** Structured AI Analysis (Consensus vs. Conflict).
- **Right Panel:** Real-time Evidence Board (Direct citations to source abstracts).

### Tech Stack

- **Frontend:** Angular 17+ (Standalone Components), TailwindCSS, Nginx (Dockerized).
- **Backend:** Python FastAPI, Pydantic (Structured Output).
- **AI/ML:** LangChain, OpenAI GPT-4o, OpenAI Embeddings.
- **Data Sources:** PubMed, OpenAlex, Europe PMC, CrossRef (400M+ papers).
- **Infrastructure:** Render (CI/CD), Docker Multi-Stage Builds.

## Key Features

1.  **Structured Intelligence:** Uses Pydantic to force the LLM into a strict schema (`Consensus`, `Conflict`, `Limitations`), preventing unstructured rambling.
2.  **Evidence Board:** Dynamically parses citation context to display source abstracts side-by-side with the AI response.
3.  **Strict Guardrails:** System prompts tuned to refuse answers when evidence is absent (Temperature 0).

## Quick Start (Local)

### Prerequisites

- Docker & Docker Compose
- Node.js 18+
- Python 3.10+ (Poetry)
