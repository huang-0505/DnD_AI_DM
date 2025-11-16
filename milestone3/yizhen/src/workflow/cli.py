"""
CLI launcher for DnD Narrator MLOps workflow on Vertex AI.
"""

import os
import argparse
import random
import string
from kfp import dsl, compiler
import google.cloud.aiplatform as aip
from model import model_training as model_training_job, model_deploy as model_deploy_job


# ======== Environment Variables ========
GCP_PROJECT = os.getenv("GCP_PROJECT", "even-turbine-471117-u0")
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "ac215-ml-workflow-central1")
BUCKET_URI = f"gs://{GCS_BUCKET_NAME}"
PIPELINE_ROOT = f"{BUCKET_URI}/pipeline_root/root"
GCS_SERVICE_ACCOUNT = os.getenv(
    "GCS_SERVICE_ACCOUNT", "ml-workflow@even-turbine-471117-u0.iam.gserviceaccount.com"
)
GCS_PACKAGE_URI = os.getenv(
    "GCS_PACKAGE_URI", f"gs://{GCS_BUCKET_NAME}/model-training"
)
GCP_REGION = os.getenv("GCP_REGION", "us-central1")

# Docker images (可以自定义你的container)
DATA_COLLECTOR_IMAGE = "dlops/dnd-data-collector"
DATA_PROCESSOR_IMAGE = "dlops/dnd-data-processor"


# ======== Utility ========
def generate_uuid(length: int = 8) -> str:
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))


# ======== 1️⃣ Data Collector ========
def data_collector():
    print("🚀 Launching DnD Data Collector pipeline...")

    @dsl.container_component
    def data_collector_component():
        return dsl.ContainerSpec(
            image=DATA_COLLECTOR_IMAGE,
            command=[],
            args=[
                "cli.py",
                "--search",
                "--nums", "20",
                "--query", "dragon battle dungeon tavern magic",  # ✅ DnD主题关键词
                "--bucket", GCS_BUCKET_NAME,
            ],
        )

    @dsl.pipeline(name="dnd-data-collector-pipeline")
    def data_collector_pipeline():
        data_collector_component()

    compiler.Compiler().compile(data_collector_pipeline, package_path="data_collector.yaml")

    aip.init(project=GCP_PROJECT, staging_bucket=BUCKET_URI)

    job_id = generate_uuid()
    display_name = f"dnd-data-collector-{job_id}"

    job = aip.PipelineJob(
        display_name=display_name,
        template_path="data_collector.yaml",
        pipeline_root=PIPELINE_ROOT,
        enable_caching=False,
    )

    job.run(service_account=GCS_SERVICE_ACCOUNT)
    print(f"✅ Data Collector job submitted! View here: "
          f"https://console.cloud.google.com/vertex-ai/pipelines?project={GCP_PROJECT}")


# ======== 2️⃣ Model Training ========
def model_training():
    print("🚀 Launching DnD Model Training Job...")

    @dsl.pipeline(name="dnd-model-training-pipeline")
    def model_training_pipeline():
        model_training_job(
            project=GCP_PROJECT,
            location=GCP_REGION,
            staging_bucket=GCS_PACKAGE_URI,
            bucket_name=GCS_BUCKET_NAME,
        )

    compiler.Compiler().compile(model_training_pipeline, package_path="model_training.yaml")

    aip.init(project=GCP_PROJECT, staging_bucket=BUCKET_URI)
    job_id = generate_uuid()
    display_name = f"dnd-model-training-{job_id}"

    job = aip.PipelineJob(
        display_name=display_name,
        template_path="model_training.yaml",
        pipeline_root=PIPELINE_ROOT,
        enable_caching=False,
    )

    job.run(service_account=GCS_SERVICE_ACCOUNT, sync=False)
    print(f"✅ Training job submitted! View here: "
          f"https://console.cloud.google.com/vertex-ai/training?project={GCP_PROJECT}")


# ======== 3️⃣ Model Deployment ========
def model_deploy():
    print("🚀 Launching DnD Model Deployment Job...")

    @dsl.pipeline(name="dnd-model-deploy-pipeline")
    def model_deploy_pipeline():
        model_deploy_job(bucket_name=GCS_BUCKET_NAME)

    compiler.Compiler().compile(model_deploy_pipeline, package_path="model_deploy.yaml")

    aip.init(project=GCP_PROJECT, staging_bucket=BUCKET_URI)
    job_id = generate_uuid()
    display_name = f"dnd-model-deploy-{job_id}"

    job = aip.PipelineJob(
        display_name=display_name,
        template_path="model_deploy.yaml",
        pipeline_root=PIPELINE_ROOT,
        enable_caching=False,
    )

    job.run(service_account=GCS_SERVICE_ACCOUNT)
    print(f"✅ Deploy job submitted! View here: "
          f"https://console.cloud.google.com/vertex-ai/models?project={GCP_PROJECT}")


# ======== 4️⃣ Full Pipeline ========
def pipeline():
    print("🚀 Launching full DnD MLOps pipeline...")

    @dsl.pipeline(name="dnd-full-pipeline")
    def dnd_pipeline():
        data_collector_task = (
            dsl.ContainerSpec(
                image=DATA_COLLECTOR_IMAGE,
                command=[],
                args=[
                    "cli.py",
                    "--search",
                    "--nums", "20",
                    "--query", "dragon quest magic tavern knight",
                    "--bucket", GCS_BUCKET_NAME,
                ],
            )
        )

        model_training_task = model_training_job(
            project=GCP_PROJECT,
            location=GCP_REGION,
            staging_bucket=GCS_PACKAGE_URI,
            bucket_name=GCS_BUCKET_NAME,
        )

        model_deploy_job(bucket_name=GCS_BUCKET_NAME).after(model_training_task)

    compiler.Compiler().compile(dnd_pipeline, package_path="pipeline.yaml")

    aip.init(project=GCP_PROJECT, staging_bucket=BUCKET_URI)
    job_id = generate_uuid()
    display_name = f"dnd-full-pipeline-{job_id}"

    job = aip.PipelineJob(
        display_name=display_name,
        template_path="pipeline.yaml",
        pipeline_root=PIPELINE_ROOT,
        enable_caching=False,
    )

    job.run(service_account=GCS_SERVICE_ACCOUNT)
    print(f"✅ Full pipeline submitted! View here: "
          f"https://console.cloud.google.com/vertex-ai/pipelines?project={GCP_PROJECT}")


# ======== CLI Entrypoint ========
def main(args=None):
    print("CLI Arguments:", args)

    if args.data_collector:
        data_collector()

    if args.model_training:
        model_training()

    if args.model_deploy:
        model_deploy()

    if args.pipeline:
        pipeline()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DnD Narrator MLOps CLI")

    parser.add_argument("--data_collector", action="store_true", help="Run data collector job")
    parser.add_argument("--model_training", action="store_true", help="Run model training job")
    parser.add_argument("--model_deploy", action="store_true", help="Run model deployment job")
    parser.add_argument("--pipeline", action="store_true", help="Run full DnD pipeline")

    args = parser.parse_args()
    main(args)
