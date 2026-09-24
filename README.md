# Dupay — Fintech Platform (Microservices Architecture)

## Project Overview

A scalable fintech platform built with a microservices architecture for transaction processing, wallet operations, KYC workflows, and secure authentication. Includes a mobile application with real-time transaction updates, notifications, and account management.

## Key Features

- Scalable microservices and REST APIs (Python, Django, DRF)
- Transaction processing and wallet operations
- KYC (Know Your Customer) workflows
- Secure authentication with JWT and RBAC
- Mobile app (React Native, Redux) with real-time updates
- Event-driven communication (Kafka, Celery, Redis, WebSockets)
- Live risk monitoring and alerting

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| Backend | Python, Django, Django REST Framework |
| Mobile | React Native, Redux |
| Messaging | Apache Kafka, Celery, Redis, WebSockets |
| Database | PostgreSQL |
| Infrastructure | Docker, GCP, API Gateway |
| Security | JWT authentication, RBAC |

## Project Structure

```
dupay-financial-platform/
├── services/
│   ├── api-gateway/       # API Gateway entry point
│   ├── auth-service/      # Authentication & RBAC
│   ├── transaction-service/ # Transaction processing
│   ├── wallet-service/    # Wallet operations
│   ├── kyc-service/       # KYC workflows
│   ├── notification-service/  # Notifications (WS/email/push)
│   └── risk-service/      # Live risk monitoring
├── mobile/                # React Native app
├── docs/                  # Architecture documentation
├── specs/                 # Specifications and development guidelines
└── docker-compose.yml     # Local orchestrations
```

## Development Workflow

- **Weekly**: 1 project milestone per week
- **Daily**: 1 code push per day (minimum)

## Quick Start

1. Clone the repository
2. Run `docker compose up -d` to start dependencies (Kafka, Redis, PostgreSQL)
3. Start services individually (`python manage.py runserver` per service)
4. Run mobile app from `mobile/` directory

## License

Private