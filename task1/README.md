# Task 1 — Cloudflare Turnstile Stealth Automation

Bypasses Cloudflare Turnstile CAPTCHA using SeleniumBase in undetected-Chrome mode, connected to Playwright via CDP for token extraction.

## How it works

SeleniumBase launches a stealth Chromium instance and exposes it via CDP. Playwright connects to that same browser session to handle navigation and read the solved token from the hidden `cf-turnstile-response` input.

Runs 10 attempts across two sessions:

- **Attempts 1–5** — `headless=False` (visible browser)
- **Attempts 6–10** — `headless=True`

The final attempt (attempt 10) skips form submission and saves the token to `reserved_token.json` for Task 2 to use.

Pass threshold: **≥ 60% success rate**

## Run

```bash
python task1/task1.py
```

## Outputs

| File | Description |
| --- | --- |
| `results.json` | Success rates and all collected tokens |
| `reserved_token.json` | Single-use token reserved for Task 2 |
| `screenshot_attempt_XX.png` | Screenshot captured after each attempt |
