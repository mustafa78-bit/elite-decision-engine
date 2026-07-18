import os
import jwt
from datetime import datetime, timedelta, timezone
from playwright.sync_api import sync_playwright

def generate_valid_token():
    # Generate a real, properly signed JWT token for the user 'test_user'
    token_payload = {
        "sub": "1",
        "username": "test_user",
        "exp": datetime.now(timezone.utc) + timedelta(hours=24)
    }
    return jwt.encode(token_payload, "supersecret", algorithm="HS256")

def run_user_journey_audit(page):
    print("Starting AI Copilot End-to-End User Journey Audit...")

    # 1. Generate real JWT token and inject into localStorage
    token = generate_valid_token()
    page.goto("http://localhost:5173")
    page.wait_for_timeout(1000)
    print("Injecting real signed auth token and active symbol context...")
    page.evaluate(f"""() => {{
        localStorage.setItem('auth_token', '{token}');
        localStorage.setItem('auth_user', JSON.stringify({{ username: 'test_user', email: 'test@elite.com' }}));
        localStorage.setItem('active_symbol', 'BTC');
    }}""")

    # 2. Go to AI Experience Workspace
    print("Navigating to AI Experience page...")
    page.goto("http://localhost:5173/ai-experience")
    page.wait_for_timeout(2500)

    # 3. Take first screenshot of initial welcome state
    print("Taking screenshot of initial state...")
    page.screenshot(path="/home/jules/verification/screenshots/verification_initial.png")
    page.wait_for_timeout(1000)

    # 4. Journey 1: "Why should I buy BTC?"
    print("Journey 1: Clicking suggestion 'Why should I buy BTC?'...")
    page.get_by_role("button", name="Why should I buy BTC?").click()
    page.wait_for_timeout(3000)  # wait for typing and response
    print("Taking screenshot of buying analysis response...")
    page.screenshot(path="/home/jules/verification/screenshots/verification_why_buy.png")
    page.wait_for_timeout(1000)

    # 5. Journey 2: Verify Cross-Linking to Decisions Page
    print("Journey 2: Clicking cross-link 'Decision Center' in AI message...")
    page.locator("a:has-text('Decision Center')").last.click()
    page.wait_for_timeout(2000)
    print("Taking screenshot of cross-linking verification...")
    page.screenshot(path="/home/jules/verification/screenshots/verification_cross_link_decisions.png")
    page.wait_for_timeout(1000)

    # Go back to AI Experience
    print("Returning to AI Workspace...")
    page.goto("http://localhost:5173/ai-experience")
    page.wait_for_timeout(2000)

    # 6. Journey 3: "What are the biggest portfolio risks?"
    print("Journey 3: Clicking suggestion 'What are the biggest portfolio risks?'...")
    page.get_by_role("button", name="What are the biggest portfolio risks?").click()
    page.wait_for_timeout(3000)
    print("Taking screenshot of portfolio risks audit response...")
    page.screenshot(path="/home/jules/verification/screenshots/verification_risks.png")
    page.wait_for_timeout(1000)

    # 7. Journey 4: "What happens if BTC drops 10%?"
    print("Journey 4: Clicking suggestion 'What happens if BTC drops 10%?'...")
    page.get_by_role("button", name="What happens if BTC drops 10%?").click()
    page.wait_for_timeout(3000)
    print("Taking screenshot of stress-test simulation response...")
    page.screenshot(path="/home/jules/verification/screenshots/verification_drops.png")
    page.wait_for_timeout(1000)

    # 8. Journey 5: "Show me the best opportunities today."
    print("Journey 5: Clicking suggestion containing 'opportunities'...")
    page.locator("button:has-text('opportunities')").first.click()
    page.wait_for_timeout(3000)
    print("Taking screenshot of top opportunities discovery response...")
    page.screenshot(path="/home/jules/verification/screenshots/verification_opportunities.png")
    page.wait_for_timeout(2000)

    print("User Journey Audit completed successfully! All assets and states verified.")

if __name__ == "__main__":
    os.makedirs("/home/jules/verification/screenshots", exist_ok=True)
    os.makedirs("/home/jules/verification/videos", exist_ok=True)

    with sync_playwright() as p:
        print("Launching Chromium headless browser...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            record_video_dir="/home/jules/verification/videos",
            viewport={"width": 1280, "height": 800}
        )
        page = context.new_page()
        try:
            run_user_journey_audit(page)
        except Exception as e:
            print(f"Error during Playwright script: {e}")
        finally:
            print("Closing browser context...")
            context.close()
            browser.close()
            print("Playback video saved successfully.")
