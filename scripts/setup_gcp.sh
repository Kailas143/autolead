#!/bin/bash

# GCP Setup Script for Autolead Deployment
# This script prepares the GCP project for Jenkins deployment.

set -e

# Configuration
PROJECT_ID="gen-lang-client-0898802422"
REGION="asia-south1"
REPO_NAME="autolead"
SA_NAME="jenkins-deployer"
KEY_FILE="gcp-key.json"

echo "🚀 Starting GCP setup for project: $PROJECT_ID"

# 1. Set project
gcloud config set project $PROJECT_ID

# 2. Enable APIs
echo "📡 Enabling APIs..."
gcloud services enable \
    artifactregistry.googleapis.com \
    run.googleapis.com \
    cloudscheduler.googleapis.com \
    iam.googleapis.com

# 3. Create Artifact Registry
echo "📦 Creating Artifact Registry..."
if ! gcloud artifacts repositories describe $REPO_NAME --location=$REGION &>/dev/null; then
    gcloud artifacts repositories create $REPO_NAME \
        --repository-format=docker \
        --location=$REGION \
        --description="Autolead Production Images"
else
    echo "✅ Repository $REPO_NAME already exists."
fi

# 4. Create Service Account
echo "👤 Creating Service Account..."
if ! gcloud iam service-accounts describe ${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com &>/dev/null; then
    gcloud iam service-accounts create $SA_NAME --display-name="Jenkins Deployer"
else
    echo "✅ Service account $SA_NAME already exists."
fi

# 5. Assign Roles
echo "🔐 Assigning IAM roles..."
ROLES=(
    "roles/artifactregistry.writer"
    "roles/run.admin"
    "roles/iam.serviceAccountUser"
)

for role in "${ROLES[@]}"; do
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
        --role="$role" --quiet
done

# 6. Generate Key
echo "🔑 Generating service account key..."
if [ ! -f "$KEY_FILE" ]; then
    gcloud iam service-accounts keys create $KEY_FILE \
        --iam-account=${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com
    echo "✅ Key generated: $KEY_FILE"
else
    echo "⚠️ $KEY_FILE already exists. Skipping key generation to avoid duplicates."
fi

echo "--------------------------------------------------"
echo "✅ GCP Setup Complete!"
echo "--------------------------------------------------"
echo "Next steps:"
echo "1. Upload '$KEY_FILE' to Jenkins as a 'Secret File' credential."
echo "2. Create another 'Secret File' in Jenkins for your backend .yaml env vars."
echo "3. Update your Jenkins Pipeline with the credential IDs."
echo "4. Configure Cloud Scheduler to trigger follow-ups (see README)."
