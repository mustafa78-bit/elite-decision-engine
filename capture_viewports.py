from playwright.sync_api import sync_playwright
import time
import os

VIEWPORTS = {
    "375x812": {"width": 375, "height": 812},
    "390x844": {"width": 390, "height": 844},
    "414x896": {"width": 414, "height": 896},
    "768x1024": {"width": 768, "height": 1024},
    "desktop_1440": {"width": 1440, "height": 900}
}

def capture():
    os.makedirs("/home/jules/verification/screenshots", exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        for name, size in VIEWPORTS.items():
            print(f"Capturing viewport: {name} ({size['width']}x{size['height']})")

            # Setup context
            context = browser.new_context(
                viewport={"width": size["width"], "height": size["height"]},
                user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1" if size["width"] < 768 else None
            )

            page = context.new_page()

            # We navigate to login page first to let localStorage be initialized
            page.goto("http://localhost:5173/login")
            page.wait_for_load_state("networkidle")

            # Inject auth credentials
            page.evaluate("() => { localStorage.setItem('auth_token', 'dev-auth-token-bypass'); localStorage.setItem('auth_user', 'dev'); }")

            # Go to command deck
            page.goto("http://localhost:5173/command-deck")

            # Wait for HQ Loading Screen to finish and systems to load
            time.sleep(3.5)

            # Take screenshot
            path = f"/home/jules/verification/screenshots/command_deck_{name}.png"
            page.screenshot(path=path)
            print(f"Saved: {path}")

            context.close()

        browser.close()

if __name__ == "__main__":
    capture()
