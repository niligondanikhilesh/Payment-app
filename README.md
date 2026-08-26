# PayQuick

A Flask-based payment API with PostgreSQL and Redis, containerized and monitored with a full DevSecOps pipeline.

## Stack
- **App**: Python / Flask
- **Database**: PostgreSQL
- **Cache**: Redis
- **Monitoring**: Prometheus + Grafana
- **CI/CD**: GitHub Actions
- **Security**: Trivy vulnerability scanning
- **Infrastructure**: Terraform (see [payquick-infra](https://github.com/niligondanikhilesh/payquick-infra))

## Endpoints
- `GET /` — health check
- `POST /pay` — process a payment
- `GET /transactions` — list transactions
- `GET /balance/<user>` — get a user's balance
- `GET /metrics` — Prometheus metrics endpoint

## Running locally
```bash
docker-compose up --build
```
This starts the app, PostgreSQL, Redis, Prometheus, and Grafana together.

- App: `http://localhost:5000`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000`

## CI/CD Pipeline
Every push to `main` triggers a 3-stage pipeline via GitHub Actions:

1. **Test** — installs dependencies and verifies the app imports cleanly
2. **Security scan** — runs Trivy against the built Docker image, checking for known CRITICAL/HIGH vulnerabilities
3. **Deploy** — SSHs into the production EC2 instance, pulls the latest code, and redeploys via Docker Compose

See `.github/workflows/ci.yml` for the full pipeline definition.

## Monitoring & Incident Response
The app exposes request count, latency, and error-rate metrics via `/metrics`, scraped by Prometheus and visualized in Grafana.

A simulated database outage was used to validate observability: stopping the `postgres` container while the app was running produced a clear, isolated 500-error spike in the error-rate dashboard, while unrelated endpoints (like `/metrics`) remained healthy — confirming the monitoring setup correctly distinguishes a dependency failure from a full outage.
