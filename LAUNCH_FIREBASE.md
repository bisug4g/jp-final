# 🔥 JAYTI — Firebase Launch Guide
## Deploy to Firebase Hosting + Google Cloud Run + Cloud SQL

**Architecture:**
```
Browser → Firebase Hosting (jaytibirthday.in, SSL, CDN, static files)
               ↓  rewrites
          Cloud Run  (Django + WhiteNoise, asia-south1 / Mumbai)
               ↓
          Cloud SQL PostgreSQL  (asia-south1, private IP via Unix socket)
               ↓
          Firebase Storage  (Tangred wardrobe photos)
```

---

## Prerequisites

- Google account with a Firebase project already created (`jayti-c7605`)
- `gcloud` CLI installed: https://cloud.google.com/sdk/docs/install
- `firebase` CLI installed: `npm install -g firebase-tools`
- Docker (only for local testing — Cloud Build handles production builds)

---

## Step 1 — Enable Google Cloud APIs

```bash
gcloud config set project jayti-c7605

gcloud services enable \
  run.googleapis.com \
  sqladmin.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  secretmanager.googleapis.com \
  firebase.googleapis.com \
  storage.googleapis.com
```

---

## Step 2 — Create Artifact Registry (Docker image storage)

```bash
gcloud artifacts repositories create jayti \
  --repository-format=docker \
  --location=asia-south1 \
  --description="Jayti app Docker images"
```

---

## Step 3 — Create Cloud SQL (PostgreSQL)

```bash
# Create the instance (~5 min)
gcloud sql instances create jayti-db \
  --database-version=POSTGRES_16 \
  --tier=db-f1-micro \
  --region=asia-south1 \
  --storage-type=SSD \
  --storage-size=10GB \
  --storage-auto-increase \
  --no-backup \
  --availability-type=ZONAL

# Create the database
gcloud sql databases create jayti --instance=jayti-db

# Create a database user (choose a strong password)
gcloud sql users create jayti \
  --instance=jayti-db \
  --password=REPLACE_WITH_STRONG_PASSWORD
```

The **Cloud SQL connection name** (needed later) is:
```
jayti-c7605:asia-south1:jayti-db
```

The `DATABASE_URL` for Cloud Run (Unix socket format):
```
postgresql://jayti:REPLACE_WITH_STRONG_PASSWORD@/jayti?host=/cloudsql/jayti-c7605:asia-south1:jayti-db
```

---

## Step 4 — Store Secrets in Secret Manager

Never put secrets in Cloud Build or Cloud Run environment variables as plain text.
Use Secret Manager instead:

```bash
# Helper function
create_secret() {
  echo -n "$2" | gcloud secrets create "$1" --data-file=-
}

# Generate Django secret key first
DJANGO_KEY=$(python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")

create_secret jayti-secret-key        "$DJANGO_KEY"
create_secret jayti-database-url      "postgresql://jayti:YOUR_DB_PASS@/jayti?host=/cloudsql/jayti-c7605:asia-south1:jayti-db"
create_secret jayti-username          "jayati"
create_secret jayti-password          "REPLACE_WITH_STRONG_PASSWORD"
create_secret jayti-gemini-key        "YOUR_GEMINI_API_KEY"
create_secret jayti-emergent-key      "YOUR_EMERGENT_API_KEY"

# VAPID keys — generate first:
python scripts/generate_vapid_keys.py
# then:
create_secret jayti-vapid-private     "YOUR_VAPID_PRIVATE_KEY"
create_secret jayti-vapid-public      "YOUR_VAPID_PUBLIC_KEY"

# Firebase web config (from Firebase console → Project settings → Your apps)
create_secret jayti-firebase-api-key          "YOUR_FIREBASE_API_KEY"
create_secret jayti-firebase-app-id          "YOUR_FIREBASE_APP_ID"
create_secret jayti-firebase-project-id      "jayti-c7605"

# Firebase Admin SDK (from Firebase console → Project settings → Service accounts → Generate new private key)
create_secret jayti-firebase-private-key      "$(cat firebase-adminsdk-key.json | python -c "import json,sys; k=json.load(sys.stdin); print(k['private_key'])")"
create_secret jayti-firebase-client-email     "$(cat firebase-adminsdk-key.json | python -c "import json,sys; k=json.load(sys.stdin); print(k['client_email'])")"
```

**Grant Cloud Run access to secrets:**
```bash
PROJECT_NUMBER=$(gcloud projects describe jayti-c7605 --format='value(projectNumber)')

gcloud projects add-iam-policy-binding jayti-c7605 \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

---

## Step 5 — Update `cloudbuild.yaml` with your secrets

Open `cloudbuild.yaml` and **uncomment** the `--update-secrets` lines in the
`deploy-cloudrun` step, replacing them with your actual secret names:

```yaml
- --update-secrets=SECRET_KEY=jayti-secret-key:latest
- --update-secrets=DATABASE_URL=jayti-database-url:latest
- --update-secrets=INITIAL_USERNAME=jayti-username:latest
- --update-secrets=INITIAL_PASSWORD=jayti-password:latest
- --update-secrets=GEMINI_API_KEY=jayti-gemini-key:latest
- --update-secrets=EMERGENT_API_KEY=jayti-emergent-key:latest
- --update-secrets=VAPID_PRIVATE_KEY=jayti-vapid-private:latest
- --update-secrets=VAPID_PUBLIC_KEY=jayti-vapid-public:latest
- --update-secrets=FIREBASE_API_KEY=jayti-firebase-api-key:latest
- --update-secrets=FIREBASE_APP_ID=jayti-firebase-app-id:latest
- --update-secrets=FIREBASE_PROJECT_ID=jayti-firebase-project-id:latest
- --update-secrets=FIREBASE_PRIVATE_KEY=jayti-firebase-private-key:latest
- --update-secrets=FIREBASE_CLIENT_EMAIL=jayti-firebase-client-email:latest
```

Also set `_CLOUDSQL_INST` substitution:
```yaml
substitutions:
  _CLOUDSQL_INST: jayti-c7605:asia-south1:jayti-db
```

---

## Step 6 — Create Cloud Build Trigger

```bash
gcloud builds triggers create github \
  --name=jayti-deploy \
  --repo-name=jp \
  --repo-owner=YOUR_GITHUB_USERNAME \
  --branch-pattern='^main$' \
  --build-config=cloudbuild.yaml \
  --region=global
```

**Grant Cloud Build permissions:**
```bash
PROJECT_NUMBER=$(gcloud projects describe jayti-c7605 --format='value(projectNumber)')
CB_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"

# Cloud Run Admin
gcloud projects add-iam-policy-binding jayti-c7605 \
  --member="serviceAccount:${CB_SA}" --role="roles/run.admin"

# Cloud SQL Client
gcloud projects add-iam-policy-binding jayti-c7605 \
  --member="serviceAccount:${CB_SA}" --role="roles/cloudsql.client"

# Artifact Registry Writer
gcloud projects add-iam-policy-binding jayti-c7605 \
  --member="serviceAccount:${CB_SA}" --role="roles/artifactregistry.writer"

# Secret Manager Accessor
gcloud projects add-iam-policy-binding jayti-c7605 \
  --member="serviceAccount:${CB_SA}" --role="roles/secretmanager.secretAccessor"

# Firebase Hosting Admin
gcloud projects add-iam-policy-binding jayti-c7605 \
  --member="serviceAccount:${CB_SA}" --role="roles/firebasehosting.admin"

# Service Account User (needed to deploy Cloud Run)
gcloud projects add-iam-policy-binding jayti-c7605 \
  --member="serviceAccount:${CB_SA}" \
  --role="roles/iam.serviceAccountUser"
```

---

## Step 7 — First Deploy

```bash
# Log in to Firebase and Google Cloud
firebase login
gcloud auth login

# Push to main — Cloud Build picks it up automatically
git add -A
git commit -m "chore: firebase deployment"
git push origin main
```

Watch the build at:
https://console.cloud.google.com/cloud-build/builds?project=jayti-c7605

The pipeline:
1. Builds the Docker image (~3 min)
2. Pushes to Artifact Registry
3. Runs Django deploy-check inside the image
4. Deploys to Cloud Run (sets up DB connection, env vars, Cloud SQL proxy)
5. Collects static files
6. Deploys Firebase Hosting (serves static files from CDN)

**First boot:** Cloud Run runs `entrypoint.sh` which:
- Runs `python manage.py migrate` (creates all tables)
- Creates the initial user from `INITIAL_USERNAME` / `INITIAL_PASSWORD`
- Seeds welcome notes and diary entry

---

## Step 8 — Custom Domain (jaytibirthday.in)

### Firebase Hosting domain
```bash
firebase hosting:channel:deploy live --project jayti-c7605

# Add custom domain in Firebase console:
# Hosting → Add custom domain → jaytibirthday.in
# Firebase gives you two A records (or a CNAME for www)
```

Or via CLI:
```bash
firebase hosting:sites:list
# Then go to Firebase Console → Hosting → Add custom domain
```

In your DNS registrar, add:
```
Type    Name    Value
A       @       151.101.1.195     ← Firebase provides these IPs
A       @       151.101.65.195
CNAME   www     jayti-c7605.web.app
```

SSL is auto-provisioned by Firebase within ~15 minutes.

### Map domain to Cloud Run (for direct access)
```bash
gcloud beta run domain-mappings create \
  --service=jayti \
  --domain=jaytibirthday.in \
  --region=asia-south1
```

---

## Step 9 — Verify Everything

```bash
# Health check
curl https://jaytibirthday.in/health
# → {"status": "healthy", "timestamp": "..."}

# Check Cloud Run logs
gcloud run services logs read jayti --region=asia-south1 --limit=50

# Check static files are being served by Firebase CDN
curl -I https://jaytibirthday.in/static/css/custom.css
# → x-served-by: cache-... (Firebase CDN header)
```

---

## Step 10 — Supabase Keep-Alive → Cloud SQL Scheduled Job

Cloud SQL doesn't pause like Supabase, so the keepalive command is not strictly
needed. But you can set up a Cloud Scheduler job for periodic health pings:

```bash
# Create a Cloud Scheduler job that pings the health endpoint every 5 days
gcloud scheduler jobs create http jayti-keepalive \
  --schedule="0 12 */5 * *" \
  --uri="https://jaytibirthday.in/health" \
  --http-method=GET \
  --location=asia-south1 \
  --description="Keep Jayti app warm"
```

---

## Cost Estimate (per month)

| Service | Tier | Est. Cost |
|---------|------|-----------|
| Cloud Run | ~100 req/day, 0 min instances | **Free** (within free tier) |
| Cloud SQL db-f1-micro | Always on | ~$7–10 |
| Artifact Registry | <1 GB images | **Free** |
| Firebase Hosting | <1 GB storage + transfer | **Free** |
| Secret Manager | <6 secrets | **Free** |
| Cloud Build | <120 min/day | **Free** |

**Total: ~$7–10/month** (almost entirely Cloud SQL)

> 💡 To save cost: set Cloud SQL to stop at night via a scheduler, or migrate to
> Supabase free tier with the keepalive cron (see `LAUNCH.md`).

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| 500 on first request after deploy | Cold start, DB migration running | Wait 30s and refresh |
| `DISALLOWED_HOST` error | Service URL not in ALLOWED_HOSTS | Set `DEPLOYMENT_URL=https://jayti-xxx-uc.a.run.app` env var |
| Static files 404 | collectstatic step failed in Cloud Build | Check Cloud Build logs step 5a |
| `connection refused` to DB | Cloud SQL instance not attached | Verify `--add-cloudsql-instances` flag and `_CLOUDSQL_INST` substitution |
| Push notifications not working | VAPID keys missing | Verify secrets `jayti-vapid-private` and `jayti-vapid-public` exist |
| AI features return 503 | API key missing or wrong | Check `jayti-gemini-key` or `jayti-emergent-key` in Secret Manager |
| Firebase deploy fails in CI | Cloud Build SA lacks firebasehosting.admin | Run the IAM grant command in Step 6 |

---

## Rollback

```bash
# List recent Cloud Run revisions
gcloud run revisions list --service=jayti --region=asia-south1

# Roll back to a specific revision
gcloud run services update-traffic jayti \
  --to-revisions=jayti-00005-xxx=100 \
  --region=asia-south1
```

---

*Made with 💕 for Jayti — Happy Birthday!*
