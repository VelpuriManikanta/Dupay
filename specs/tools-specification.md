# Tools Specification

## Service Stack

### API Gateway

```yaml
technology: nginx / GCP API Gateway
features:
  - JWT validation
  - Rate limiting (100 req/min per user)
  - Request routing to internal services
  - CORS handling
```

### auth-service

```yaml
python: 3.12
django: 4.2
packages:
  - djangorestframework
  - djangorestframework-simplejwt
  - django-axes (brute force protection)
  - cryptography
models:
  - User (extended)
  - Role
  - Permission
  - UserRole mapping
endpoints:
  - POST /auth/register
  - POST /auth/login
  - POST /auth/refresh
  - POST /auth/logout
  - GET  /auth/me
```

### wallet-service

```yaml
python: 3.12
django: 4.2
packages:
  - djangorestframework
  - django-redis
models:
  - Wallet
  - LedgerEntry
  - WalletTransaction
endpoints:
  - GET  /wallets/{user_id}
  - POST /wallets/{user_id}/deposit
  - POST /wallets/{user_id}/withdraw
  - GET  /wallets/{user_id}/ledger
features:
  - Double-entry ledger
  - Transactional integrity
  - Idempotency keys on all mutations
```

### transaction-service

```yaml
python: 3.12
django: 4.2
kafka: true
celery: true
models:
  - Transaction (status: PENDING/SUCCESS/FAILED)
  - TransactionEvent
endpoints:
  - POST /transactions       (initiate)
  - GET  /transactions/{id}  (status)
  - GET  /transactions       (list w/ filters)
flows:
  - Consume kafka topic 'transactions'
  - Async processing via Celery
  - Publish events to 'transactions.status'
```

### kyc-service

```yaml
python: 3.12
django: 4.2
packages:
  - django-environ
  - requests (vendor API integration)
models:
  - KycSubmission (status: PENDING/APPROVED/REJECTED)
  - KycDocument
  - KycVerification (vendor responses)
endpoints:
  - POST /kyc/submissions
  - GET  /kyc/submissions/{id}
  - POST /kyc/submissions/{id}/review
flows:
  - Webhook ingestion from vendor
  - Publish kyc.events on status change
```

### notification-service

```yaml
python: 3.12
django: 4.2
channels: 4 (WebSockets)
celery: true
features:
  - WebSocket endpoint for real-time push
  - Email + push notifications via Celery
  - Consume 'notifications' kafka topic
```

### risk-service

```yaml
python: 3.12
django: 4.2
kafka: true
features:
  - Real-time transaction monitoring
  - Rule engine (velocity, amount, geo)
  - Publish alerts on suspicious patterns
  - Dashboards via Prometheus metrics
```

### Mobile App (React Native)

```yaml
react-native: 0.74
redux: "@reduxjs/toolkit"
packages:
  - axios
  - @react-navigation/native
  - @react-navigation/stack
  - react-native-keychain (token storage)
  - react-native-splash-screen
screens:
  - Login / Register
  - Wallet (balance, transactions)
  - Transfer (send/receive)
  - Notifications (real-time)
  - Profile (KYC status)
state:
  - Redux Toolkit slices per domain
  - RTK Query for API caching
  - WebSocket listener for live events
```

## Infrastructure Configuration

### docker-compose.yml (local)

```yaml
version: "3.8"

services:
  postgres:
    image: postgres:16
    env:
      POSTGRES_DB: dupay
      POSTGRES_USER: dupay
      POSTGRES_PASSWORD: dupay_secret
    ports: ["5432:5432"]

  redis:
    image: redis:7
    ports: ["6379:6379"]

  kafka:
    image: confluentinc/cp-kafka:7.7
    ports: ["9092:9092"]

  zookeeper:
    image: confluentinc/cp-zookeeper:7.7
    ports: ["2181:2181"]

  gateway:
    build: ./services/api-gateway
    ports: ["8080:80"]
    depends_on: [auth-service, wallet-service, transaction-service, kyc-service]
```

### CI/CD Pipeline (GitHub Actions)

```yaml
name: deploy

on:
  push:
    branches: [main]

jobs:
  test:
    - setup python 3.12
    - pip install -r requirements.txt
    - run pytest per service

  build:
    - build docker image per service
    - push to GCR

  deploy:
    - terraform apply (infra)
    - deploy services to GCP Cloud Run / GKE
```

## Monitoring Stack

| Tool | Purpose |
|------|---------|
| Prometheus | Metrics collection |
| Grafana | Dashboards |
| Loki | Log aggregation |
| Sentry | Error tracking |

## Testing Strategy

| Level | Tool | Scope |
|-------|------|-------|
| Unit | pytest | Domain logic, validators |
| API | DRF APITestCase / pytest-django | Endpoint contract |
| Contract | pact | Cross-service contracts |
| Integration | testcontainers / docker | Kafka, Redis, DB flows |
| E2E | jest + detox | Mobile flows |