# =========================
# DnD Narrator Fine-Tuning (Vertex AI Gemini, SDK ≥ 1.126)
# =========================

import os
import time
import argparse
import vertexai
from vertexai.generative_models import GenerativeModel
from vertexai.preview import tuning

# InputOutputTextPair moved between SDK modules across versions.
# Prefer the stable location and provide fallbacks for older/newer SDKs.
try:
    from vertexai.language_models import InputOutputTextPair
except Exception:
    try:
        from vertexai.preview.generative_models import InputOutputTextPair
    except Exception:
        # Final fallback: preview.language_models (some SDK snapshots)
        from vertexai.preview.language_models import InputOutputTextPair


# -----------------------------
# ✅ Default Environment Config
# -----------------------------
PROJECT_ID = os.getenv("GCP_PROJECT", "even-turbine-471117-u0")
LOCATION = os.getenv("GCP_REGION", "us-central1")
BASE_MODEL = os.getenv("BASE_MODEL", "gemini-1.5-flash-002")

# ✅ 训练数据路径（如果你有 GCS 文件）
TRAIN_DATASET = os.getenv(
    "TRAIN_DATASET",
    "gs://ac215-ml-workflow-central1/dnd-ml-dataset-clean/train_clean.jsonl",
)
VALIDATION_DATASET = os.getenv(
    "VALIDATION_DATASET",
    "gs://ac215-ml-workflow-central1/dnd-ml-dataset-clean/validation_clean.jsonl",
)

# -----------------------------
# Initialize Vertex AI
# -----------------------------
vertexai.init(project=PROJECT_ID, location=LOCATION)


# -----------------------------
# 🚀 Start Fine-Tuning Job
# -----------------------------
def train_model(epochs=3, lr=1.0, wait=False):
    """Start a Vertex AI Gemini fine-tuning job."""
    print("\n🚀 Starting DnD Narrator Fine-Tuning Job on Vertex AI...")
    print(f"Project: {PROJECT_ID} | Region: {LOCATION}")
    print(f"Base Model: {BASE_MODEL}")
    print(f"Epochs: {epochs}, LR multiplier: {lr}")

    # ✅ Example: You can load from GCS or provide sample pairs inline
    training_data = [
        InputOutputTextPair(
            input_text="Describe a dragon attacking a village.",
            output_text="The dragon descended from the smoky clouds, its roar shaking the rooftops."
        ),
        InputOutputTextPair(
            input_text="Narrate a knight’s quest for the lost crown.",
            output_text="The knight crossed barren lands under a crimson sky, guided only by faith and memory."
        ),
    ]

    # ✅ 如果你要使用 GCS 文件替代内联数据，可以用：
    # training_data = tuning.TrainingDataset(gcs_uri=TRAIN_DATASET)

    job = tuning.create_tuning_job(
        base_model=BASE_MODEL,
        training_data=training_data,
        epoch_count=epochs,
        learning_rate_multiplier=lr,
        tuned_model_display_name="dnd-narrator-gemini-v2",
    )

    print("\n✅ Fine-tuning job submitted successfully!")
    print(f"Job name: {job.name}")
    print(f"Dashboard: https://console.cloud.google.com/vertex-ai/training?project={PROJECT_ID}")

    if wait:
        monitor_job(job.name)

    return job


# -----------------------------
# 🕒 Monitor Fine-Tuning Job
# -----------------------------
def monitor_job(job_name):
    """持续监控 Vertex AI 模型训练任务状态"""
    print("\n🕒 Monitoring Vertex AI tuning job progress...\n")

    done_states = {"JOB_STATE_SUCCEEDED", "JOB_STATE_FAILED", "JOB_STATE_CANCELLED"}
    client = tuning.get_tuning_job(job_name)

    while True:
        job = tuning.get_tuning_job(job_name)
        print(f"Current state: {job.state}")
        if job.state in done_states:
            print(f"\n🎯 Training finished with state: {job.state}")
            if job.state == "JOB_STATE_SUCCEEDED":
                print(f"Trained model: {job.tuned_model}")
            break
        time.sleep(60)


# -----------------------------
# 🧙 Test the Tuned Model
# -----------------------------
def test_model(model_name=None):
    if not model_name:
        model_name = input(
            "Enter tuned model name (e.g., tunedModels/dnd-narrator-gemini-v2): "
        ).strip()

    print(f"\n🧙 Testing tuned model: {model_name}")
    model = GenerativeModel(model_name)

    query = "Narrate a battle between a dragon and a knight in a dark forest."
    response = model.generate_content(query)

    print("\n=== MODEL OUTPUT ===")
    print(response.text)
    print("======================")


# -----------------------------
# 🧩 CLI Entry Point
# -----------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DnD Narrator Model Fine-Tuning (Gemini SDK ≥1.126)")
    parser.add_argument("--train", action="store_true", help="Launch fine-tuning job on Vertex AI")
    parser.add_argument("--test", action="store_true", help="Test a tuned model")
    parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs")
    parser.add_argument("--lr", type=float, default=1.0, help="Learning rate multiplier")
    parser.add_argument("--wait", action="store_true", help="Wait for job completion")

    args = parser.parse_args()

    if args.train:
        train_model(epochs=args.epochs, lr=args.lr, wait=args.wait)
    elif args.test:
        test_model()
    else:
        parser.print_help()
