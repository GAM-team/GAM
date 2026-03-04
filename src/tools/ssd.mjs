// Node.js script to launch Simply Sign Desktop app and log a user in
// using native Windows keystrokes and native PowerShell screenshots.

import { exec, execSync } from 'child_process';
import { TOTP } from 'totp-generator';

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// Native PowerShell Keystroke Sender
function sendKeys(keys) {
  const script = `$wshell = New-Object -ComObject wscript.shell; $wshell.SendKeys('${keys}')`;
  execSync(`powershell -Command "${script}"`);
}

// NEW: Native PowerShell Screen Capture
function takeScreenshot(filename) {
  const psScript = `
    Add-Type -AssemblyName System.Windows.Forms;
    Add-Type -AssemblyName System.Drawing;
    $Screen = [System.Windows.Forms.SystemInformation]::VirtualScreen;
    $bitmap = New-Object System.Drawing.Bitmap $Screen.Width, $Screen.Height;
    $graphic = [System.Drawing.Graphics]::FromImage($bitmap);
    $graphic.CopyFromScreen($Screen.Left, $Screen.Top, 0, 0, $bitmap.Size);
    $bitmap.Save('${filename}');
  `;
  try {
    execSync(`powershell -Command "${psScript}"`);
    console.log(`Saved screenshot: ${filename}`);
  } catch (err) {
    console.error(`Failed to save screenshot ${filename}:`, err.message);
  }
}

async function runSSD() {
    console.log('Launching SimplySign Desktop...');
    
    // Launch the application.
    exec('"C:\\Program Files\\Certum\\SimplySign Desktop\\SimplySignDesktop.exe"', (error) => {
        if (error) console.error(`exec error: ${error}`);
    });

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
        exec('"C:\\Program Files\\Certum\\SimplySign Desktop\\SimplySignDesktop.exe"');
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
    
    // Original screenshot cascade to monitor the window closing
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
}

runSSD();
