"""
Task 1: Automation - Stealth Assessment
---------------------------------------
Uses SeleniumBase SB(uc=True) for stealth + Playwright (sync) connected via
CDP for page interaction. SB handles Turnstile solving, Playwright handles
navigation and token extraction.

Runs 10 attempts total:
  - Attempts 1-5:  headless=False  (single shared browser session)
  - Attempts 6-10: headless=True   (single shared browser session)

"""

import json
from pathlib import Path

from playwright.sync_api import sync_playwright
from seleniumbase import SB

TURNSTILE_URL = "https://cd.captchaaiplus.com/turnstile.html"
NUM_ATTEMPTS = 10
RESULTS_FILE = Path(__file__).parent / "results.json"
RESERVED_TOKEN_FILE = Path(__file__).parent / "reserved_token.json"


def run_attempt_on_page(
    sb, page, attempt_num: int, headless: bool, skip_submit: bool = False
) -> tuple[bool, str | None]:
    mode_label = f"headless={headless}"
    token: str | None = None

    try:
        page.goto(TURNSTILE_URL)
        page.wait_for_load_state("domcontentloaded")

        sb.solve_captcha()

        try:
            page.wait_for_function(
                "() => (document.querySelector('[name=\"cf-turnstile-response\"]')?.value?.length ?? 0) > 20",
                timeout=15_000,
            )
        except Exception:
            pass

        token = page.evaluate(
            "document.querySelector('[name=\"cf-turnstile-response\"]')?.value || null"
        )

        if not token or len(token) < 20:
            print(f"  [{mode_label}] FAILED — no token after solve_captcha()")
            page.screenshot(
                path=str(
                    Path(__file__).parent / f"screenshot_attempt_{attempt_num:02d}.png"
                )
            )
            return False, None

        print(f"  [{mode_label}] Token: {token[:60]}…")

        # Reserve token for Task 2 on the last attempt — skip submit
        if skip_submit:
            print(f"  [{mode_label}] RESERVED for Task 2 (no submit) ✓")
            RESERVED_TOKEN_FILE.write_text(json.dumps({"token": token}, indent=2))
            page.screenshot(
                path=str(
                    Path(__file__).parent / f"screenshot_attempt_{attempt_num:02d}.png"
                )
            )
            return True, token

        page.click('input[type="submit"], button[type="submit"]')
        try:
            page.wait_for_selector("p#result", timeout=8_000)
            print(f"  [{mode_label}] SUCCESS ✓")
            page.screenshot(
                path=str(
                    Path(__file__).parent / f"screenshot_attempt_{attempt_num:02d}.png"
                )
            )
            return True, token
        except Exception:
            print(f"  [{mode_label}] FAILED — success message not found")
            page.screenshot(
                path=str(
                    Path(__file__).parent / f"screenshot_attempt_{attempt_num:02d}.png"
                )
            )
            return False, token

    except Exception as exc:
        print(f"  [{mode_label}] ERROR: {exc}")
        return False, None


def run_session(
    headless: bool,
    attempt_range: range,
) -> tuple[list[bool], list[str]]:
    """Run a batch of attempts in a single shared browser session."""
    results: list[bool] = []
    tokens: list[str] = []
    mode_label = f"headless={headless}"

    try:
        with SB(uc=True, headless=headless) as sb:
            sb.activate_cdp_mode()
            endpoint_url = sb.cdp.get_endpoint_url()

            with sync_playwright() as p:
                browser = p.chromium.connect_over_cdp(endpoint_url)
                context = browser.contexts[0]

                for attempt in attempt_range:
                    print(f"\n─── Attempt {attempt}/{NUM_ATTEMPTS} [{mode_label}] ───")
                    page = context.new_page()
                    try:
                        success, token = run_attempt_on_page(
                            sb,
                            page,
                            attempt,
                            headless,
                            skip_submit=(attempt == NUM_ATTEMPTS),
                        )
                        results.append(success)
                        if token:
                            tokens.append(token)
                    finally:
                        page.close()

                browser.close()

    except Exception as exc:
        print(f"  [SESSION ERROR | {mode_label}] {exc}")
        # Pad results so counts stay consistent
        while len(results) < len(attempt_range):
            results.append(False)

    return results, tokens


def main() -> None:
    print("=" * 60)
    print("Task 1 — Cloudflare Turnstile Stealth Automation")
    print("=" * 60)

    half = NUM_ATTEMPTS // 2

    print(f"\n{'─' * 60}")
    print(f"  SESSION 1 — headless=False (attempts 1–{half})")
    print(f"{'─' * 60}")
    headed_results, headed_tokens = run_session(
        headless=False,
        attempt_range=range(1, half + 1),
    )

    print(f"\n{'─' * 60}")
    print(f"  SESSION 2 — headless=True (attempts {half + 1}–{NUM_ATTEMPTS})")
    print(f"{'─' * 60}")
    headless_results, headless_tokens = run_session(
        headless=True,
        attempt_range=range(half + 1, NUM_ATTEMPTS + 1),
    )

    all_tokens = headed_tokens + headless_tokens
    total_success = sum(headed_results) + sum(headless_results)
    total_rate = total_success / NUM_ATTEMPTS * 100
    headed_rate = (
        sum(headed_results) / len(headed_results) * 100 if headed_results else 0.0
    )
    headless_rate = (
        sum(headless_results) / len(headless_results) * 100 if headless_results else 0.0
    )

    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    print(
        f"  headless=False : {sum(headed_results)}/{len(headed_results)}  ({headed_rate:.0f}%)"
    )
    print(
        f"  headless=True  : {sum(headless_results)}/{len(headless_results)}  ({headless_rate:.0f}%)"
    )
    print(f"  Overall        : {total_success}/{NUM_ATTEMPTS}  ({total_rate:.0f}%)")
    print(f"  Required ≥60%  : {'✓ PASS' if total_rate >= 60 else '✗ FAIL'}")

    if all_tokens:
        print("\nCollected tokens:")
        for i, t in enumerate(all_tokens, 1):
            print(f"  [{i}] {t}")

    summary = {
        "total_attempts": NUM_ATTEMPTS,
        "total_successes": total_success,
        "overall_success_rate_pct": round(total_rate, 1),
        "headed_success_rate_pct": round(headed_rate, 1),
        "headless_success_rate_pct": round(headless_rate, 1),
        "pass": total_rate >= 60,
        "tokens": all_tokens,
    }
    RESULTS_FILE.write_text(json.dumps(summary, indent=2))
    print(f"\nResults saved → {RESULTS_FILE}")


if __name__ == "__main__":
    main()
