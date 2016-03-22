echo off
:: This is a batch file to run the core Ematoblender elements 
:: This script will set up the system to run live - with the WAVE on port 3030
echo Running the Windows run script for Ematoblender Live
pause
:: Run live data
set ip_address_string="IPv4 Address"
for /f "usebackq tokens=2 delims=:" %%h in (`ipconfig ^| findstr /c:%ip_address_string%`) do (
    echo %%h
    goto :break
)

:break
echo Setting WAVE host to %%h
gradlew runFromWave -Phost=%%h -Pport=3030
pause