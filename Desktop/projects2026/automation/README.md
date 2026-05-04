# ⚡ Nexus Sync — Enterprise Automation Suite

**Developed by Ashish Kumar**

An enterprise-grade, fully automated data synchronization and reporting system for JJM (Jal Jeevan Mission) SCADA operations — built with a production DevOps pipeline.

---

## 🏗️ Project Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Developer (Ashish Kumar)                                    │
│  git push → main branch                                     │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  GitHub Actions CI/CD Pipeline                              │
│  1. Validate (pyflakes syntax check)                        │
│  2. Build EXE (windows-latest runner + PyInstaller)         │
│  3. Upload EXE → AWS S3 (versioned + latest.exe)           │
│  4. Build Docker Image → AWS ECR                           │
│  5. Deploy Container → AWS ECS (Fargate)                   │
└────────────────────┬────────────────────────────────────────┘
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
┌─────────────────┐   ┌─────────────────────┐
│   AWS S3        │   │   AWS ECS (Fargate)  │
│  (EXE Hosting)  │   │  Control Tower API   │
│  latest.exe     │   │  devash.in           │
└─────────────────┘   └─────────────────────┘
                                │
                                ▼
                  ┌─────────────────────────┐
                  │   5 Client Machines      │
                  │   NexusSyncPro.exe       │
                  │   Auto-checks updates    │
                  │   License verified       │
                  └─────────────────────────┘
```

---

## 🚀 DevOps Stack

| Layer | Technology |
|---|---|
| Source Control | GitHub (branching: `dev` → `staging` → `main`) |
| CI/CD | GitHub Actions |
| Containerization | Docker + Docker Compose |
| Container Registry | AWS ECR |
| Deployment | AWS ECS (Fargate) |
| Artifact Storage | AWS S3 |
| Monitoring | AWS CloudWatch |
| Domain | devash.in (GoDaddy → AWS ALB) |

---

## 📦 Repository Structure

```
automation/
├── NexusSyncPro_Advanced.py      # Main Desktop Application
├── NexusSyncPro_Advanced.spec    # PyInstaller build config
├── WhatsApp_Nexus_Bot/
│   └── NexusBot.py               # Telegram Bot
├── Nexus_Control_Tower/
│   ├── server.py                 # FastAPI backend (OTA + Licensing)
│   ├── admin.py                  # Admin CLI (key management)
│   └── requirements.txt
├── Dockerfile                    # Multi-stage Docker build
├── docker-compose.yml            # Local dev environment
└── .github/
    └── workflows/
        └── ci-cd.yml             # Full CI/CD pipeline
```

---

## ⚙️ GitHub Secrets Required

Add these in: **GitHub → Repository → Settings → Secrets → Actions**

| Secret Name | Description |
|---|---|
| `AWS_ACCESS_KEY_ID` | Your AWS IAM Access Key |
| `AWS_SECRET_ACCESS_KEY` | Your AWS IAM Secret Key |

---

## 🖥️ Local Development

```bash
# Start the Control Tower locally with Docker
docker-compose up --build

# Access the web portal
http://localhost:8000

# Run the admin CLI
python Nexus_Control_Tower/admin.py
```

---

## 📋 Branching Strategy

| Branch | Purpose | Auto-Deploy |
|---|---|---|
| `dev` | Active development | Build only (no deploy) |
| `staging` | Pre-release testing | Docker image built and pushed |
| `main` | Production release | Full pipeline: EXE → S3, Docker → ECS |
