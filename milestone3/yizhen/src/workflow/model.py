from kfp import dsl


# ===========================================================
# 🧠 DnD Narrator Model Training Component
# ===========================================================
@dsl.component(
    base_image="python:3.11",
    packages_to_install=[
        "google-cloud-aiplatform>=1.43.0",
        "google-cloud-storage>=2.16.0",
        "pandas>=2.0.0",
        "numpy>=1.24.0",
        "scikit-learn>=1.3.0",
        "tensorflow==2.13.1",
        "transformers>=4.35.0",
    ],
)
def model_training(
    project: str = "",
    location: str = "",
    staging_bucket: str = "",
    bucket_name: str = "",
    epochs: int = 3,
    batch_size: int = 8,
    lr: float = 2e-5,
    model_name: str = "bert-base-uncased",
    job_display_name: str = "dnd-narrator-finetune",
):
    import google.cloud.aiplatform as aip

    print("🚀 Starting DnD Narrator Model Training Job...")
    print(f"Project: {project}")
    print(f"Region: {location}")
    print(f"Bucket: {bucket_name}")
    print(f"Model: {model_name}")

    # Initialize Vertex AI SDK
    aip.init(project=project, location=location, staging_bucket=staging_bucket)

    # Vertex AI base container for fine-tuning (PyTorch or TensorFlow)
    container_uri = "us-docker.pkg.dev/vertex-ai/training/pytorch-xla.2-1.py310:latest"

    # Python package (tar.gz) path in GCS
    python_package_gcs_uri = f"{staging_bucket}/dnd-model-trainer.tar.gz"

    # Create the Vertex AI Custom Job
    job = aip.CustomPythonPackageTrainingJob(
        display_name=job_display_name,
        python_package_gcs_uri=python_package_gcs_uri,
        python_module_name="trainer.task",
        container_uri=container_uri,
        project=project,
    )

    # Custom training arguments
    CMDARGS = [
        f"--epochs={epochs}",
        f"--batch_size={batch_size}",
        f"--lr={lr}",
        f"--model_name={model_name}",
        f"--bucket_name={bucket_name}",
    ]

    MODEL_DIR = f"gs://{bucket_name}/trained_models/{job_display_name}"

    print(f"📦 Training package: {python_package_gcs_uri}")
    print(f"💾 Output directory: {MODEL_DIR}")
    print(f"🧩 Running fine-tuning on: {model_name}")

    # Run the Vertex AI Custom Training Job
    job.run(
        model_display_name=job_display_name,
        args=CMDARGS,
        replica_count=1,
        machine_type="n1-standard-8",
        base_output_dir=MODEL_DIR,
        sync=False,
    )

    print("✅ Fine-tuning job submitted successfully!")
    print(f"View job in Vertex AI Console: https://console.cloud.google.com/vertex-ai/training?project={project}")


# ===========================================================
# 🚀 DnD Narrator Model Deployment Component
# ===========================================================
@dsl.component(
    base_image="python:3.11",
    packages_to_install=["google-cloud-aiplatform>=1.43.0"],
)
def model_deploy(
    project: str = "",
    location: str = "",
    bucket_name: str = "",
    model_display_name: str = "dnd-narrator-finetune",
):
    import google.cloud.aiplatform as aip

    print("🚀 Deploying DnD Narrator Model to Vertex AI Endpoint...")

    aip.init(project=project, location=location)

    # Path to trained model artifacts
    artifact_uri = f"gs://{bucket_name}/trained_models/{model_display_name}"

    # Pre-built container for TensorFlow Serving
    serving_container_image_uri = "us-docker.pkg.dev/vertex-ai/prediction/tf2-cpu.2-13:latest"

    # Upload model
    model = aip.Model.upload(
        display_name=model_display_name,
        artifact_uri=artifact_uri,
        serving_container_image_uri=serving_container_image_uri,
        sync=True,
    )

    print("✅ Model uploaded to Vertex AI successfully.")

    # Deploy to endpoint
    endpoint = model.deploy(
        deployed_model_display_name=f"{model_display_name}-endpoint",
        machine_type="n1-standard-4",
        min_replica_count=1,
        max_replica_count=1,
        sync=True,
    )

    print(f"✅ Model deployed successfully at endpoint: {endpoint.resource_name}")
    print(f"View endpoint in console: https://console.cloud.google.com/vertex-ai/endpoints?project={project}")
