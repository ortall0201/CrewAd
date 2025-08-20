import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';

async function testCrewAdUpload() {
    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext();
    const page = await context.newPage();

    try {
        // Navigate to the app
        console.log('🌐 Navigating to CrewAd...');
        await page.goto('http://localhost:3000');
        await page.waitForLoadState('networkidle');

        // Wait for the upload form to be ready
        console.log('⏳ Waiting for upload form...');
        await page.waitForSelector('.file-drop-zone', { timeout: 10000 });

        // Listen for console errors
        page.on('console', (msg) => {
            if (msg.type() === 'error') {
                console.error('🚨 Frontend Error:', msg.text());
            }
        });

        // Listen for network responses to catch API errors
        page.on('response', async (response) => {
            if (response.url().includes('/api/') && !response.ok()) {
                console.error(`🚨 API Error: ${response.status()} - ${response.url()}`);
                try {
                    const body = await response.text();
                    console.error('Response body:', body);
                } catch (e) {
                    console.error('Could not read response body');
                }
            }
        });

        // Create test files if they don't exist
        console.log('📁 Creating test files...');
        const testDir = path.join(process.cwd(), 'test-files');
        if (!fs.existsSync(testDir)) {
            fs.mkdirSync(testDir);
        }

        // Create a simple test image (1x1 pixel PNG)
        const testImagePath = path.join(testDir, 'test-image.png');
        const pngBuffer = Buffer.from([
            0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A, // PNG signature
            0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52, // IHDR chunk
            0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01, // 1x1 pixel
            0x08, 0x06, 0x00, 0x00, 0x00, 0x1F, 0x15, 0xC4,
            0x89, 0x00, 0x00, 0x00, 0x0A, 0x49, 0x44, 0x41, // IDAT chunk  
            0x54, 0x78, 0x9C, 0x63, 0x00, 0x01, 0x00, 0x00,
            0x05, 0x00, 0x01, 0x0D, 0x0A, 0x2D, 0xB4, 0x00,
            0x00, 0x00, 0x00, 0x49, 0x45, 0x4E, 0x44, 0xAE, // IEND chunk
            0x42, 0x60, 0x82
        ]);
        fs.writeFileSync(testImagePath, pngBuffer);

        // Create a test text file (brief)
        const testBriefPath = path.join(testDir, 'test-brief.txt');
        fs.writeFileSync(testBriefPath, 'Create an engaging ad for a modern tech product. Use confident tone and highlight innovation.');

        console.log('📤 Testing file upload...');
        
        // Test uploading the image
        const fileInput = await page.locator('#file-input');
        await fileInput.setInputFiles([testImagePath]);
        
        // Wait for file to appear in the list
        await page.waitForSelector('.file-item', { timeout: 5000 });
        console.log('✅ First file uploaded successfully');

        // Try uploading a second file (the brief)
        console.log('📤 Testing second file upload...');
        await fileInput.setInputFiles([testBriefPath]);
        
        // Wait a moment for processing
        await page.waitForTimeout(2000);

        // Check how many files are listed
        const fileItems = await page.locator('.file-item').count();
        console.log(`📋 Total files uploaded: ${fileItems}`);

        // Try to click upload button
        console.log('🚀 Attempting to upload files...');
        const uploadButton = page.locator('button:text("Upload Files")');
        await uploadButton.click();

        // Wait for response
        await page.waitForTimeout(3000);

        console.log('✅ Upload test completed. Check for any errors above.');

    } catch (error) {
        console.error('🚨 Test failed:', error.message);
    } finally {
        await browser.close();
    }
}

// Run the test
testCrewAdUpload().catch(console.error);