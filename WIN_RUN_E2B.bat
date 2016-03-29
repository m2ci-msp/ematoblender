echo off
:: This is a batch file to run the core Ematoblender elements 
:: It runs the GUIs for the static server and the gameserver
cd %~dp0%
echo Running the Windows run script for Ematoblender Static
pause
:: Run static data
gradlew run
pause
