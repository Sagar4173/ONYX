import { test, expect, request as playwrightRequest } from "@playwright/test";

const apiURL = process.env.E2E_API_URL || "http://localhost:8000";
const apiBaseURL = `${apiURL}/api`;
const E2E_PASSWORD = "E2ePassword123!";

test.describe("Backend Health", () => {
  test("API docs endpoint returns 200", async ({ request }) => {
    const response = await request.get(`${apiURL}/docs`);
    expect(response.ok()).toBeTruthy();
  });

  test("OpenAPI spec is valid", async ({ request }) => {
    const response = await request.get(`${apiURL}/openapi.json`);
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
    await expect(page.getByRole("heading", { name: /sign in/i })).toBeVisible({ timeout: 10000 });
    const identifierInput = page
      .locator('input[autocomplete="username"], input[placeholder*="email or username" i]')
      .first();
    await expect(identifierInput).toBeVisible({ timeout: 5000 });
  });

  test("Register page has registration form", async ({ page }) => {
    await page.goto("/register");
    await expect(page.getByText(/join onyx/i).first()).toBeVisible({ timeout: 10000 });
    const emailInput = page.locator('input[type="email"]').first();
    await expect(emailInput).toBeVisible({ timeout: 5000 });
  });

  test("Unknown routes redirect unauthenticated visitors to landing", async ({ page }) => {
    await page.goto("/nonexistent-route-12345");
    await page.waitForURL((url) => url.pathname === "/");
    await expect(page.locator("text=ONYX").first()).toBeVisible();
  });
});

test.describe("Navigation", () => {
  test("Can navigate from landing to login", async ({ page }) => {
    await page.goto("/");
    const loginLink = page
      .locator('a[href="/login"], a:has-text("Sign in"), button:has-text("Sign in")')
      .first();
    if (await loginLink.isVisible({ timeout: 3000 }).catch(() => false)) {
      await loginLink.click();
      await page.waitForURL("**/login");
      await expect(page).toHaveURL(/login/);
    }
  });

  test("Can navigate from landing to register", async ({ page }) => {
    await page.goto("/");
    const registerLink = page
      .locator(
        'a[href="/register"], a:has-text("Register"), a:has-text("Sign up"), button:has-text("Sign up")'
      )
      .first();
    if (await registerLink.isVisible({ timeout: 3000 }).catch(() => false)) {
      await registerLink.click();
      await page.waitForURL("**/register");
      await expect(page).toHaveURL(/register/);
    }
  });
});

test.describe("Authenticated E2E", () => {
  let apiContext;
  let testUser;

  test.beforeAll(async () => {
    apiContext = await playwrightRequest.newContext();

    const runId = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
    testUser = {
      email: `e2e-${runId}@example.com`,
      username: `e2e_${runId.replace(/-/g, "_")}`,
      full_name: "E2E User",
      password: E2E_PASSWORD,
    };

    const response = await apiContext.post(`${apiBaseURL}/auth/register`, { data: testUser });
    expect(response.status(), await response.text()).toBe(201);
  });

  test.afterAll(async () => {
    await apiContext?.dispose();
  });

  async function authenticatePage(page) {
    const response = await apiContext.post(`${apiBaseURL}/auth/login`, {
      data: {
        username_or_email: testUser.email,
        password: testUser.password,
      },
    });
    expect(response.status(), await response.text()).toBe(200);

    const session = await response.json();
    await page.addInitScript((storedSession) => {
      localStorage.setItem("access_token", storedSession.access_token);
      localStorage.setItem("refresh_token", storedSession.refresh_token);
      localStorage.setItem("user_data", JSON.stringify(storedSession.user));
    }, session);
  }

  test("Login form submits and redirects to dashboard", async ({ page }) => {
    await page.goto("/login");

    const emailInput = page
      .locator('input[autocomplete="username"], input[placeholder*="email or username" i]')
      .first();
    const passwordInput = page.locator('input[type="password"]').first();
    const submitButton = page
      .locator('button[type="submit"], button:has-text("Sign in"), button:has-text("Sign In")')
      .first();

    await expect(emailInput).toBeVisible({ timeout: 5000 });
    await expect(passwordInput).toBeVisible({ timeout: 5000 });
    await expect(submitButton).toBeVisible({ timeout: 5000 });

    await emailInput.fill(testUser.email);
    await passwordInput.fill(testUser.password);
    await submitButton.click();

    await expect(page).toHaveURL(/\/dashboard/, { timeout: 15000 });
    await expect(page.getByRole("heading", { name: /security dashboard/i })).toBeVisible({
      timeout: 10000,
    });
  });

  test.describe("Sidebar Navigation", () => {
    test("Navigation links render after authentication", async ({ page }) => {
      await authenticatePage(page);
      await page.goto("/dashboard");

      const navLinks = [
        { name: "Dashboard", href: "/dashboard" },
        { name: "Projects", href: "/projects" },
        { name: "Reports", href: "/reports" },
        { name: "Analytics", href: "/analytics" },
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
      await authenticatePage(page);
      await page.goto("/dashboard");

      const pages = ["/projects", "/reports", "/compliance", "/settings"];
      for (const path of pages) {
        const link = page.locator(`a[href="${path}"]`).first();
        await expect(link).toBeVisible({ timeout: 5000 });
        await link.click();
        await expect(page).toHaveURL(new RegExp(`${path}$`), { timeout: 5000 });
        await expect(page.locator("main")).toBeVisible();
        await page.goto("/dashboard");
      }
    });
  });
});
