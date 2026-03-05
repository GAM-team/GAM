// Node.js script to launch Simply Sign Desktop app and log a user in
// using native Windows keystrokes and screenshot-desktop for reliable CI imaging.

import { execSync, spawn } from 'child_process';
import { TOTP } from 'totp-generator';
import path from 'path';
import fs from 'fs';
import screenshot from 'screenshot-desktop';

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// Native PowerShell Keystroke Sender
function sendKeys(keys) {
  const script = `$wshell = New-Object -ComObject wscript.shell; $wshell.SendKeys('${keys}')`;
  execSync(`powershell -Command "${script}"`);
}

// Reliable Screen Capture using screenshot-desktop
async function takeScreenshot(filename) {
  const workspace = process.env.GITHUB_WORKSPACE || process.cwd();
  const fullPath = path.join(workspace, filename);

  try {
    await screenshot({ filename: fullPath });
    console.log(`Saved screenshot: ${fullPath}`);
  } catch (err) {
    console.error(`Failed to save screenshot ${fullPath}:`, err.message);
  }
}

// Fire and forget application launcher
function launchSSD() {
    const child = spawn('C:\\Program Files\\Certum\\SimplySign Desktop\\SimplySignDesktop.exe', [], {
        detached: true,       
        stdio: 'ignore'       
    });
    child.unref();            
}

async function runSSD() {
    console.log('Launching SimplySign Desktop...');
    
    // Launch the application detached.
    launchSSD();

    // 1. Handle ARM64 Out-Of-Box experience
    const runner_arch = process.env.RUNNER_ARCH;
    if (runner_arch === "ARM64") {
        console.log('Running on ARM64...');
        await sleep(3000);
        await takeScreenshot('oob1.png');
        sendKeys('{ENTER}');
        
        await sleep(3000);
        await takeScreenshot('oob2.png');
        sendKeys('{ENTER}');
        
        await sleep(3000);
        await takeScreenshot('oob3.png');
        sendKeys('{ESC}');
        await takeScreenshot('oob6.png');

        // Try dismissing OneDrive also
        await sleep(3000);
        sendKeys('{TAB}');
        await takeScreenshot('oob7.png');

        await sleep(3000);
        sendKeys('{TAB}');
        await takeScreenshot('oob8.png');

        await sleep(3000);
        sendKeys('{TAB}');
        await takeScreenshot('oob9.png');

        await sleep(3000);
        sendKeys('{ENTER}');
        await takeScreenshot('oob10.png');
    } else {
        console.log('NOT running on ARM64');
    }

    // Re-execute SSD to open login dialog
    launchSSD();
    await sleep(3000);

    // 2. Login Flow
    await takeScreenshot('login01.png');
    console.log('Typing credentials...');
    
    // Type Email
    sendKeys('jay0lee@gmail.com');
    await sleep(500); 
    await takeScreenshot('login02.png');
    
    // Tab to next field
    sendKeys('{TAB}');
    await sleep(500);

    // Generate and type TOTP
    console.log(`Our secret is ${process.env.TOTP_SECRET.length} characters.`);
    const { otp } = await TOTP.generate(process.env.TOTP_SECRET, {algorithm: 'SHA-256'});
    console.log(`Our token is ${otp.length} characters.`);
    
    sendKeys(otp);
    await sleep(500);
    await takeScreenshot('login03.png');

    // Submit
    sendKeys('{ENTER}');
    console.log('Login sequence complete.');
    
    // Screenshot cascade to monitor the window closing
    await takeScreenshot('login04.png');
    await sleep(500);
    await takeScreenshot('login05.png');
    await sleep(500);
    await takeScreenshot('login06.png');
    await sleep(500);
    await takeScreenshot('login07.png');
    await sleep(500);
    await takeScreenshot('login08.png');
    await sleep(500);
    await takeScreenshot('login09.png');
    await sleep(500);
    await takeScreenshot('login10.png');
    await sleep(500);
    await takeScreenshot('login11.png');
    await sleep(500);
    await takeScreenshot('login12.png');
    
    console.log('Exiting script, leaving SimplySign running in background.');

    // Verification block to list all PNGs in the workspace
    console.log('\n--- Screenshot Verification ---');
    const workspace = process.env.GITHUB_WORKSPACE || process.cwd();
    try {
        const files = fs.readdirSync(workspace);
        const pngFiles = files.filter(f => f.endsWith('.png'));
        console.log(`Target Directory: ${workspace}`);
        console.log(`Found ${pngFiles.length} .png files:`);
        pngFiles.forEach(f => console.log(` - ${f}`));
    } catch (err) {
        console.error(`Error reading directory ${workspace}:`, err.message);
    }
    console.log('-------------------------------\n');
}

runSSD();
