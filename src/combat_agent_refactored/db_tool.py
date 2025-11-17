"""
db_tool.py
Utilities to create and manage embedding databases for action/target retrieval.
Uses Google GenAI for text embeddings and cosine similarity for semantic search.
"""

import os
import json
import argparse
import numpy as np
import pandas as pd
from google import genai
from google.genai import types
from typing import List, Optional


# ========== Configuration ==========
class DBConfig:
    """Configuration for database and embedding settings."""

    def __init__(self):
        # GCP Settings (from environment variables)
        self.gcp_project = os.environ.get("GCP_PROJECT")
        if not self.gcp_project:
            raise ValueError("GCP_PROJECT environment variable must be set")

        self.gcp_location = os.environ.get("GCP_LOCATION", "us-central1")

        # Model Settings
        self.embedding_model = "text-embedding-004"
        self.embedding_dimension = 256
        self.generative_model = "gemini-2.0-flash-001"

        # Default Paths
        self.input_dir = "input"
        self.output_dir = "output"


# ========== Embedding Generator ==========
class EmbeddingGenerator:
    """Handles text embedding generation using Google GenAI."""

    def __init__(self, config: DBConfig):
        self.config = config
        self.client = genai.Client(
            vertexai=True,
            project=config.gcp_project,
            location=config.gcp_location
        )

    def generate_batch(self, texts: List[str], batch_size: int = 100) -> np.ndarray:
        """Generate embeddings for a list of texts in batches."""
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            response = self.client.models.embed_content(
                model=self.config.embedding_model,
                contents=batch,
                config=types.EmbedContentConfig(
                    output_dimensionality=self.config.embedding_dimension
                ),
            )
            all_embeddings.extend([e.values for e in response.embeddings])

        return np.array(all_embeddings)

    def generate_single(self, query: str) -> np.ndarray:
        """Generate embedding for a single query string."""
        response = self.client.models.embed_content(
            model=self.config.embedding_model,
            contents=query,
            config=types.EmbedContentConfig(
                output_dimensionality=self.config.embedding_dimension
            ),
        )
        return np.array(response.embeddings[0].values)


# ========== Similarity Calculator ==========
def cosine_similarity(query_emb: np.ndarray, corpus_embs: np.ndarray) -> np.ndarray:
    """Calculate cosine similarity between query and corpus embeddings."""
    query_norm = query_emb / np.linalg.norm(query_emb)
    corpus_norm = corpus_embs / np.linalg.norm(corpus_embs, axis=1, keepdims=True)
    return np.dot(corpus_norm, query_norm)


# ========== Database Manager ==========
class DatabaseManager:
    """Manages embedding database creation, loading, and retrieval."""

    def __init__(self, config: DBConfig):
        self.config = config
        self.generator = EmbeddingGenerator(config)

    def create_database(self, input_file: str, output_file: str):
        """
        Load JSON data, generate embeddings, and save to JSONL format.

        Args:
            input_file: Path to input JSON file with structured data
            output_file: Path to output JSONL file for embeddings
        """
        # Load input data
        with open(input_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Prepare texts and IDs
        texts = []
        ids = []

        for item in data:
            ids.append(item["id"])
            # Concatenate all fields except 'id' into a single text
            text = " ".join([f"{k}: {v}" for k, v in item.items() if k != "id" and v])
            texts.append(text.strip())

        print(f"📥 Loaded {len(texts)} entries from {input_file}")

        # Generate embeddings
        print(f"🔄 Generating embeddings...")
        embeddings = self.generator.generate_batch(texts).tolist()

        # Save to JSONL
        df = pd.DataFrame({"id": ids, "text": texts, "embedding": embeddings})
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        df.to_json(output_file, orient="records", lines=True, force_ascii=False)

        print(f"✅ Saved embeddings to {output_file}")

    def retrieve_top_k(self, query: str, embeddings_file: str, k: int = 5) -> List[int]:
        """
        Retrieve top-k most similar entries for a given query.

        Args:
            query: Natural language query string
            embeddings_file: Path to JSONL file with embeddings
            k: Number of top results to return

        Returns:
            List of IDs for top-k most similar entries
        """
        # Load embeddings database
        df = pd.read_json(embeddings_file, lines=True)
        embeddings = np.vstack(df["embedding"].values)

        # Generate query embedding
        query_emb = self.generator.generate_single(query)

        # Calculate similarities
        sims = cosine_similarity(query_emb, embeddings)

        # Get top-k indices
        topk_idx = np.argsort(sims)[-k:][::-1]

        # Return top-k IDs
        results = df.iloc[topk_idx].copy()
        results["score"] = sims[topk_idx]

        return results['id'].tolist()


# ========== Convenience Functions ==========
def retrieve_top_k(query: str, embeddings_file: str = "output/embeddings-actions.jsonl",
                   k: int = 5) -> List[int]:
    """
    Convenience function for quick retrieval without config setup.

    Args:
        query: Natural language query
        embeddings_file: Path to embeddings database
        k: Number of results to return

    Returns:
        List of top-k IDs
    """
    config = DBConfig()
    db_manager = DatabaseManager(config)
    return db_manager.retrieve_top_k(query, embeddings_file, k)


# ========== CLI Interface ==========
def main():
    """Command-line interface for database operations."""
    parser = argparse.ArgumentParser(description="DnD Combat Agent Database Tool")

    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Embed command
    embed_parser = subparsers.add_parser("embed", help="Generate embeddings for JSON data")
    embed_parser.add_argument("--input", required=True, help="Input JSON file path")
    embed_parser.add_argument("--output", required=True, help="Output JSONL file path")

    # Retrieve command
    retrieve_parser = subparsers.add_parser("retrieve", help="Retrieve top-k similar entries")
    retrieve_parser.add_argument("--query", required=True, help="Query string")
    retrieve_parser.add_argument("--file", required=True, help="Embeddings JSONL file")
    retrieve_parser.add_argument("--k", type=int, default=5, help="Number of results (default: 5)")

    args = parser.parse_args()

    # Initialize config and manager
    config = DBConfig()
    db_manager = DatabaseManager(config)

    # Execute command
    if args.command == "embed":
        db_manager.create_database(args.input, args.output)

    elif args.command == "retrieve":
        results = db_manager.retrieve_top_k(args.query, args.file, args.k)
        print(f"\n🔍 Top {args.k} results for: '{args.query}'")
        print(f"IDs: {results}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
