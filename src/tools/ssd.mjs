// Node.js script to launch Simply Sign Desktop app and log a user in
// using native Windows keystrokes and screenshot-desktop for reliable CI imaging.

import { execSync, spawn } from 'child_process';
import { TOTP } from 'totp-generator';
import path from 'path';
import fs from 'fs';

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// Native PowerShell Keystroke Sender
function sendKeys(keys) {
  const script = `$wshell = New-Object -ComObject wscript.shell; $wshell.SendKeys('${keys}')`;
  execSync(`powershell -Command "${script}"`);
}

// Native PowerShell Desktop Clear
function minimizeAllWindows() {
  console.log('Minimizing all rogue background windows...');
  const script = `$shell = New-Object -ComObject "Shell.Application"; $shell.MinimizeAll()`;
  try {
    execSync(`powershell -Command "${script}"`);
  } catch (err) {
    console.log('Minimize command failed silently.');
  }
}

async function takeScreenshot(filename) {
  const workspace = process.env.GITHUB_WORKSPACE || process.cwd();
  const fullPath = path.join(workspace, filename);
  
  // Create a temporary script file path
  const scriptPath = path.join(workspace, `screenshot_${Date.now()}.ps1`);

  const psScript = `
    Add-Type -AssemblyName System.Windows.Forms;
    Add-Type -AssemblyName System.Drawing;
    $Screen = [System.Windows.Forms.SystemInformation]::VirtualScreen;
    
    if ($Screen.Width -eq 0 -or $Screen.Height -eq 0) {
        Write-Error "Screen dimensions are 0x0. Desktop not fully initialized.";
        exit 1;
    }
    
    $bitmap = New-Object System.Drawing.Bitmap $Screen.Width, $Screen.Height;
    $graphic = [System.Drawing.Graphics]::FromImage($bitmap);
    $graphic.CopyFromScreen($Screen.Left, $Screen.Top, 0, 0, $bitmap.Size);
    
    # Save the file (using single quotes safely now)
    $bitmap.Save('${fullPath}');
    Write-Output "Wrote ${fullPath}";
    
    # Specify ItemType to prevent older PS versions from prompting interactively
    New-Item -Path "${fullPath}.written" -ItemType File | Out-Null;
  `;
  
  try {
    // 1. Write the script to disk
    fs.writeFileSync(scriptPath, psScript);

    // 2. Execute the file directly, piping stdout/stderr to the Node console
    execSync(`powershell -NoProfile -ExecutionPolicy Bypass -File "${scriptPath}"`, { 
        stdio: 'inherit' 
    });
    
    console.log(`Saved screenshot: ${fullPath}`);
  } catch (err) {
    console.error(`Failed to save screenshot ${fullPath}:`, err.message);
  } finally {
    // 3. Clean up the temp file so it doesn't clutter your CI artifacts
    if (fs.existsSync(scriptPath)) {
        fs.unlinkSync(scriptPath);
    }
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
    await takeScreenshot('001.png');
    minimizeAllWindows();
    await sleep(2000);
    await takeScreenshot('002.png');
    sendKeys('{ESC}');
    await sleep(2000);
    await takeScreenshot('003.png');
    //sendKeys('{ESC}');
    //await sleep(2000);
    //await takeScreenshot('004.png');
    //sendKeys('{ESC}');
    //await sleep(2000);
    //await takeScreenshot('005.png');
    //sendKeys('%{F4}');
    //await sleep(2000);
    //await takeScreenshot('006.png');
    //sendKeys('%{F4}');
    //await sleep(2000);
    //await takeScreenshot('007.png');

    // Re-execute SSD to open login dialog
    launchSSD();
    await sleep(3000);
    await takeScreenshot('008.png');
    launchSSD();
    await sleep(3000);
    await takeScreenshot('009.png');

    // 2. Login Flow
    console.log('Typing credentials...');
    
    // Type Email
    sendKeys('jay0lee@gmail.com');
    await sleep(500); 
    await takeScreenshot('010.png');
    
    // Tab to next field
    sendKeys('{TAB}');
    await sleep(500);

    // Generate and type TOTP
    console.log(`Our secret is ${process.env.TOTP_SECRET.length} characters.`);
    const { otp } = await TOTP.generate(process.env.TOTP_SECRET, {algorithm: 'SHA-256'});
    console.log(`Our token is ${otp.length} characters.`);
    
    sendKeys(otp);
    await sleep(500);
    await takeScreenshot('011.png');

    // Submit
    sendKeys('{ENTER}');
    console.log('Login sequence complete.');
    
    // Screenshot cascade to monitor the window closing
    await takeScreenshot('012.png');
    await sleep(500);
    await takeScreenshot('013.png');
    await sleep(500);
    await takeScreenshot('014.png');
    await sleep(500);

    
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
