// Node.js script to launch Simply Sign Desktop app and log a user in
// using native Windows keystrokes and native PowerShell screenshots.

import { execSync, spawn } from 'child_process';
import { TOTP } from 'totp-generator';
import path from 'path';
import fs from 'fs'; // NEW: Added file system module for verification

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// Native PowerShell Keystroke Sender
function sendKeys(keys) {
  const script = `$wshell = New-Object -ComObject wscript.shell; $wshell.SendKeys('${keys}')`;
  execSync(`powershell -Command "${script}"`);
}

// Native PowerShell Screen Capture (Saved to GITHUB_WORKSPACE)
function takeScreenshot(filename) {
  // Default to the GitHub workspace, or use the current directory if running locally
  const workspace = process.env.GITHUB_WORKSPACE || process.cwd();
  const fullPath = path.join(workspace, filename);

  const psScript = `
    Add-Type -AssemblyName System.Windows.Forms;
    Add-Type -AssemblyName System.Drawing;
    $Screen = [System.Windows.Forms.SystemInformation]::VirtualScreen;
    $bitmap = New-Object System.Drawing.Bitmap $Screen.Width, $Screen.Height;
    $graphic = [System.Drawing.Graphics]::FromImage($bitmap);
    $graphic.CopyFromScreen($Screen.Left, $Screen.Top, 0, 0, $bitmap.Size);
    $bitmap.Save('${fullPath}');
  `;
  try {
    execSync(`powershell -Command "${psScript}"`);
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
        takeScreenshot('oob1.png');
        sendKeys('{ENTER}');
        
        await sleep(3000);
        takeScreenshot('oob2.png');
        sendKeys('{ENTER}');
        
        await sleep(3000);
        takeScreenshot('oob3.png');
        sendKeys('{ESC}');
        takeScreenshot('oob6.png');
        
        // Re-execute SSD to open login dialog
        launchSSD();
    } else {
        console.log('NOT running on ARM64');
    }

    await sleep(3000);

    // 2. Login Flow
    takeScreenshot('login01.png');
    console.log('Typing credentials...');
    
    // Type Email
    sendKeys('jay0lee@gmail.com');
    await sleep(500); 
    takeScreenshot('login02.png');
    
    // Tab to next field
    sendKeys('{TAB}');
    await sleep(500);

    // Generate and type TOTP
    console.log(`Our secret is ${process.env.TOTP_SECRET.length} characters.`);
    const { otp } = await TOTP.generate(process.env.TOTP_SECRET, {algorithm: 'SHA-256'});
    console.log(`Our token is ${otp.length} characters.`);
    
    sendKeys(otp);
    await sleep(500);
    takeScreenshot('login03.png');

    // Submit
    sendKeys('{ENTER}');
    console.log('Login sequence complete.');
    
    // Screenshot cascade to monitor the window closing
    takeScreenshot('login04.png');
    await sleep(500);
    takeScreenshot('login05.png');
    await sleep(500);
    takeScreenshot('login06.png');
    await sleep(500);
    takeScreenshot('login07.png');
    await sleep(500);
    takeScreenshot('login08.png');
    await sleep(500);
    takeScreenshot('login09.png');
    await sleep(500);
    takeScreenshot('login10.png');
    await sleep(500);
    takeScreenshot('login11.png');
    await sleep(500);
    takeScreenshot('login12.png');
    
    console.log('Exiting script, leaving SimplySign running in background.');

    // NEW: Verification block to list all PNGs in the workspace
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
