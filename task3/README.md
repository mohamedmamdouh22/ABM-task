# Task 3 — DOM Scraping Assessment

Scrapes the BLS Spain CAPTCHA page to extract all images and identify which ones are actually visible to the user, using async Playwright.

## How it works

Network responses are intercepted as the page loads to capture each image as base64 before it's rendered. Once the page is idle, all `img.captcha-img` elements are iterated and each is tested against a strict visibility check:

1. Element must pass Playwright's `is_visible()`
2. Must have a bounding box with width and height > 1px
3. Center point must be within the viewport bounds
4. `document.elementFromPoint(cx, cy)` must return the element itself (not obscured by another element)

Visible text labels from `.box-label` are also extracted and deduplicated.

## Run

```bash
python task3/task3.py
```

## Outputs

| File | Description |
| --- | --- |
| `allimages.json` | Every `img.captcha-img` found in the DOM with `src`, `alt`, dimensions, and base64 data |
| `visible_images_only.json` | Subset of images that pass the full visibility check |
| `screenshot.png` | Full-page screenshot captured after the page reaches network idle |
