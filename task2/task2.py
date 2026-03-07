"""
Task 2: Network Interception
-----------------------------
Pure Playwright — no SeleniumBase needed.

1. Open the Turnstile URL with page.route() blocking all Cloudflare/Turnstile
   requests before they load.
2. Capture sitekey, pageaction, cdata, pagedata from intercepted URLs and
   HTML data-attributes.
3. Inject the reserved token from task1/reserved_token.json (captured by task1
   on its last attempt without submitting — keeping it single-use for here).
4. Submit — expects "Success! Turnstile verified".
"""

import json
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from playwright.sync_api import sync_playwright

TURNSTILE_URL = "https://cd.captchaaiplus.com/turnstile.html"
RESERVED_TOKEN_FILE = Path(__file__).parent.parent / "task1" / "reserved_token.json"
RESULTS_FILE = Path(__file__).parent / "task2_results.json"


def load_token() -> str:
    if not RESERVED_TOKEN_FILE.exists():
        raise RuntimeError(
            "task1/reserved_token.json not found — run task1 first "
            "(it reserves the last attempt's token without submitting)."
        )
    token = json.loads(RESERVED_TOKEN_FILE.read_text())["token"]
    return token


def main() -> None:
    print("Task 2 — Network Interception")

    token = load_token()

    captured = {
        "sitekey": None,
        "pageaction": None,
        "cdata": None,
        "pagedata": None,
        "intercepted_urls": [],
    }
    success = False

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        def intercept(route):
            url = route.request.url
            if "challenges.cloudflare.com" in url or "/turnstile/" in url:
                captured["intercepted_urls"].append(url)
                try:
                    params = parse_qs(urlparse(url).query)
                    for qs_key, field in [
                        ("sitekey", "sitekey"),
                        ("action", "pageaction"),
                        ("cdata", "cdata"),
                        ("pagedata", "pagedata"),
                    ]:
                        if qs_key in params and not captured[field]:
                            captured[field] = params[qs_key][0]
                except Exception:
                    pass
                route.abort()
            else:
                route.continue_()

        page.route("**/*", intercept)

        page.goto(TURNSTILE_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(2_000)

        handle = page.query_selector("[data-sitekey], .cf-turnstile")
        if handle:
            captured["sitekey"] = captured["sitekey"] or handle.get_attribute(
                "data-sitekey"
            )
            captured["pageaction"] = captured["pageaction"] or handle.get_attribute(
                "data-action"
            )
            captured["cdata"] = captured["cdata"] or handle.get_attribute("data-cdata")
            captured["pagedata"] = captured["pagedata"] or handle.get_attribute(
                "data-pagedata"
            )

        print(
            f"  Turnstile blocked ({len(captured['intercepted_urls'])} request(s) intercepted)"
        )
        print(f"  sitekey: {captured['sitekey']}")

        page.evaluate(f"""
            () => {{
                let input = document.querySelector('[name="cf-turnstile-response"]');
                if (!input) {{
                    input = document.createElement('input');
                    input.type  = 'hidden';
                    input.name  = 'cf-turnstile-response';
                    document.querySelector('form').appendChild(input);
                }}
                input.value = `{token}`;
            }}
        """)
        print("  Token injected, submitting…")

        for selector in ['input[type="submit"]', 'button[type="submit"]']:
            try:
                page.click(selector, timeout=3_000)
                break
            except Exception:
                continue

        try:
            page.wait_for_selector("text=Turnstile verified", timeout=8_000)
            success = True
            print("  SUCCESS — 'Turnstile verified' ✓")
        except Exception:
            body = page.inner_text("body")
            print(f"  FAILED — body: {body[:300]}")

        page.screenshot(path=str(Path(__file__).parent / "task2_result.png"))
        browser.close()

    results = {**captured, "token_used": token, "success": success}
    RESULTS_FILE.write_text(json.dumps(results, indent=2, default=str))

    print(f"  Result: {'✓ SUCCESS' if results['success'] else '✗ FAILED'}")
    print(f"  Results  → {RESULTS_FILE}")
    print(f"  Screenshot → {Path(__file__).parent / 'task2_result.png'}")


if __name__ == "__main__":
    main()
