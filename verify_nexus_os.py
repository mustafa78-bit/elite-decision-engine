from playwright.sync_api import sync_playwright
import os

def run_desktop_verification(page):
    print("Navigating to local environment to seed auth token...")
    page.goto("http://localhost:5173/")
    page.wait_for_timeout(500)

    # Inject token and user details to localStorage
    page.evaluate("localStorage.setItem('auth_token', 'mock-token-for-playwright-verification');")
    page.evaluate("localStorage.setItem('auth_user', 'Mustafa');")

    print("Navigating to NEXUS AI Operating System Command Deck...")
    page.goto("http://localhost:5173/command-deck")

    # Wait for the loader to fade out
    print("Waiting for sync loader to clear...")
    page.wait_for_timeout(4500)

    # Capture pristine home state of NEXUS OS (the hero crystal brain) - Idle state & Conversation panel
    print("Taking Idle state & Conversation panel screenshot...")
    page.screenshot(path="verification_screenshots/idle_state.png")

    # Click Explore to open Evidence Surface
    print("Clicking Explore Active Surveillance to open Evidence Surface...")
    page.locator('button[aria-label="Explore Active Surveillance Radar"]').click()
    page.wait_for_timeout(1000)

    # Take a screenshot showing the Evidence Surface open
    print("Taking Evidence Surface Open screenshot...")
    page.screenshot(path="verification_screenshots/evidence_surface_open.png")

    # Interactive chat operation: type "check portfolio"
    print("Initiating Chat directive...")
    chat_input = page.locator('input[aria-label="Initialize operator directive input"]')
    chat_input.fill("check portfolio")
    page.wait_for_timeout(500)

    # Click transmit to trigger thinking state
    page.locator('button[aria-label="Transmit directive to NEXUS"]').click()
    print("Transmitting directive (Entering thinking state)...")
    page.wait_for_timeout(800)

    # Take screenshot showing Thinking state
    print("Taking Thinking state screenshot...")
    page.screenshot(path="verification_screenshots/thinking_state.png")

    # Wait for the response to resolve
    print("Waiting for response to resolve...")
    page.wait_for_timeout(1800)
    page.screenshot(path="verification_screenshots/chat_resolved.png")

def run_mobile_verification(page):
    print("Navigating to local environment to seed auth token (Mobile)...")
    page.goto("http://localhost:5173/")
    page.wait_for_timeout(500)

    # Inject token and user details to localStorage
    page.evaluate("localStorage.setItem('auth_token', 'mock-token-for-playwright-verification');")
    page.evaluate("localStorage.setItem('auth_user', 'Mustafa');")

    print("Navigating to NEXUS AI Operating System Command Deck (Mobile)...")
    page.goto("http://localhost:5173/command-deck")
    page.wait_for_timeout(4500)

    print("Taking Mobile layout screenshot...")
    page.screenshot(path="verification_screenshots/mobile_layout.png")

if __name__ == "__main__":
    os.makedirs("verification_screenshots", exist_ok=True)
    os.makedirs("verification_videos", exist_ok=True)

    with sync_playwright() as p:
        print("--- RUNNING DESKTOP VERIFICATION ---")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            record_video_dir="verification_videos",
            viewport={"width": 1440, "height": 900}
        )
        page = context.new_page()
        try:
            run_desktop_verification(page)
        except Exception as e:
            print(f"Error in desktop verification: {e}")
        finally:
            context.close()
            browser.close()

        print("--- RUNNING MOBILE VERIFICATION ---")
        browser_mobile = p.chromium.launch(headless=True)
        context_mobile = browser_mobile.new_context(
            viewport={"width": 375, "height": 812}
        )
        page_mobile = context_mobile.new_page()
        try:
            run_mobile_verification(page_mobile)
        except Exception as e:
            print(f"Error in mobile verification: {e}")
        finally:
            context_mobile.close()
            browser_mobile.close()

    print("Verification processes finished.")
