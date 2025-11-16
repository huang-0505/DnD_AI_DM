#!/bin/bash
set -e

# ======== Basic Configuration ========
export GCP_PROJECT="even-turbine-471117-u0"
export GCS_PACKAGE_URI="gs://even-turbine-471117-u0/model-training"
export PACKAGE_NAME="dnd-model-trainer"
export PACKAGE_DIR="trainer"
export OUTPUT_TAR="${PACKAGE_NAME}.tar.gz"

echo "============================================"
echo "Packaging Python Trainer for Vertex AI"
echo "Project: $GCP_PROJECT_ID"
echo "Package Directory: $PACKAGE_DIR"
echo "Target URI: $GCS_PACKAGE_URI/$OUTPUT_TAR"
echo "============================================"

# ======== Step 1: Clean Old Files ========
rm -f trainer.tar trainer.tar.gz $OUTPUT_TAR

# ======== Step 2: Create TAR.GZ ========
tar cvf trainer.tar $PACKAGE_DIR
gzip trainer.tar
mv trainer.tar.gz $OUTPUT_TAR

# ======== Step 3: Upload to GCS ========
gsutil cp $OUTPUT_TAR $GCS_PACKAGE_URI/$OUTPUT_TAR

echo "✅ Upload complete!"
echo "Uploaded to → $GCS_PACKAGE_URI/$OUTPUT_TAR"
