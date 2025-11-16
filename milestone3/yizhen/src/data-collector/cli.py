import argparse
from google.cloud import storage
import json

def copy_dataset(source_uri, target_bucket):
    """Copy all files from a GCS path to our workflow bucket."""
    client = storage.Client()

    # parse source
    src_bucket_name, src_prefix = source_uri.replace("gs://", "").split("/", 1)
    src_bucket = client.bucket(src_bucket_name)
    blobs = list(src_bucket.list_blobs(prefix=src_prefix))

    dest_bucket = client.bucket(target_bucket)

    for blob in blobs:
        print(f"Copying {blob.name} ...")
        dest_blob = dest_bucket.blob(f"dnd-data/{blob.name.split('/')[-1]}")
        dest_blob.rewrite(blob)

    print("✅ Dataset copied successfully!")

def verify_jsonl_format(gcs_uri):
    """Download one JSONL file and check required keys."""
    client = storage.Client()
    bucket_name, blob_name = gcs_uri.replace("gs://", "").split("/", 1)
    blob = client.bucket(bucket_name).blob(blob_name)
    content = blob.download_as_text().splitlines()
    first_line = json.loads(content[0])
    print("🔍 Example keys in dataset:", list(first_line.keys()))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source_uri", required=True,
                        help="Source GCS folder (e.g. gs://dnd-master-dataset/dnd-narrator-finetune-dataset/)")
    parser.add_argument("--target_bucket", required=True,
                        help="Destination bucket (e.g. ac215-ml-workflow)")
    args = parser.parse_args()

    copy_dataset(args.source_uri, args.target_bucket)
    verify_jsonl_format(args.source_uri + "train.jsonl")
