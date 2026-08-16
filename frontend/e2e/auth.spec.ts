import { test, expect } from "@playwright/test";

// First e2e test in this repo -- covers the golden path that everything
// else depends on: a real user, registered against the real backend, can
// log in through the real UI and land on an authenticated page. No UI
// exists for registration (LoginPage.tsx only has a login form -- see
// api/routes/auth.py's /auth/register), so the user is seeded directly
// via the backend API, then the actual login form is what's exercised.
test.describe("Login", () => {
  test("a registered user can log in and reach the dashboard", async ({ page, request }) => {
    const username = `e2e_user_${Date.now()}`;
    const password = "e2e-test-password-123";

    const registerResp = await request.post("http://localhost:8000/auth/register", {
      data: { username, email: `${username}@example.com`, password },
    });
    expect(registerResp.ok()).toBeTruthy();
    const registerBody = await registerResp.json();
    expect(registerBody.success).toBe(true);

    await page.goto("/login");
    await page.locator("#username").fill(username);
    await page.locator("#password").fill(password);
    await page.getByRole("button", { type: "submit" }).click();

    // LoginPage navigates to /dashboard, which immediately redirects to
    // /command-deck (App.tsx's real routing) -- assert the actual final
    // landing page, not the intermediate redirect target.
    await expect(page).toHaveURL(/\/command-deck/);
    await expect(page.locator("#username")).not.toBeVisible();
  });

  test("an invalid password does not navigate away from the login page", async ({ page, request }) => {
    const username = `e2e_user_${Date.now()}_badpw`;

    const registerResp = await request.post("http://localhost:8000/auth/register", {
      data: { username, email: `${username}@example.com`, password: "the-real-password-123" },
    });
    expect(registerResp.ok()).toBeTruthy();

    await page.goto("/login");
    await page.locator("#username").fill(username);
    await page.locator("#password").fill("the-wrong-password");
    await page.getByRole("button", { type: "submit" }).click();

    await expect(page).toHaveURL(/\/login/);
  });
});
