# 🧙‍♂️ DnD Master AI — Milestone 2

## Overview
This project is part of **AC215: Applied Deep Learning Systems** at Harvard.  
Our team is building an **AI Dungeon Master (DM)** that can narrate, guide, and manage interactive *Dungeons & Dragons* adventures.

The **Milestone 2** branch focuses on the **containerization and deployment setup** across the full system — including the **frontend**, **backend**, **RAG orchestrator**, and **finetuning pipeline**.  
Each module runs independently in Docker and communicates through internal networking defined in `docker-compose.yml`.

The frontend stack includes:
- ⚛️ **Next.js 14 (App Router)**
- 🟦 **TypeScript**
- 🎨 **TailwindCSS + shadcn/ui**
- 📦 **pnpm** for fast, reproducible package management
- 🐳 **Docker** for containerized deployment

---

## ⚙️ Features
- 🎮 Interactive React-based player interface for the AI DM  
- ⚙️ FastAPI-based backend API for orchestrating requests and managing session logic  
- 🔁 RAG (Retrieval-Augmented Generation) pipeline for contextually enriched storytelling  
- 🧠 Model finetuning environment for iterative improvements  
- 🧩 Modular multi-container setup using **Docker Compose**  
- 🌐 Unified routing through **Nginx reverse proxy**

---

## 🧰 Project Structure
```text
AC215-DnD-Master/
├── frontend/                  # Next.js 14 app for player interaction
│   ├── app/
│   ├── components/
│   ├── lib/
│   ├── public/
│   ├── styles/
│   ├── package.json
│   ├── pnpm-lock.yaml
│   └── Dockerfile             # SSR build for production
│
├── src/
│   ├── datapipeline/          # Data preprocessing & training pipelines
│   │   ├── dataloader.py
│   │   ├── preprocess_cv.py
│   │   ├── preprocess_rag.py
│   │   ├── Dockerfile
│   │   └── Pipfile
│   │
│   ├── models/                # Model training, inference, and RAG modules
│   │   ├── train_model.py
│   │   ├── model_rag.py
│   │   ├── infer_model.py
│   │   ├── Dockerfile
│   │   └── docker-shell.sh
│   │
│   └── orchestrator/          # FastAPI orchestration and agent routing
│       ├── app.py
│       ├── requirements.txt
│       └── Dockerfile
│
├── infra/
│   └── nginx.conf             # Reverse proxy configuration for / and /api
│
├── docker-compose.yml         # Multi-container compose for all modules
├── LICENSE
└── README.md
```
---

## 🐳 Docker Setup

### 1️⃣ Build and Run (frontend only)
```bash
docker compose up --build
```
Then open:
👉 http://localhost:3000

This starts the production Next.js SSR server inside a container.

### 2️⃣ Stop the containers

Press Ctrl + C, or run:
```bash
docker compose down
```
