# Deployment Guide for composite-ms1

This guide covers deploying the composite microservice to Google Cloud Platform.

## Option 1: Cloud Run (Recommended - Serverless)

Cloud Run is easier to deploy and manage. It automatically scales and you get a public URL.

### Prerequisites
- Google Cloud SDK installed (`gcloud`)
- Project set up in GCP
- Docker installed (for local testing)

### Step 1: Build and Push Docker Image

```bash
cd /Users/ag/Desktop/final_project/composite-ms1

# Set your GCP project
export PROJECT_ID=your-gcp-project-id
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com

# Build and push to Container Registry
gcloud builds submit --tag gcr.io/$PROJECT_ID/composite-ms1

# Or use Artifact Registry (recommended)
gcloud artifacts repositories create composite-repo \
    --repository-format=docker \
    --location=us-central1
gcloud builds submit --tag us-central1-docker.pkg.dev/$PROJECT_ID/composite-repo/composite-ms1
```

### Step 2: Deploy to Cloud Run

```bash
# Deploy with environment variables for atomic services
gcloud run deploy composite-ms1 \
    --image us-central1-docker.pkg.dev/$PROJECT_ID/composite-repo/composite-ms1 \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --port 8080 \
    --set-env-vars "INTEGRATIONS_SERVICE_URL=http://35.188.76.100:8000,ACTIONS_SERVICE_URL=http://YOUR_ACTIONS_SERVICE_URL,CLASSIFICATION_SERVICE_URL=http://YOUR_CLASSIFICATION_SERVICE_URL,FASTAPIPORT=8080" \
    --memory 512Mi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 10
```

**Important**: Replace:
- `YOUR_ACTIONS_SERVICE_URL` with your actions service URL
- `YOUR_CLASSIFICATION_SERVICE_URL` with your classification service URL

### Step 3: Get Your Public URL

After deployment, you'll get a URL like:
```
https://composite-ms1-xxxxx-uc.a.run.app
```

This is your **public URL** that anyone can access (if you set `--allow-unauthenticated`).

### Step 4: Test Deployment

```bash
# Get the service URL
SERVICE_URL=$(gcloud run services describe composite-ms1 --region us-central1 --format 'value(status.url)')

# Test health endpoint
curl $SERVICE_URL/health

# Test API docs
echo "API Docs: $SERVICE_URL/docs"
```

---

## Option 2: Compute Engine VM (Like integrations-svc-ms2)

If you want to deploy to a VM like your other service (http://35.188.76.100:8000), follow these steps:

### Step 1: Create VM Instance

```bash
# Create VM instance
gcloud compute instances create composite-ms1-vm \
    --zone=us-central1-a \
    --machine-type=e2-medium \
    --image-family=ubuntu-2204-lts \
    --image-project=ubuntu-os-cloud \
    --boot-disk-size=20GB \
    --tags=http-server,https-server

# Get external IP
gcloud compute instances describe composite-ms1-vm \
    --zone=us-central1-a \
    --format='get(networkInterfaces[0].accessConfigs[0].natIP)'
```

### Step 2: Configure Firewall Rules

```bash
# Allow HTTP traffic on port 8002 (or your chosen port)
gcloud compute firewall-rules create allow-composite-ms1 \
    --allow tcp:8002 \
    --source-ranges 0.0.0.0/0 \
    --target-tags http-server \
    --description "Allow HTTP traffic to composite-ms1"
```

**Note**: `source-ranges: 0.0.0.0/0` makes it publicly accessible. Restrict this for production!

### Step 3: SSH into VM and Setup

```bash
# SSH into VM
gcloud compute ssh composite-ms1-vm --zone=us-central1-a

# Once inside VM, run:
sudo apt-get update
sudo apt-get install -y python3-pip git

# Clone your repository
git clone https://github.com/cloudteam4153/composite-ms1.git
cd composite-ms1

# Install dependencies
pip3 install -r requirements.txt

# Set environment variables
export INTEGRATIONS_SERVICE_URL=http://35.188.76.100:8000
export ACTIONS_SERVICE_URL=http://YOUR_ACTIONS_SERVICE_URL
export CLASSIFICATION_SERVICE_URL=http://YOUR_CLASSIFICATION_SERVICE_URL
export FASTAPIPORT=8002

# Run the service
python3 main.py
```

### Step 4: Run as a Service (Optional - for auto-start)

Create a systemd service:

```bash
sudo nano /etc/systemd/system/composite-ms1.service
```

Add:
```ini
[Unit]
Description=Composite Microservice
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/home/your-username/composite-ms1
Environment="INTEGRATIONS_SERVICE_URL=http://35.188.76.100:8000"
Environment="ACTIONS_SERVICE_URL=http://YOUR_ACTIONS_SERVICE_URL"
Environment="CLASSIFICATION_SERVICE_URL=http://YOUR_CLASSIFICATION_SERVICE_URL"
Environment="FASTAPIPORT=8002"
ExecStart=/usr/bin/python3 main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable composite-ms1
sudo systemctl start composite-ms1
sudo systemctl status composite-ms1
```

### Step 5: Access Your Service

Your service will be available at:
```
http://EXTERNAL_IP:8002
```

Get the external IP:
```bash
gcloud compute instances describe composite-ms1-vm \
    --zone=us-central1-a \
    --format='get(networkInterfaces[0].accessConfigs[0].natIP)'
```

---

## Security Considerations

### Cloud Run
- **Public by default** if you use `--allow-unauthenticated`
- To restrict: Remove `--allow-unauthenticated` and use IAM
- Access control via IAM roles

### Compute Engine VM
- **Public IP ≠ Public Access** automatically
- Only accessible if firewall rules allow it
- Restrict `source-ranges` in firewall rules for production
- Example: `--source-ranges YOUR_IP/32` for your IP only

## Quick Deploy Script (Cloud Run)

Save as `deploy.sh`:

```bash
#!/bin/bash

PROJECT_ID="your-gcp-project-id"
REGION="us-central1"
SERVICE_NAME="composite-ms1"

# Set project
gcloud config set project $PROJECT_ID

# Build and deploy
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME

gcloud run deploy $SERVICE_NAME \
    --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --port 8080 \
    --set-env-vars "INTEGRATIONS_SERVICE_URL=http://35.188.76.100:8000,ACTIONS_SERVICE_URL=http://YOUR_ACTIONS_SERVICE_URL,CLASSIFICATION_SERVICE_URL=http://YOUR_CLASSIFICATION_SERVICE_URL,FASTAPIPORT=8080"

# Get URL
echo "Service URL:"
gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)'
```

Make executable and run:
```bash
chmod +x deploy.sh
./deploy.sh
```

## Troubleshooting

### Cloud Run Issues
- Check logs: `gcloud run services logs read composite-ms1 --region us-central1`
- Verify environment variables are set correctly
- Check that atomic services are accessible from Cloud Run

### VM Issues
- Check firewall rules: `gcloud compute firewall-rules list`
- Verify service is running: `sudo systemctl status composite-ms1`
- Check logs: `journalctl -u composite-ms1 -f`

