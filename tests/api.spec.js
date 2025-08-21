// @ts-check
const { test, expect } = require('@playwright/test');
const path = require('path');

test.describe('CrewAd API Tests', () => {
  const BASE_URL = 'http://localhost:8000';

  test('should return healthy status from health endpoint', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/health`);
    expect(response.ok()).toBeTruthy();
    
    const data = await response.json();
    expect(data.status).toBe('healthy');
  });

  test('should handle file upload endpoint', async ({ request }) => {
    // Test upload endpoint validation
    const response = await request.post(`${BASE_URL}/api/upload`, {
      multipart: {
        files: [], // Empty files array to test validation
      }
    });
    
    // Should either accept empty upload or return validation error
    expect(response.status()).toBeLessThan(500); // No server errors
  });

  test('should validate run endpoint requires run_id', async ({ request }) => {
    const response = await request.post(`${BASE_URL}/api/run`);
    
    // Should return client error for missing run_id
    expect(response.status()).toBeGreaterThanOrEqual(400);
    expect(response.status()).toBeLessThan(500);
  });

  test('should handle status endpoint with invalid run_id', async ({ request }) => {
    const invalidRunId = 'invalid-run-id-12345';
    const response = await request.get(`${BASE_URL}/api/status/${invalidRunId}`);
    
    // Should handle invalid run_id gracefully
    expect(response.status()).toBeLessThan(500);
  });

  test('should handle download endpoint with invalid run_id', async ({ request }) => {
    const invalidRunId = 'invalid-run-id-12345';
    const response = await request.get(`${BASE_URL}/api/download/${invalidRunId}`);
    
    // Should return not found or similar client error
    expect(response.status()).toBeLessThan(500);
  });

  test('should handle CORS preflight requests', async ({ request }) => {
    const response = await request.fetch(`${BASE_URL}/api/upload`, {
      method: 'OPTIONS',
      headers: {
        'Origin': 'http://localhost:3000',
        'Access-Control-Request-Method': 'POST',
        'Access-Control-Request-Headers': 'Content-Type',
      }
    });
    
    // Should handle CORS preflight
    expect(response.status()).toBeLessThan(500);
  });
});