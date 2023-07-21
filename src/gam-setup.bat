:neworupgrade
@echo.
@set /p nu= "If you have installed any version of GAM on any computer for your domain, enter u to upgrade, otherwise enter n? [u or n] "
@if /I "%nu%"=="u" (
@  echo GAM installation and setup complete!
@  goto alldone
   )
@if /I not "%nu%"=="n" (
@  echo.
@  echo Please answer n or u.
@  goto neworupgrade
   )

:createproject
@echo.
@set /p yn= "Are you ready to set up a Google API project for GAM? [y or n] "
@if /I "%yn%"=="n" (
@  echo.
@  echo You can create an API project later by running:
@  echo.
@  echo gam create project
@  goto alldone
   )
@if /I not "%yn%"=="y" (
@  echo.
@  echo Please answer y or n.
@  goto createproject
   )

@set /p adminemail= "Please enter your Google Workspace admin email address: "

@gam create project %adminemail%
@if not ERRORLEVEL 1 goto projectdone
@echo.
@echo Project creation failed. Trying again. Say n to skip project creation.
@goto createproject
:projectdone

:adminauth
@echo.
@set /p yn= "Are you ready to authorize GAM to perform Google Workspace management operations as your admin account? [y or n] "
@if /I "%yn%"=="n" (
@  echo.
@  echo You can authorize an admin later by running:
@  echo.
@  echo gam oauth create %adminemail%
@  goto admindone
   )
@if /I not "%yn%"=="y" (
@  echo.
@  echo Please answer y or n.
@  goto adminauth
   )
@gam oauth create %adminemail%
@if not ERRORLEVEL 1 goto admindone
@echo.
@echo Admin authorization failed. Trying again. Say n to skip admin authorization.
@goto adminauth
:admindone

:saauth
@echo.
@set /p yn= "Are you ready to authorize GAM to manage Google Workspace user data and settings? [y or n] "
@if /I "%yn%"=="n" (
@  echo.
@  echo You can authorize a service account later by running:
@  echo.
@  echo gam user %adminemail% check serviceaccount
@  goto sadone
   )
@if /I not "%yn%"=="y" (
@  echo.
@  echo Please answer y or n.
@  goto saauth
   )
@echo.
@set /p regularuser= "Please enter the email address of a regular Google Workspace user: "
@echo Great! Checking service account scopes. This will fail the first time. Follow the steps to authorize and retry. It can take a few minutes for scopes to PASS after they've been authorized in the admin console.
@gam user %regularuser% check serviceaccount
@if not ERRORLEVEL 1 goto sadone
@echo.
@echo Service account authorization failed. Confirm you entered the scopes correctly in the admin console. It can take a few minutes for scopes to PASS after they are entered in the admin console so if you're sure you entered them correctly, go grab a coffee and then hit Y to try again. Say N to skip admin authorization.
@goto saauth
:sadone

@echo GAM installation and setup complete!
:alldone
@pause
