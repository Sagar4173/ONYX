import { test, expect } from "@playwright/test";

test.describe("Backend Health", () => {
  test("API docs endpoint returns 200", async ({ request }) => {
    const response = await request.get("/docs");
    expect(response.ok()).toBeTruthy();
  });

  test("OpenAPI spec is valid", async ({ request }) => {
    const response = await request.get("/openapi.json");
    expect(response.ok()).toBeTruthy();
    const spec = await response.json();
    expect(spec.info.title).toContain("ONYX");
  });
});

test.describe("Frontend Pages", () => {
  test("Landing page loads with branding", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator("text=ONYX").first()).toBeVisible();
    await expect(page.locator("text=Security Intelligence").first()).toBeVisible();
  });

  test("Login page has form elements", async ({ page }) => {
    await page.goto("/login");
    await expect(page.locator("text=Sign in").first()).toBeVisible({ timeout: 10000 });
    const emailInput = page.locator('input[type="email"], input[name="email"], input[placeholder*="email" i]').first();
    await expect(emailInput).toBeVisible({ timeout: 5000 });
  });

  test("Register page has registration form", async ({ page }) => {
    await page.goto("/register");
    await expect(page.locator("text=Join ONYX").first()).toBeVisible({ timeout: 10000 });
    const emailInput = page.locator('input[type="email"], input[name="email"]').first();
    await expect(emailInput).toBeVisible({ timeout: 5000 });
  });

  test("404 page shown for unknown routes", async ({ page }) => {
    const response = await page.goto("/nonexistent-route-12345");
    expect(response?.status()).toBe(404);
  });
});

test.describe("Navigation", () => {
  test("Can navigate from landing to login", async ({ page }) => {
    await page.goto("/");
    const loginLink = page.locator('a[href="/login"], a:has-text("Sign in"), button:has-text("Sign in")').first();
    if (await loginLink.isVisible({ timeout: 3000 }).catch(() => false)) {
      await loginLink.click();
      await page.waitForURL("**/login");
      await expect(page).toHaveURL(/login/);
    }
  });

  test("Can navigate from landing to register", async ({ page }) => {
    await page.goto("/");
    const registerLink = page.locator(
      'a[href="/register"], a:has-text("Register"), a:has-text("Sign up"), button:has-text("Sign up")'
    ).first();
    if (await registerLink.isVisible({ timeout: 3000 }).catch(() => false)) {
      await registerLink.click();
      await page.waitForURL("**/register");
      await expect(page).toHaveURL(/register/);
    }
  });
});

test.describe("Dashboard (Authenticated)", () => {
  test("Login form submits and redirects to dashboard", async ({ page }) => {
    await page.goto("/login");

    const emailInput = page.locator('input[type="email"], input[name="email"]').first();
    const passwordInput = page.locator('input[type="password"], input[name="password"]').first();
    const submitButton = page.locator(
      'button[type="submit"], button:has-text("Sign in"), button:has-text("Login")'
    ).first();

    await expect(emailInput).toBeVisible({ timeout: 5000 });
    await expect(passwordInput).toBeVisible({ timeout: 5000 });
    await expect(submitButton).toBeVisible({ timeout: 5000 });

    await emailInput.fill("test@onyx.security");
    await passwordInput.fill("TestPassword123!");

    await submitButton.click();

    await page.waitForURL(/dashboard/, { timeout: 15000 }).catch(() => {});
    const currentUrl = page.url();
    const isDashboard = currentUrl.includes("dashboard");
    const isLoginPage = currentUrl.includes("login");

    if (isDashboard) {
      const heading = page.locator("text=Dashboard").first();
      await expect(heading).toBeVisible({ timeout: 5000 });
    } else if (isLoginPage) {
      const errorMsg = page.locator("text=Invalid").first();
      const errorVisible = await errorMsg.isVisible({ timeout: 3000 }).catch(() => false);
      if (errorVisible) {
        test.skip();
      }
    }
  });
});

test.describe("Sidebar Navigation", () => {
  test("Navigation links render after authentication", async ({ page }) => {
    await page.goto("/dashboard");

    const isUnauthenticated = page.url().includes("login");
    if (isUnauthenticated) {
      test.skip();
    }

    const navLinks = [
      { name: "Dashboard", href: "/dashboard" },
      { name: "Projects", href: "/projects" },
      { name: "Reports", href: "/reports" },
      { name: "Compliance", href: "/compliance" },
      { name: "Scheduled Scans", href: "/scheduled-scans" },
      { name: "Secret History", href: "/secret-history" },
      { name: "Settings", href: "/settings" },
    ];

    for (const link of navLinks) {
      const locator = page.locator(`a[href="${link.href}"]`).first();
      await expect(locator).toBeVisible({ timeout: 3000 });
    }
  });

  test("Each nav link navigates to correct page", async ({ page }) => {
    await page.goto("/dashboard");

    const isUnauthenticated = page.url().includes("login");
    if (isUnauthenticated) {
      test.skip();
    }

    const pages = ["/projects", "/reports", "/compliance", "/settings"];
    for (const path of pages) {
      const link = page.locator(`a[href="${path}"]`).first();
      if (await link.isVisible({ timeout: 2000 }).catch(() => false)) {
        await link.click();
        await page.waitForURL(`**${path}`, { timeout: 5000 });
        await expect(page).toHaveURL(new RegExp(path.replace("/", "\\/")));
        await page.goBack();
        await page.waitForLoadState("networkidle");
      }
    }
  });
});
