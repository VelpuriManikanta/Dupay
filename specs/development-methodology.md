# Tools & Spec-Driven Development

## Overview

This document defines the development methodology, tools, and specifications for the Dupay Fintech Platform, a microservices architecture.

## Development Methodology

### Spec-Driven Development (SDD)

1. **Write spec first** — define service contracts and requirements before code
2. **Implement to spec** — code must match the API contract
3. **Test against spec** — verify behavior with contract tests
4. **Update spec** — revise specs when business rules change

### Weekly Cadence

| Week | Deliverable | Status |
|------|-------------|--------|
| 1 | Infrastructure: Docker, Kafka, Redis, PostgreSQL | |
| 2 | API Gateway + auth-service (JWT, RBAC) | |
| 3 | wallet-service + transaction-service core | |
| 4 | kyc-service + event-driven integration | |
| 5 | risk-service + WebSocket live monitoring | |
| 6 | notification-service + Celery async jobs | |
| 7 | Mobile app (React Native + Redux) | |
| 8 | Testing, deployment (GCP), docs | |

### Daily Push Protocol

- **Commit message**: `[type]: description`
  - Types: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`
- **Push time**: End of workday
- **Branch naming**: `feature/<service>/<description>`, `fix/<service>/<description>`

## Tools

### Backend Services

| Tool | Purpose | Version |
|------|---------|---------|
| Python | Primary language | 3.12+ |
| Django | Web framework | 4.2+ |
| Django REST Framework | API layer | 3.14+ |
| PostgreSQL | Primary database | 16 |
| Apache Kafka | Event bus | 3.7+ |
| Celery | Async task queue | 5.3+ |
| Redis | Cache + broker | 7+ |
| Channels/WebSockets | Real-time | 4+ |

### Mobile

| Tool | Purpose | Version |
|------|---------|---------|
| React Native | Mobile app framework | 0.74+ |
| Redux Toolkit | State management | 2.x |
| Axios | API client | 1.7+ |
| React Navigation | Routing | 6.x |

### Infrastructure

| Tool | Purpose |
|------|---------|
| Docker Compose | Local orchestration |
| GCP | Cloud deployment |
| API Gateway | Request routing, auth |
| Terraform | Infrastructure as Code |
| Prometheus + Grafana | Monitoring |

### Security

| Tool | Purpose |
|------|---------|
| JWT | Token authentication |
| RBAC | Role-based access control |
| OWASP ZAP | Security scanning |
| Hashicorp Vault | Secrets management |

## Specifications

### API Contract

- RESTful design per service
- OpenAPI 3.0 schemas per service
- Unified error response format
- JWT bearer auth with role claims
- Rate limiting at API Gateway

### Event Contracts

- Kafka topics per domain: `transactions`, `wallets`, `kyc.events`, `notifications`
- Avro/JSON schema registry
- At-least-once delivery semantics
- Idempotent consumer handlers

### Database per Service

- Dedicated PostgreSQL schema per microservice
- No cross-service joins — use events / direct API calls
- Migrations versioned per service

### Security Requirements

- HTTPS everywhere
- JWT with short-lived access + refresh tokens
- RBAC enforced at API Gateway + service level
- PII encrypted at rest (KYC data)
- Audit logging on all wallet/transaction mutations

## Development Workflow

```
1. Create feature branch: feature/<service>/<name>
2. Write/update OpenAPI spec
3. Implement service changes
4. Write tests (unit + contract)
5. Run linting and type checks
6. Create PR referencing spec
7. Code review with service owner
8. Merge to main
9. Deploy to staging via CI/CD
```

## Tracking

- GitHub Issues for task tracking
- Link commits to issues
- Weekly milestone reviews
- Daily standup notes in PR descriptions