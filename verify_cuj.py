import sys
from playwright.sync_api import sync_playwright

def run_cuj(page):
    print("Navigating to LoginPage...")
    page.goto("http://localhost:5173/login")
    page.wait_for_timeout(2000)

    # Take login page screenshot
    page.screenshot(path="/home/jules/verification/screenshots/login.png")

    print("Filling in login info...")
    page.locator("#username").fill("admin")
    page.locator("#password").fill("password123")
    page.wait_for_timeout(500)
    page.screenshot(path="/home/jules/verification/screenshots/login_filled.png")

    print("Clicking sign in...")
    page.get_by_role("button", name="Sign In").click()
    page.wait_for_timeout(3000)

    print("Taking post-login screenshot...")
    page.screenshot(path="/home/jules/verification/screenshots/command-deck.png")

    # Try navigation
    routes = [
        "overview", "scanner", "decisions", "portfolio", "signals", "risk",
        "paper-trading", "notifications", "intelligence", "trading-control",
        "journal", "backtest", "preferences", "funding", "open-interest",
        "hero-dashboard", "trading-workspace", "ai-experience"
    ]

    for route in routes:
        print(f"Navigating to /{route}...")
        page.goto(f"http://localhost:5173/{route}")
        page.wait_for_timeout(2000)
        page.screenshot(path=f"/home/jules/verification/screenshots/{route}.png")

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            record_video_dir="/home/jules/verification/videos"
        )
        page = context.new_page()
        try:
            run_cuj(page)
        except Exception as e:
            print("CUJ error:", e)
        finally:
            context.close()
            browser.close()
