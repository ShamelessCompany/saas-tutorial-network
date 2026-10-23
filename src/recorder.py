"""Browser automation and screen recording using Playwright."""
import asyncio
from pathlib import Path
from typing import Any, Dict, List
from playwright.async_api import async_playwright

INJECTED_OVERLAY_SCRIPT = """
(() => {
  if (window.__tutorialOverlayInitialized) return;
  window.__tutorialOverlayInitialized = true;

  // Visual Overlay Container
  const overlay = document.createElement('div');
  overlay.id = 'saas-tutorial-hud';
  overlay.style.position = 'fixed';
  overlay.style.top = '0';
  overlay.style.left = '0';
  overlay.style.width = '100vw';
  overlay.style.height = '100vh';
  overlay.style.pointerEvents = 'none';
  overlay.style.zIndex = '9999999';

  // Step callout card (top-right)
  const callout = document.createElement('div');
  callout.id = 'saas-step-callout';
  callout.style.position = 'absolute';
  callout.style.top = '24px';
  callout.style.right = '28px';
  callout.style.background = 'rgba(15, 23, 42, 0.9)';
  callout.style.border = '1px solid rgba(99, 102, 241, 0.5)';
  callout.style.color = '#ffffff';
  callout.style.padding = '10px 18px';
  callout.style.borderRadius = '10px';
  callout.style.fontFamily = '-apple-system, sans-serif';
  callout.style.fontSize = '15px';
  callout.style.fontWeight = '600';
  callout.style.boxShadow = '0 10px 25px rgba(0,0,0,0.5)';
  callout.style.display = 'none';
  callout.style.transition = 'all 0.25s ease';

  // Affiliate Lower-Third Banner (bottom)
  const affiliateBanner = document.createElement('div');
  affiliateBanner.id = 'saas-affiliate-banner';
  affiliateBanner.style.position = 'absolute';
  affiliateBanner.style.bottom = '18px';
  affiliateBanner.style.left = '50%';
  affiliateBanner.style.transform = 'translateX(-50%)';
  affiliateBanner.style.background = 'linear-gradient(90deg, #4f46e5, #06b6d4)';
  affiliateBanner.style.color = '#ffffff';
  affiliateBanner.style.padding = '8px 24px';
  affiliateBanner.style.borderRadius = '9999px';
  affiliateBanner.style.fontFamily = '-apple-system, sans-serif';
  affiliateBanner.style.fontSize = '14px';
  affiliateBanner.style.fontWeight = '700';
  affiliateBanner.style.boxShadow = '0 6px 20px rgba(79, 70, 229, 0.5)';
  affiliateBanner.style.letterSpacing = '0.02em';
  affiliateBanner.style.display = 'none';

  overlay.appendChild(callout);
  overlay.appendChild(affiliateBanner);
  document.body.appendChild(overlay);

  window.__showCallout = (text) => {
    if (!text) {
      callout.style.display = 'none';
      return;
    }
    callout.innerText = text;
    callout.style.display = 'block';
  };

  window.__showAffiliate = (text) => {
    if (!text) {
      affiliateBanner.style.display = 'none';
      return;
    }
    affiliateBanner.innerText = text;
    affiliateBanner.style.display = 'block';
  };
})();
"""

async def _execute_action(page, step: Dict[str, Any]):
    action = step.get("action", "wait")
    callout = step.get("callout")
    if callout:
        await page.evaluate(f"window.__showCallout({repr(callout)})")

    selector = step.get("selector")
    duration = step.get("duration_ms", 1000)

    if action == "hover" and selector:
        loc = page.locator(selector)
        await loc.scroll_into_view_if_needed()
        await loc.hover()
        await page.wait_for_timeout(duration)

    elif action == "click" and selector:
        loc = page.locator(selector)
        await loc.scroll_into_view_if_needed()
        await loc.hover()
        await page.wait_for_timeout(300)
        await loc.click()
        await page.wait_for_timeout(duration)

    elif action == "type" and selector:
        text = step.get("text", "")
        delay = step.get("delay_ms", 50)
        loc = page.locator(selector)
        await loc.scroll_into_view_if_needed()
        await loc.click()
        await loc.type(text, delay=delay)
        await page.wait_for_timeout(duration)

    elif action == "wait":
        await page.wait_for_timeout(duration)

async def record_workflow_video(
    target_url: str,
    workflow: Dict[str, Any],
    output_dir: Path | str,
    headless: bool = True
) -> Path:
    out_dir = Path(output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    viewport = workflow.get("viewport", {"width": 1920, "height": 1080})
    steps: List[Dict[str, Any]] = workflow.get("steps", [])
    affiliate_banner = workflow.get("affiliate", {}).get("banner_text", "")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=headless,
            args=["--disable-infobars", "--no-sandbox"]
        )

        context = await browser.new_context(
            record_video_dir=str(out_dir),
            record_video_size={"width": viewport["width"], "height": viewport["height"]},
            viewport={"width": viewport["width"], "height": viewport["height"]}
        )

        page = await context.new_page()

        # Navigate
        await page.goto(target_url, wait_until="networkidle")
        await page.wait_for_timeout(1000)

        # Inject HUD and affiliate banner
        await page.evaluate(INJECTED_OVERLAY_SCRIPT)
        if affiliate_banner:
            await page.evaluate(f"window.__showAffiliate({repr(affiliate_banner)})")

        # Execute all steps
        for step in steps:
            await _execute_action(page, step)

        # Buffer end
        await page.wait_for_timeout(1500)

        video_obj = page.video
        await page.close()
        await context.close()
        await browser.close()

        if video_obj:
            video_path = await video_obj.path()
            return Path(video_path)
        else:
            # Fallback search in out_dir
            videos = list(out_dir.glob("*.webm"))
            if videos:
                return sorted(videos, key=lambda f: f.stat().st_mtime, reverse=True)[0]
            raise RuntimeError("Playwright did not output a recorded video file.")

def record_workflow_sync(
    target_url: str,
    workflow: Dict[str, Any],
    output_dir: Path | str,
    headless: bool = True
) -> Path:
    return asyncio.run(record_workflow_video(target_url, workflow, output_dir, headless))
