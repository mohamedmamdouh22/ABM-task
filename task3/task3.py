"""
Task 3: DOM Scraping Assessment
--------------------------------
Opens the BLS Spain CAPTCHA page and:
  1. Scrapes ALL images as base64 → allimages.json
  2. Scrapes only the humanly visible images → visible_images_only.json
  3. Prints the visible text instructions
"""

import asyncio
import base64
import json
from pathlib import Path

from playwright.async_api import async_playwright

URL = "https://egypt.blsspainglobal.com/Global/CaptchaPublic/GenerateCaptcha?data=4CDiA9odF2%2b%2bsWCkAU8htqZkgDyUa5SR6waINtJfg1ThGb6rPIIpxNjefP9UkAaSp%2fGsNNuJJi5Zt1nbVACkDRusgqfb418%2bScFkcoa1F0I%3d"

OUTPUT_DIR = Path(__file__).parent


async def main() -> None:
    image_responses: dict[str, str] = {}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        async def on_response(response):
            if response.request.resource_type == "image":
                try:
                    body = await response.body()
                    ct = response.headers.get("content-type", "image/png")
                    image_responses[response.url] = (
                        f"data:{ct};base64,{base64.b64encode(body).decode()}"
                    )
                except Exception:
                    pass

        page.on("response", on_response)

        await page.goto(URL, wait_until="networkidle", timeout=30_000)
        await page.wait_for_timeout(1_000)
        await page.screenshot(
            path=OUTPUT_DIR / "screenshot.png"
        )  # screenshot of the page to see the visible imgs/labels

        img_locator = page.locator("img.captcha-img")
        img_count = await img_locator.count()

        viewport = page.viewport_size or {"width": 1280, "height": 720}

        async def is_humanly_visible(locator_item) -> bool:
            """True only if the element is actually on screen and not visually occluded."""
            if not await locator_item.is_visible():
                return False

            box = await locator_item.bounding_box()
            if not box:
                return False

            if box["width"] <= 1 or box["height"] <= 1:
                return False

            left, top = box["x"], box["y"]
            right, bottom = left + box["width"], top + box["height"]
            if right <= 0 or bottom <= 0:
                return False
            if left >= viewport["width"] or top >= viewport["height"]:
                return False

            handle = await locator_item.element_handle()
            if not handle:
                return False

            return await page.evaluate(
                """(el) => {
                    const r = el.getBoundingClientRect();
                    if (!r || r.width <= 1 || r.height <= 1) return false;
                    const cx = r.left + r.width / 2;
                    const cy = r.top + r.height / 2;
                    if (cx < 0 || cy < 0 || cx > window.innerWidth || cy > window.innerHeight) {
                        return false;
                    }
                    const topEl = document.elementFromPoint(cx, cy);
                    return !!topEl && (topEl === el || el.contains(topEl));
                }""",
                handle,
            )

        all_images: list[dict] = []
        visible_images: list[dict] = []

        for i in range(img_count):
            img = img_locator.nth(i)
            src = await img.get_attribute("src")
            alt = await img.get_attribute("alt")
            width = await img.get_attribute("width")
            height = await img.get_attribute("height")
            is_visible = await is_humanly_visible(img)

            src_value = src or ""
            inline_b64 = src_value if src_value.startswith("data:") else None
            b64 = inline_b64 or image_responses.get(src_value)
            record = {
                "src": src,
                "alt": alt,
                "width": int(width) if width and width.isdigit() else width,
                "height": int(height) if height and height.isdigit() else height,
                "base64": b64,
            }
            all_images.append(record)
            if is_visible:
                visible_images.append(record)

        label_locator = page.locator(".main-div-container .box-label")
        label_count = await label_locator.count()
        visible_text: list[str] = []
        for i in range(label_count):
            label = label_locator.nth(i)
            if await is_humanly_visible(label):
                txt = (await label.text_content() or "").strip()
                if txt:
                    visible_text.append(txt)
        visible_text = list(dict.fromkeys(visible_text))

        await browser.close()

    # Save
    (OUTPUT_DIR / "allimages.json").write_text(
        json.dumps(all_images, indent=2), encoding="utf-8"
    )
    (OUTPUT_DIR / "visible_images_only.json").write_text(
        json.dumps(visible_images, indent=2), encoding="utf-8"
    )

    print(f"All images     : {len(all_images)}")
    print(f"Visible images : {len(visible_images)}")
    print("Visible text   :")
    for line in visible_text:
        print(f"  {line}")


if __name__ == "__main__":
    asyncio.run(main())
