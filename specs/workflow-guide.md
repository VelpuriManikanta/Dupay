# Development Workflow Guide

## Daily Push Protocol

### Commit Convention

```
[type]: short description (max 60 chars)

Types:
- feat:     New feature
- fix:      Bug fix
- docs:     Documentation
- style:    Formatting
- refactor: Code refactoring
- test:     Adding/fixing tests
- chore:    Build, deps, tooling
```

### Daily Checklist

1. [ ] `git pull origin main`
2. [ ] Branch: `git checkout -b feature/<service>/<name>`
3. [ ] Make changes
4. [ ] Run tests: `pytest`
5. [ ] Run lint: `flake8 . && black --check .`
6. [ ] Commit: `git commit -m "feat: description"`
7. [ ] Push: `git push origin feature/<service>/<name>`
8. [ ] Create PR

## Weekly Milestones

### Week 1 — Infrastructure
- [ ] Docker Compose for Kafka, Redis, PostgreSQL
- [ ] Service skeletons, CI pipeline
- [ ] API Gateway routing

### Week 2 — Auth
- [ ] auth-service: register/login/refresh
- [ ] JWT + RBAC
- [ ] Gateway JWT validation

### Week 3 — Wallet + Transactions
- [ ] wallet-service: double-entry ledger
- [ ] transaction-service: initiate + status
- [ ] Kafka topics wired

### Week 4 — KYC + Events
- [ ] kyc-service submissions + review
- [ ] Celery async jobs
- [ ] Idempotent consumers

### Week 5 — Risk + Real-time
- [ ] risk-service rule engine
- [ ] WebSocket live monitoring
- [ ] Alert publishing

### Week 6 — Notifications
- [ ] notification-service (WS/email/push)
- [ ] Kafka consumer

### Week 7 — Mobile
- [ ] RN app: auth, wallet, transfer
- [ ] Redux Toolkit + RTK Query
- [ ] Real-time notifications

### Week 8 — Launch
- [ ] Contract tests green
- [ ] GCP deployment
- [ ] Docs, monitoring, final QA

## Git Commands Reference

```bash
# Start new feature
git checkout main
git pull origin main
git checkout -b feature/wallet-service/ledger

# End of day push
git add .
git commit -m "feat: add wallet ledger endpoints"
git push origin feature/wallet-service/ledger
```

## Branch Strategy

```
main (production)
  └── develop (integration)
       ├── feature/auth-service/jwt-rbac
       ├── feature/wallet-service/ledger
       ├── fix/kyc-service/webhook-retry
       └── ...
```