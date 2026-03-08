# ABM Tasks

Browser automation and system design assessment covering Cloudflare bypass, network interception, DOM scraping, and distributed architecture.

---

## Task 1 — Cloudflare Turnstile Stealth Automation

**File:** `task1/task1.py`

Bypasses Cloudflare Turnstile CAPTCHA using SeleniumBase in undetected-Chrome mode, connected to Playwright via CDP for token extraction.

**Approach:**

- Runs 10 attempts split across two sessions: 5 headed (`headless=False`) and 5 headless (`headless=True`)
- SeleniumBase handles Turnstile solving; Playwright handles navigation and token extraction from the hidden `cf-turnstile-response` input
- The final attempt reserves the token without submitting, saving it to `reserved_token.json` for use by Task 2
- Pass threshold: ≥60% success rate

**Outputs:**

- `task1/results.json` — success rates and collected tokens
- `task1/reserved_token.json` — single-use token passed to Task 2
- `task1/screenshot_attempt_XX.png` — screenshot per attempt

---

## Task 2 — Network Interception

**File:** `task2/task2.py`

Intercepts and blocks Cloudflare/Turnstile network requests, then injects the reserved token from Task 1 to submit the form without triggering the challenge.

**Approach:**

- Uses `page.route()` to intercept all outgoing requests matching `challenges.cloudflare.com` or `/turnstile/`, aborting them before they load
- Extracts CAPTCHA parameters (`sitekey`, `pageaction`, `cdata`, `pagedata`) from intercepted URLs and DOM data-attributes
- Injects the reserved token directly into the hidden form field via `page.evaluate()`
- Submits the form and waits for the "Turnstile verified" confirmation

**Outputs:**

- `task2/task2_results.json` — captured parameters and success status
- `task2/task2_result.png` — screenshot of the final page state

---

## Task 3 — DOM Scraping Assessment

**File:** `task3/task3.py`

Scrapes the BLS Spain CAPTCHA page to extract all images and identify which ones are actually visible to the user.

**Approach:**

- Intercepts network responses to capture images as base64 before they load into the DOM
- Scrapes all `img.captcha-img` elements and records `src`, `alt`, dimensions, and base64 data
- Applies a strict visibility check: element must be visible, have non-trivial dimensions, be within the viewport, and be the topmost element at its center point (`document.elementFromPoint`)
- Also extracts visible text labels from `.box-label` elements

**Outputs:**

- `task3/allimages.json` — every image found in the DOM with base64 data
- `task3/visible_images_only.json` — only the images a human would actually see
- `task3/screenshot.png` — full-page screenshot for visual reference

---

## Task 4 — System Architecture Diagram

**File:** `task4/system_design.png`

Comprehensive architecture diagram for a distributed browser-automation system at scale.

**Components covered:**

| Layer | Components |
|---|---|
| Ingress | API Gateway, Load Balancer, Task Dispatcher |
| Message Queue | RabbitMQ Primary + HA Mirror, `tasks.queue`, `retry.queue`, `priority.queue`, Dead Letter Exchange |
| Workers | Horizontally scaled worker nodes (Playwright + captcha solver), Kubernetes HPA auto-scaling |
| Data | PostgreSQL Primary + Read Replica, Redis cache |
| Monitoring | Prometheus, Grafana, System Health service, Current Load service, ELK Stack, Alertmanager |
| Failover | Circuit Breaker, DB auto-failover (Patroni), message persistence, exponential backoff retry, multi-region DNS failover |

Open `task4/system_design.png`.

---

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install seleniumbase playwright
playwright install chromium
```

**Run order:**

```bash
python task1/task1.py   # generates reserved_token.json
python task2/task2.py   # requires task1 to have run first
python task3/task3.py   # independent
```
