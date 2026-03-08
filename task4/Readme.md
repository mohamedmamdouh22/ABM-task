# Task 4 — System Architecture Diagram

A comprehensive architecture diagram for a distributed browser-automation system at scale, covering message queuing, worker orchestration, data persistence, monitoring, and failover.

## View

Open `architecture_diagram.html` in any browser — no dependencies or build step required.

## What's covered

### Ingress
API Gateway (rate limiting, auth, TLS) → Load Balancer (L4-L7, health checks) → Task Dispatcher (priority routing) → WebSocket/SSE real-time push

### Message Queue — RabbitMQ
- Primary node + HA Mirror (quorum queues, auto-sync)
- `tasks.queue` — main automation work
- `retry.queue` — dead-letter + TTL for failed tasks
- `priority.queue` — high/low priority routing
- Dead Letter Exchange for tasks that exceed max retries

### Worker Nodes
- Horizontally scaled via Kubernetes HPA
- Each worker runs: Playwright browser + captcha solver + result publisher
- Scale-out triggered by queue depth; scale-in on idle timeout

### Data Layer
- PostgreSQL Primary (write) + Read Replica (streaming replication, failover candidate)
- Redis for caching and rate-limit counters (Sentinel HA)

### Monitoring
- **Prometheus** — metrics scraping every 15s
- **Grafana** — dashboards for health, load, and errors
- **System Health service** — liveness/readiness probes and heartbeats
- **Current Load service** — queue depth, worker utilization, CPU/MEM/latency
- **ELK Stack** — Elasticsearch + Logstash + Kibana for structured error logging
- **Alertmanager** — routes alerts to PagerDuty, Slack, and Email

### Failover & Recovery
- Circuit Breaker (open/closed/half-open, auto-reset after 60s)
- DB auto-failover via Patroni (replica promotion in < 30s)
- Worker crash recovery — Kubernetes restart + NACK → `retry.queue`
- Exponential backoff retry (1s → 2s → 4s, max 5 retries)
- Daily backups + WAL archiving to S3 (RPO: 5 min, RTO: 30 min)
- Multi-region Active-Passive with Route53 DNS failover
