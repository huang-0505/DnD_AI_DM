"""
CLI launcher for DnD Narrator Model Training on Vertex AI.

Example:
    python cli.py --train
"""

import os
import argparse
import random
import string
from google.cloud import aiplatform as aip
from google.oauth2 import service_account


# ======== Environment Variables ========
# ======== Environment Variables ========
# ======== Environment Variables ========
GCP_PROJECT = os.getenv("GCP_PROJECT", "even-turbine-471117-u0")   # ✅ 你的项目ID
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "ac215-ml-workflow-central1")
GCS_PACKAGE_URI = f"gs://{GCS_BUCKET_NAME}/model-training"
GCP_REGION = os.getenv("GCP_REGION", "us-central1")
CREDENTIALS_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "/Users/yz/Desktop/secrets/ml-workflow.json")


# ======== Utility Functions ========
def generate_uuid(length: int = 8) -> str:
    """Generate a random alphanumeric job ID."""
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))


# ======== Main Logic ========
def main(args=None):
    if args.train:
        print("\n🚀 Launching DnD Model Training Job on Vertex AI ...")

        # Debug environment info
        print(f"DEBUG Project: {GCP_PROJECT}")
        print(f"DEBUG Region: {GCP_REGION}")
        print(f"DEBUG Package URI: {GCS_PACKAGE_URI}")
        print(f"DEBUG Bucket: {GCS_BUCKET_NAME}")
        print(f"DEBUG Credentials Path: {CREDENTIALS_PATH}")

        # Explicitly load credentials
        try:
            credentials = service_account.Credentials.from_service_account_file(CREDENTIALS_PATH)
            print("✅ Service account credentials loaded successfully.")
        except Exception as e:
            print(f"❌ Failed to load credentials: {e}")
            return

        # Initialize Vertex AI
        aip.init(
            project=GCP_PROJECT,
            location=GCP_REGION,
            staging_bucket=GCS_PACKAGE_URI,
            credentials=credentials,
        )
        print("DEBUG: aip.init() called successfully.")

        # Generate Job ID and setup parameters
        job_id = generate_uuid()
        display_name = f"dnd_model_training_{job_id}"

        container_uri = "us-docker.pkg.dev/vertex-ai/training/tf-cpu.2-14.py310:latest"
        python_package_gcs_uri = f"{GCS_PACKAGE_URI}/dnd-model-trainer.tar.gz"

        print(f"DEBUG: Using container: {container_uri}")
        print(f"DEBUG: Using Python package: {python_package_gcs_uri}")

        # Define training job
        job = aip.CustomPythonPackageTrainingJob(
            display_name=display_name,
            python_package_gcs_uri=python_package_gcs_uri,
            python_module_name="trainer.task",
            container_uri=container_uri,
            project=GCP_PROJECT,
            location=GCP_REGION,
        )

        CMDARGS = [
            "--epochs=3",
            "--batch_size=16",
            "--lr=0.001",
            f"--bucket_name={GCS_BUCKET_NAME}",
        ]
        MODEL_DIR = f"gs://{GCS_BUCKET_NAME}/trained_models/{job_id}"
        MACHINE_TYPE = "n1-standard-4"

        print(f"\n📦 Training package: {python_package_gcs_uri}")
        print(f"🧩 Job display name: {display_name}")
        print(f"💾 Output directory: {MODEL_DIR}")
        print(f"🧠 Starting Vertex AI training job...\n")
        print(f"DEBUG: Submitting job with args: {CMDARGS}")

        # Submit job
        try:
            job.run(
                model_display_name=None,
                args=CMDARGS,
                replica_count=1,
                machine_type=MACHINE_TYPE,
                base_output_dir=MODEL_DIR,
                sync=True,
            )
            print("DEBUG: job.run() executed without exception.")
        except Exception as e:
            print(f"❌ DEBUG: job.run() failed with error: {e}")
            return

        print("\n✅ Vertex AI training job submitted successfully!")
        print(
            f"👉 Check progress in Vertex AI Console: "
            f"https://console.cloud.google.com/vertex-ai/training?project={GCP_PROJECT}"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DnD Model Trainer CLI")

    parser.add_argument(
        "--train",
        action="store_true",
        help="Launch DnD Narrator model training job on Vertex AI",
    )

    args = parser.parse_args()
    main(args)
