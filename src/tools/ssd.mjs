// Node.js script that implements an Appium client which will launch
// Simply Sign Desktop app and log a user in. Once logged in it should
// be possible to use tools like signtool.exe to sign Windows EXE/MSI files
// with the Certum certificate.

import { Key, remote } from 'webdriverio';
import { exec } from 'child_process';
import { TOTP } from 'totp-generator';

async function screenshot(driver, filename) {
  // uncomment to save .png screenshots
  //await driver.saveScreenshot(filename);
  return
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function executeCommand(command) {
  try {
    let { stdout, stderr } = await exec(command);
    return stdout;
  } catch (error) {
    console.error(`Error executing command: ${command}`);
    console.error(`Error details: ${error}`);
    throw error; 
  }
}

async function runSSD() {
    const opts = {
        port: 4723,
        logLevel: "silent",
        capabilities: {
            platformName: "Windows",
            "appium:app": "C:\\Program Files\\Certum\\SimplySign Desktop\\SimplySignDesktop.exe",
            "appium:automationName": "Windows",
        },
    };

    let driver;
    try {
        driver = await remote(opts);
        
        // Github Actions Win ARM64 is stuck on a OOB screen that steals focus
        // These enter / escapes should dismiss it.
        const runner_arch =  process.env.RUNNER_ARCH;
        if ( runner_arch === "ARM64" ) {
          console.log('Running on ARM64...');
          await sleep(3000); // Pause execution for 3 seconds
          await screenshot(driver, 'oob1.png');
          await driver.sendKeys([Key.Enter]);
          await sleep(3000); // Pause execution for 3 seconds
          await screenshot(driver, 'oob2.png');
          await driver.sendKeys([Key.Enter]);
          await sleep(3000); // Pause execution for 3 seconds
          await screenshot(driver, 'oob3.png');
          await driver.sendKeys([Key.Escape]);
          await screenshot(driver, 'oob6.png');
        } else {
          console.log('NOT running on ARM64');
        }

        //  Execute SSD again to open login dialog
        exec('"C:\\Program Files\\Certum\\SimplySign Desktop\\SimplySignDesktop.exe"', (error, stdout, stderr) => {
          if (error) {
            console.error(`exec error: ${error}`);
            return;
          }
        });
        await sleep(3000);

        // Login
        const windows = await driver.getWindowHandles();
        const login_window = windows[0]
        await driver.switchWindow(login_window);
        await screenshot(driver, 'login01.png');
        const id_value = 'jay0lee@gmail.com';
        const id_arr =  [...id_value];
        await driver.sendKeys(id_arr);
        await screenshot(driver, 'login02.png');
        await driver.sendKeys([Key.Tab]);
        // We wait until the last possible second to generate
        // our TOTP to ensure it's still valid.
        const token_value = TOTP.generate(process.env.TOTP_SECRET, {algorithm: 'SHA-256'}).otp;
        const token_arr =  [...token_value];
        await driver.sendKeys(token_arr);
        await screenshot(driver, 'login03.png');
        await driver.sendKeys([Key.Enter]);

        // TODO: it's expected that on successful login the window
        // will close and these screenshots will error out. Figure
        // out how to handle that gracefully.
        await screenshot(driver, 'login04.png');
        await sleep(500);
        await screenshot(driver, 'login05.png');
        await sleep(500);
        await screenshot(driver, 'login06.png');
        await sleep(500);
        await screenshot(driver, 'login07.png');
        await sleep(500);
        await screenshot(driver, 'login08.png');
        await sleep(500);
        await screenshot(driver, 'login09.png');
        await sleep(500);
        await screenshot(driver, 'login10.png');
        await sleep(500);
        await screenshot(driver, 'login11.png');
        await sleep(500);
        await screenshot(driver, 'login12.png');

    } catch (error) {
        console.error("Error during Appium run:", error.name);
    }

    // INTENTIONAL Keep driver open so tray icon for Certum doesn't close
    // finally {
    //    if (driver) {
    //        await driver.deleteSession(); // Close the Appium session
    //    }
    //}
}

runSSD();
