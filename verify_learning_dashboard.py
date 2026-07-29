import os
from playwright.sync_api import sync_playwright

def run_cuj(page):
    print("Navigating to LoginPage...")
    page.goto("http://localhost:5173/login")
    page.wait_for_timeout(2000)

    # Take screenshot of login page for debugging
    page.screenshot(path="/home/jules/verification/screenshots/login_debug.png")
    print("Saved login_debug.png")

    print("Entering credentials using ID selectors...")
    page.fill("#username", "founder")
    page.wait_for_timeout(500)
    page.fill("#password", "password123")
    page.wait_for_timeout(500)

    print("Submitting login form...")
    page.click("button[type='submit']")
    page.wait_for_timeout(2000)  # Wait for login to complete

    print("Navigating directly to Decision Center...")
    page.goto("http://localhost:5173/decisions")
    page.wait_for_timeout(2000)

    # Take screenshot of decisions page to verify login succeeded
    page.screenshot(path="/home/jules/verification/screenshots/decisions_debug.png")
    print("Saved decisions_debug.png")

    print("Clicking on 'Learning AI' tab...")
    page.get_by_role("button", name="Learning AI").click()
    page.wait_for_timeout(3000)  # Wait for dashboard data to load

    # Take screenshot at key moment
    screenshot_path = "/home/jules/verification/screenshots/learning_dashboard.png"
    print(f"Saving high-fidelity screenshot to {screenshot_path}...")
    page.screenshot(path=screenshot_path)
    page.wait_for_timeout(1000)

if __name__ == "__main__":
    with sync_playwright() as p:
        print("Launching headless Chromium...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 960},
            record_video_dir="/home/jules/verification/videos"
        )
        page = context.new_page()
        try:
            run_cuj(page)
        except Exception as e:
            print(f"Exception during verification: {e}")
        finally:
            print("Closing browser context and saving video...")
            context.close()
            browser.close()
            print("Verification CUJ finished.")
