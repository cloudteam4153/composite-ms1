#!/bin/bash

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-your-gcp-project-id}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="composite-ms1"

# Atomic service URLs (update these!)
INTEGRATIONS_URL="${INTEGRATIONS_SERVICE_URL:-http://35.188.76.100:8000}"
ACTIONS_URL="${ACTIONS_SERVICE_URL:-http://YOUR_ACTIONS_SERVICE_URL}"
CLASSIFICATION_URL="${CLASSIFICATION_SERVICE_URL:-http://YOUR_CLASSIFICATION_SERVICE_URL}"

echo "=========================================="
echo "Deploying composite-ms1 to Cloud Run"
echo "=========================================="
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Service: $SERVICE_NAME"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ Error: gcloud CLI not found. Install it from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Set project
echo "Setting GCP project..."
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "Enabling required APIs..."
gcloud services enable run.googleapis.com cloudbuild.googleapis.com --quiet

# Build and push Docker image
echo "Building and pushing Docker image..."
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME

# Deploy to Cloud Run
echo "Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --port 8080 \
    --set-env-vars "INTEGRATIONS_SERVICE_URL=$INTEGRATIONS_URL,ACTIONS_SERVICE_URL=$ACTIONS_URL,CLASSIFICATION_SERVICE_URL=$CLASSIFICATION_URL" \
    --memory 512Mi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 10

# Get service URL
echo ""
echo "=========================================="
echo "✅ Deployment complete!"
echo "=========================================="
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)' 2>/dev/null)
if [ ! -z "$SERVICE_URL" ]; then
    echo "Service URL: $SERVICE_URL"
    echo ""
    echo "Test endpoints:"
    echo "  Health: $SERVICE_URL/health"
    echo "  API Docs: $SERVICE_URL/docs"
else
    echo "Run this to get the URL:"
    echo "  gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)'"
fi

