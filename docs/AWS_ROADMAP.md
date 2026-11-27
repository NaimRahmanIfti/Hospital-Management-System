# AWS Roadmap: Hospital Management System

The plan for moving HMS from Railway to a production-style AWS setup.
Each phase is something you build, understand, and can explain in an interview.

## Target architecture

```
                         ┌──────────────── AWS (us-west-1) ─────────────────────────────┐
                         │                                                              │
 Browser ──HTTPS──► CloudFront ──► S3 (React build, private)                            │
    │                    │                                                              │
    │                    └──/api──► ALB ──► ECS Fargate (FastAPI container)             │
    │                                           │   │   │                               │
    │                                           │   │   └──► Secrets Manager (JWT key,  │
    │                                           │   │         DB password)            │
    │                                           │   └──────► RDS PostgreSQL (private    │
    │                                           │             subnet, encrypted)        │
    │                                           └──────────► S3 (medical documents,     │
    │                                                         private, SSE encrypted)   │
    └──presigned URL (5 min)───────────────────────────────► S3 documents bucket        │
                                                                                        │
  GitHub Actions ──OIDC (no stored keys)──► ECR (Docker images) ──► ECS deploy          │
  CloudWatch: container logs, alarms on 5xx errors and high CPU                         │
                         └──────────────────────────────────────────────────────────────┘
```

## Why each service (the interview answers)

| Service | Job in HMS | Why this one, not the alternative |
|---|---|---|
| **S3** | Lab reports, scans, and the React site | Pay per GB with 11 nines of durability. Files don't belong in Postgres. |
| **RDS PostgreSQL** | The database | AWS handles backups, patching, and encryption. Postgres running in a container loses its data if the volume is lost. |
| **ECR** | Stores Docker images | Private registry next to ECS. Image pulls stay inside AWS. |
| **ECS Fargate** | Runs the FastAPI container | No servers to patch (unlike EC2). Simpler than Kubernetes (EKS) for one service. |
| **ALB** | HTTPS entry point, health checks | Only sends traffic to healthy containers (it uses `/health`). |
| **CloudFront** | CDN in front of S3 and the API | Caches the frontend near users and serves HTTPS on one domain, so there are no CORS problems. |
| **Secrets Manager** | `SECRET_KEY`, DB password | Secrets are not in code, `.env`, or the image. ECS injects them at startup. |
| **IAM roles** | Permissions | The container's role can access only *this* bucket. There are no access keys anywhere. |
| **CloudWatch** | Logs and alarms | You see errors in production without having to SSH into anything. |
| **Terraform** | Creates all of the above as code | Repeatable, reviewable, and can be torn down with one command. |
| **GitHub Actions + OIDC** | CI/CD | Tests, build, and deploy run on every push. OIDC means no long-lived AWS keys are stored in GitHub. |

## Phases

- [x] **Phase 1: S3 document storage (app code).** `app/core/storage.py` defines a `StorageBackend`
  interface with `LocalStorage` and `S3Storage`. It uploads with SSE encryption, downloads through
  presigned URLs, and uses role-based access. It is tested with `moto`, so no AWS account is needed.
- [ ] **Phase 2: Terraform infrastructure.** VPC, S3 buckets, RDS, ECR, ECS Fargate, ALB,
  Secrets Manager, IAM, CloudWatch log group.
- [ ] **Phase 3: CI/CD.** A GitHub Actions workflow runs pytest, then builds and pushes to ECR,
  then deploys to ECS. A second job builds the frontend, syncs it to S3, and invalidates CloudFront.
- [ ] **Phase 4: Production hardening.** Alembic migrations (replacing `create_all`), structured JSON
  logs, CloudWatch alarms, S3 lifecycle rules, and RDS automated backups.
- [ ] **Phase 5 (optional): Amazon SES** for appointment confirmation emails.

## Cost (be careful)

A small always-on setup costs roughly **$40–60/month** if you have no credits: ALB about $16, RDS
`db.t4g.micro` about $12–15, Fargate 0.25 vCPU about $9, plus small amounts for S3 and CloudWatch.
New AWS accounts get Free Tier credits; check the current terms on the AWS Free Tier page.
To keep costs down:

1. **Create a billing alarm first** (Billing → Budgets → $10 budget with an email alert).
2. Don't create a NAT Gateway (about $32/month). The plan puts Fargate tasks in public subnets
   with security groups that accept traffic only from the ALB.
3. `terraform destroy` when you're not demoing. `terraform apply` brings everything back in about 10 minutes.

## Resume bullets (write them only after you've built each phase)

- Deployed a containerized FastAPI + React hospital management system on **AWS (ECS Fargate, RDS
  PostgreSQL, S3, CloudFront, ALB)**, with all infrastructure defined in **Terraform**.
- Built HIPAA-minded medical document storage on **S3** with server-side encryption, private buckets,
  and 5-minute **presigned URLs** gated by role-based access control.
- Built a **GitHub Actions** CI/CD pipeline that uses **OIDC federation** (no stored AWS keys) to test,
  build, push to **ECR**, and roll out zero-downtime ECS deployments.
- Kept secrets in **AWS Secrets Manager** and gave each service a least-privilege **IAM role**.
  Monitored the system with **CloudWatch** logs and alarms.
