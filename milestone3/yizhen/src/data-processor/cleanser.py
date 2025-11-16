import os
import json
from typing import List, Dict
from google.cloud import storage

GCP_PROJECT = os.getenv("GCP_PROJECT_ID", "ac215")
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "ac215-ml-workflow")


RAW_PREFIX = "dnd-ml-dataset"
CLEAN_PREFIX = "dnd-ml-dataset-clean"

def _get_client() -> storage.Client:
    return storage.Client(project=GCP_PROJECT)

def _read_jsonl(bucket: storage.Bucket, blob_name: str) -> List[Dict]:
    blob = bucket.blob(blob_name)
    if not blob.exists():
        raise FileNotFoundError(f"❌ File not found: gs://{bucket.name}/{blob_name}")

    print(f"📥 Reading: gs://{bucket.name}/{blob_name}")
    text = blob.download_as_text()
    data = []
    for i, line in enumerate(text.strip().split("\n")):
        if not line.strip():
            continue
        try:
            data.append(json.loads(line))
        except json.JSONDecodeError as e:
            print(f"⚠️ Line {i+1}: invalid JSON ({e})")
    print(f"✅ Loaded {len(data)} samples.")
    return data

def _write_jsonl(bucket: storage.Bucket, blob_name: str, data: List[Dict]):
    print(f"📤 Writing {len(data)} records → gs://{bucket.name}/{blob_name}")
    blob = bucket.blob(blob_name)
    blob.upload_from_string(
        "\n".join(json.dumps(x, ensure_ascii=False) for x in data),
        content_type="application/jsonl",
    )
    print("✅ Upload complete.\n")


def clean_records(records: List[Dict]) -> List[Dict]:

    cleaned = []
    for r in records:
        c = r.get("contents")
        if not isinstance(c, list) or len(c) < 2:
            continue
        try:
            user = c[0]["parts"][0]["text"].strip()
            model = c[1]["parts"][0]["text"].strip()
            if user and model:
                cleaned.append(r)
        except Exception:
            continue
    print(f"🧹 Cleaned: {len(cleaned)}/{len(records)} samples kept.\n")
    return cleaned

def process_split(bucket: storage.Bucket, split: str):
    src_blob = f"{RAW_PREFIX}/{split}.jsonl"
    dst_blob = f"{CLEAN_PREFIX}/{split}_clean.jsonl"
    print(f"=== Processing {split} split ===")
    raw = _read_jsonl(bucket, src_blob)
    cleaned = clean_records(raw)
    _write_jsonl(bucket, dst_blob, cleaned)

def run_cleaning():
    print("🚀 Running DnD dataset cleaning pipeline ...")
    print(f"   Project: {GCP_PROJECT}")
    print(f"   Bucket: gs://{GCS_BUCKET_NAME}")

    client = _get_client()
    bucket = client.bucket(GCS_BUCKET_NAME)

    for split in ["train", "validation"]:
        process_split(bucket, split)

    print("🎯 Cleaning complete!")
    print(f"Output → gs://{GCS_BUCKET_NAME}/{CLEAN_PREFIX}/")

if __name__ == "__main__":
    run_cleaning()
