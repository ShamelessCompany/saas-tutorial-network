"""Browser automation and screen recording using Playwright."""
import asyncio
import math
import random
from pathlib import Path
from typing import Any, Dict, List, Tuple
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
  overlay.style.zIndex = '2147483647';

  // Realistic Human Mouse Pointer (SVG)
  const cursor = document.createElement('div');
  cursor.id = 'human-mouse-cursor';
  cursor.style.position = 'fixed';
  cursor.style.top = '0';
  cursor.style.left = '0';
  cursor.style.width = '28px';
  cursor.style.height = '28px';
  cursor.style.pointerEvents = 'none';
  cursor.style.zIndex = '2147483647';
  cursor.style.transform = 'translate(250px, 250px)';
  cursor.style.transition = 'transform 0.04s cubic-bezier(0.25, 1, 0.5, 1)';
  cursor.style.willChange = 'transform';
  cursor.innerHTML = `
    <svg width="26" height="26" viewBox="0 0 24 24" style="filter: drop-shadow(0 2px 5px rgba(0,0,0,0.45));">
      <path d="M4 2L18 11.5L11.5 13.5L8 21.5L4 2Z" fill="#0f172a" stroke="#ffffff" stroke-width="1.8" stroke-linejoin="round"/>
    </svg>
    <div id="cursor-ripple" style="position: absolute; top: 0; left: 0; width: 34px; height: 34px; border-radius: 50%; background: rgba(59, 130, 246, 0.4); border: 2px solid #3b82f6; transform: translate(-50%, -50%) scale(0); pointer-events: none; opacity: 0;"></div>
  `;

  // Step callout card (top-right)
  const callout = document.createElement('div');
  callout.id = 'saas-step-callout';
  callout.style.position = 'absolute';
  callout.style.top = '24px';
  callout.style.right = '28px';
  callout.style.background = 'rgba(15, 23, 42, 0.92)';
  callout.style.border = '1px solid rgba(99, 102, 241, 0.6)';
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

  overlay.appendChild(cursor);
  overlay.appendChild(callout);
  overlay.appendChild(affiliateBanner);
  document.body.appendChild(overlay);

  window.__moveCursor = (x, y) => {
    cursor.style.transform = `translate(${x}px, ${y}px)`;
  };

  window.__clickCursor = (x, y) => {
    if (x !== undefined && y !== undefined) {
      cursor.style.transform = `translate(${x}px, ${y}px)`;
    }
    const ripple = document.getElementById('cursor-ripple');
    if (ripple) {
      ripple.style.transition = 'none';
      ripple.style.transform = 'translate(-50%, -50%) scale(0.2)';
      ripple.style.opacity = '1';
      setTimeout(() => {
        ripple.style.transition = 'transform 0.4s ease-out, opacity 0.4s ease-out';
        ripple.style.transform = 'translate(-50%, -50%) scale(2.2)';
        ripple.style.opacity = '0';
      }, 20);
    }
  };

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

  window.addEventListener('mousemove', (e) => {
    window.__moveCursor(e.clientX, e.clientY);
  });
  window.addEventListener('mousedown', (e) => {
    window.__clickCursor(e.clientX, e.clientY);
  });
})();
"""

async def human_mouse_move(
    page,
    start: Tuple[float, float],
    end: Tuple[float, float],
    steps: int = 20
) -> Tuple[float, float]:
    """Simulates realistic human mouse movement with Bezier curvature and variable acceleration."""
    x0, y0 = start
    x2, y2 = end
    dist = math.hypot(x2 - x0, y2 - y0)
    if dist < 4:
        await page.mouse.move(x2, y2)
        try:
            await page.evaluate(f"window.__moveCursor({x2}, {y2})")
        except Exception:
            pass
        return end

    # Random arc curvature
    mid_x = (x0 + x2) / 2
    mid_y = (y0 + y2) / 2
    normal_x = -(y2 - y0) / dist
    normal_y = (x2 - x0) / dist
    arc = (random.random() - 0.5) * min(120.0, dist * 0.35)
    x1 = mid_x + normal_x * arc
    y1 = mid_y + normal_y * arc

    # Smoothstep interpolation
    for i in range(1, steps + 1):
        t = i / steps
        ease = t * t * (3 - 2 * t)
        bx = (1 - ease)**2 * x0 + 2 * (1 - ease) * ease * x1 + ease**2 * x2
        by = (1 - ease)**2 * y0 + 2 * (1 - ease) * ease * y1 + ease**2 * y2
        await page.mouse.move(bx, by)
        try:
            await page.evaluate(f"window.__moveCursor({bx}, {by})")
        except Exception:
            pass
        await page.wait_for_timeout(random.randint(12, 22))

    await page.mouse.move(x2, y2)
    try:
        await page.evaluate(f"window.__moveCursor({x2}, {y2})")
    except Exception:
        pass
    return end

async def _execute_action(
    page,
    step: Dict[str, Any],
    cursor_state: List[float],
    affiliate_banner: str = ""
):
    action = step.get("action", "wait")
    callout = step.get("callout")

    try:
        await page.evaluate(INJECTED_OVERLAY_SCRIPT)
        if affiliate_banner:
            await page.evaluate(f"window.__showAffiliate({repr(affiliate_banner)})")
        if callout:
            await page.evaluate(f"window.__showCallout({repr(callout)})")
    except Exception:
        pass

    selector = step.get("selector")
    duration = step.get("duration_ms", 1000)

    if action == "hover" and selector:
        try:
            loc = page.locator(selector).locator("visible=true").first
            await loc.scroll_into_view_if_needed(timeout=2500)
            box = await loc.bounding_box()
            if box:
                target_x = box["x"] + box["width"] * 0.5 + random.uniform(-4, 4)
                target_y = box["y"] + box["height"] * 0.5 + random.uniform(-3, 3)
                cursor_state[0], cursor_state[1] = await human_mouse_move(
                    page, (cursor_state[0], cursor_state[1]), (target_x, target_y)
                )
        except Exception:
            pass
        await page.wait_for_timeout(duration)

    elif action == "click" and selector:
        try:
            loc = page.locator(selector).locator("visible=true").first
            await loc.scroll_into_view_if_needed(timeout=2500)
            box = await loc.bounding_box()
            if box:
                target_x = box["x"] + box["width"] * 0.5 + random.uniform(-4, 4)
                target_y = box["y"] + box["height"] * 0.5 + random.uniform(-3, 3)
                cursor_state[0], cursor_state[1] = await human_mouse_move(
                    page, (cursor_state[0], cursor_state[1]), (target_x, target_y)
                )
            await page.wait_for_timeout(random.randint(80, 160))
            try:
                await page.evaluate(f"window.__clickCursor({cursor_state[0]}, {cursor_state[1]})")
            except Exception:
                pass
            await loc.click(timeout=3000)
        except Exception:
            try:
                await page.evaluate(f"window.__clickCursor({cursor_state[0]}, {cursor_state[1]})")
                await page.mouse.click(cursor_state[0], cursor_state[1])
            except Exception:
                pass
        await page.wait_for_timeout(duration)

    elif action == "type" and selector:
        try:
            loc = page.locator(selector).locator("visible=true").first
            await loc.scroll_into_view_if_needed(timeout=2500)
            box = await loc.bounding_box()
            if box:
                target_x = box["x"] + box["width"] * 0.5
                target_y = box["y"] + box["height"] * 0.5
                cursor_state[0], cursor_state[1] = await human_mouse_move(
                    page, (cursor_state[0], cursor_state[1]), (target_x, target_y)
                )
            await loc.click(timeout=3000)
            text = step.get("text", "")
            delay = step.get("delay_ms", 55)
            await loc.type(text, delay=delay)
        except Exception:
            pass
        await page.wait_for_timeout(duration)

    elif action == "scroll":
        delta_y = step.get("delta_y", 600)
        steps_count = 15
        step_delta = delta_y / steps_count
        for _ in range(steps_count):
            await page.mouse.wheel(0, step_delta)
            await page.wait_for_timeout(35)
        await page.wait_for_timeout(duration)

    elif action == "navigate" and step.get("url"):
        await page.goto(step["url"], wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(duration)

    elif action == "wait":
        await page.wait_for_timeout(duration)

    # Re-inject overlay in case page DOM changed
    try:
        await page.evaluate(INJECTED_OVERLAY_SCRIPT)
        if affiliate_banner:
            await page.evaluate(f"window.__showAffiliate({repr(affiliate_banner)})")
        if callout:
            await page.evaluate(f"window.__showCallout({repr(callout)})")
    except Exception:
        pass

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

        # Navigate (using domcontentloaded for robust live web scraping & recording)
        await page.goto(target_url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(1500)

        # Inject HUD and affiliate banner
        try:
            await page.evaluate(INJECTED_OVERLAY_SCRIPT)
            if affiliate_banner:
                await page.evaluate(f"window.__showAffiliate({repr(affiliate_banner)})")
        except Exception:
            pass

        cursor_state = [400.0, 350.0]
        # Execute all steps
        for step in steps:
            await _execute_action(page, step, cursor_state, affiliate_banner=affiliate_banner)

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
