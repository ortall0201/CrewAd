import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';

async function testSingleFileUpload() {
    const browser = await chromium.launch({ 
        headless: false,
        slowMo: 500 
    });
    const context = await browser.newContext();
    const page = await context.newPage();

    console.log('🧪 Testing Single File Upload');

    try {
        // Navigate and wait for page load
        await page.goto('http://localhost:3000');
        await page.waitForLoadState('networkidle');
        
        // Listen for API responses
        page.on('response', async (response) => {
            if (response.url().includes('/api/upload')) {
                if (response.ok()) {
                    console.log(`✅ Upload API Success: ${response.status()}`);
                } else {
                    console.error(`❌ Upload API Failed: ${response.status()}`);
                    console.error(await response.text());
                }
            }
        });

        // Wait for upload zone
        await page.waitForSelector('.file-drop-zone');
        console.log('📋 Upload form ready');

        // Test 1: Single file upload
        console.log('📤 Testing single file upload...');
        
        // Use the test file we created
        const testFile = path.join(process.cwd(), 'single-test.txt');
        
        const fileInput = page.locator('#file-input');
        await fileInput.setInputFiles([testFile]);
        
        // Wait for file to appear
        await page.waitForSelector('.file-item');
        
        // Check file count display
        const dropZoneText = await page.locator('.drop-zone-text').textContent();
        console.log(`📋 Drop zone shows: "${dropZoneText}"`);
        
        // Check button text
        const buttonText = await page.locator('button.btn').textContent();
        console.log(`🔘 Button text: "${buttonText}"`);
        
        // Click upload
        await page.click('button.btn');
        console.log('🚀 Clicked upload button');
        
        // Wait for step 2 to appear (success)
        try {
            await page.waitForSelector('.step:has(.step-number:text("2"))', { timeout: 10000 });
            console.log('✅ SUCCESS: Single file upload works! Step 2 appeared.');
        } catch (error) {
            console.log('⏳ Step 2 didn\'t appear - checking for errors...');
            
            // Check for error messages
            const errorElements = await page.locator('.error-message').count();
            if (errorElements > 0) {
                const errorText = await page.locator('.error-message').textContent();
                console.error(`❌ Error shown: ${errorText}`);
            }
        }
        
        await page.waitForTimeout(3000); // Keep browser open to see result

    } catch (error) {
        console.error('❌ Test failed:', error.message);
    } finally {
        await browser.close();
        console.log('🏁 Test completed');
    }
}

testSingleFileUpload().catch(console.error);