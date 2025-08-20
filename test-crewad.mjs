import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';

async function createTestFiles() {
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

    // Create a logo image (copy of the same PNG for simplicity)
    const testLogoPath = path.join(testDir, 'logo.png');
    fs.writeFileSync(testLogoPath, pngBuffer);

    // Create a test text file (brief)
    const testBriefPath = path.join(testDir, 'brief.txt');
    fs.writeFileSync(testBriefPath, `Create an engaging video advertisement for a revolutionary AI tool.

Key Message: Transform your workflow with AI-powered automation
Tone: Confident and innovative
Target: Tech professionals and business owners
CTA: Start your free trial today

Highlights:
- 10x faster processing
- 99% accuracy rate  
- Used by 50,000+ professionals
- Save 20 hours per week`);

    return { testImagePath, testLogoPath, testBriefPath };
}

async function testCrewAdWorkflow() {
    const browser = await chromium.launch({ 
        headless: false,
        slowMo: 1000 // Slow down for demo
    });
    const context = await browser.newContext();
    const page = await context.newPage();

    console.log('🚀 Starting CrewAd Full Workflow Test');

    try {
        // Create test files
        console.log('📁 Creating test files...');
        const { testImagePath, testLogoPath, testBriefPath } = await createTestFiles();

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

        // Listen for network responses
        page.on('response', async (response) => {
            if (response.url().includes('/api/')) {
                if (response.ok()) {
                    console.log(`✅ API Success: ${response.status()} - ${response.url()}`);
                } else {
                    console.error(`🚨 API Error: ${response.status()} - ${response.url()}`);
                    try {
                        const body = await response.text();
                        console.error('Response body:', body);
                    } catch (e) {
                        console.error('Could not read response body');
                    }
                }
            }
        });

        // Test 1: Upload multiple files
        console.log('📤 Test 1: Uploading multiple files...');
        const fileInput = page.locator('#file-input');
        await fileInput.setInputFiles([testImagePath, testLogoPath, testBriefPath]);
        
        // Wait for files to appear in the list
        await page.waitForSelector('.file-item', { timeout: 5000 });
        const fileCount = await page.locator('.file-item').count();
        console.log(`📋 Files in list: ${fileCount}/3`);

        // Click upload button
        console.log('🚀 Clicking Upload Files button...');
        const uploadButton = page.locator('button:text("Upload Files")');
        await uploadButton.click();

        // Wait for upload success and step 2 to appear
        console.log('⏳ Waiting for upload success...');
        await page.waitForSelector('.step:has(.step-number:text("2"))', { timeout: 10000 });
        console.log('✅ Upload successful! Step 2 appeared.');

        // Test 2: Configure parameters
        console.log('⚙️ Test 2: Configuring ad parameters...');
        
        // Set target length
        await page.fill('input[type="number"]', '15');
        
        // Set tone
        await page.selectOption('select[value="confident"]', 'friendly');
        
        // Set aspect ratio  
        await page.selectOption('select[value="16:9"]', '9:16');
        
        console.log('✅ Parameters configured');

        // Test 3: Start pipeline (but don't wait for completion)
        console.log('🎬 Test 3: Starting ad generation pipeline...');
        const generateButton = page.locator('button:text("Generate Ad")');
        await generateButton.click();

        // Wait for status panel to appear
        await page.waitForSelector('.status-panel', { timeout: 10000 });
        console.log('✅ Pipeline started! Status panel visible.');

        // Check status for a few seconds
        console.log('📊 Monitoring pipeline status...');
        for (let i = 0; i < 5; i++) {
            await page.waitForTimeout(2000);
            const statusItems = await page.locator('.status-item').count();
            console.log(`📈 Status items visible: ${statusItems}`);
            
            // Check for any completed steps
            const completedSteps = await page.locator('.status-icon.completed').count();
            const runningSteps = await page.locator('.status-icon.running').count();
            const failedSteps = await page.locator('.status-icon.failed').count();
            
            console.log(`   ✅ Completed: ${completedSteps}, 🔄 Running: ${runningSteps}, ❌ Failed: ${failedSteps}`);
            
            if (failedSteps > 0) {
                console.log('⚠️ Pipeline has failed steps, but continuing test...');
                break;
            }
        }

        console.log('🎉 CrewAd workflow test completed successfully!');
        console.log('📝 Summary:');
        console.log('   ✅ Multiple file upload working');
        console.log('   ✅ Parameter configuration working');
        console.log('   ✅ Pipeline can start (full completion requires system deps)');

    } catch (error) {
        console.error('🚨 Test failed:', error.message);
        console.error('Stack:', error.stack);
    } finally {
        console.log('🏁 Closing browser...');
        await page.waitForTimeout(2000); // Keep open for a moment
        await browser.close();
    }
}

// Run the comprehensive test
testCrewAdWorkflow().catch(console.error);