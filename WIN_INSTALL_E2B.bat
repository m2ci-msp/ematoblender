echo off
:: This is a batch file to run the Ematoblender package install with gradle.
:: It is simply an alternative to running gradlew setup.

echo Running the Windows buildscript for Ematoblender
gradlew setup
pause