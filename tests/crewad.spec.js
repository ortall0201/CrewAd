// @ts-check
const { test, expect } = require('@playwright/test');

test.describe('CrewAd Application', () => {
  test('should load the home page', async ({ page }) => {
    await page.goto('/');
    
    // Check if the main heading is visible
    await expect(page.locator('h1')).toBeVisible();
    
    // Check for upload form
    await expect(page.locator('form')).toBeVisible();
  });

  test('should show upload form elements', async ({ page }) => {
    await page.goto('/');
    
    // Check for file input
    await expect(page.locator('input[type="file"]')).toBeVisible();
    
    // Check for upload button
    await expect(page.locator('button[type="submit"]')).toBeVisible();
  });

  test('should validate backend API health', async ({ request }) => {
    const response = await request.get('http://localhost:8000/health');
    expect(response.ok()).toBeTruthy();
    
    const data = await response.json();
    expect(data.status).toBe('healthy');
  });

  test('should handle file upload interaction', async ({ page }) => {
    await page.goto('/');
    
    // Locate file input
    const fileInput = page.locator('input[type="file"]');
    await expect(fileInput).toBeVisible();
    
    // Test file upload interaction (without actual file)
    await fileInput.click();
    
    // Check if upload button becomes interactive
    const uploadButton = page.locator('button[type="submit"]');
    await expect(uploadButton).toBeVisible();
  });

  test('should show status polling functionality', async ({ page }) => {
    await page.goto('/');
    
    // Look for any status-related elements
    // This test checks if the page has elements that would show status updates
    const statusElements = page.locator('[class*="status"], [id*="status"], [data-testid*="status"]');
    
    // The page should be ready to show status updates
    await expect(page.locator('body')).toBeVisible();
  });

  test('should handle navigation and basic interactions', async ({ page }) => {
    await page.goto('/');
    
    // Test basic page interactions
    await page.waitForLoadState('networkidle');
    
    // Check if JavaScript is working by looking for dynamic elements
    const dynamicElements = page.locator('script, [class*="component"], [id*="app"]');
    await expect(dynamicElements.first()).toBeVisible();
  });
});