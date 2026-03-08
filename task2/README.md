# Task 2 — Network Interception

Intercepts and blocks all Cloudflare/Turnstile network requests, then injects the reserved token from Task 1 to submit the form without ever triggering the challenge.

## How it works

Uses Playwright's `page.route()` to intercept every outgoing request. Any request matching `challenges.cloudflare.com` or `/turnstile/` is aborted before it loads. Parameters are extracted from the blocked URLs and DOM data-attributes, then the reserved token is injected directly into the hidden form field via `page.evaluate()`.

**Requires Task 1 to have run first** — reads `task1/reserved_token.json`.

## Run

```bash
python task2/task2.py
```

## Outputs

| File | Description |
| --- | --- |
| `task2_results.json` | Captured parameters (`sitekey`, `pageaction`, `cdata`, `pagedata`) and success status |
| `task2_result.png` | Screenshot of the final page state after submission |

## What gets captured

- `sitekey` — Turnstile site key extracted from intercepted URLs or DOM
- `pageaction` — action value from the challenge config
- `cdata` / `pagedata` — additional challenge parameters
- `intercepted_urls` — list of all blocked Cloudflare request URLs
