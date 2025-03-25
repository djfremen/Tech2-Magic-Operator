@echo off
echo Preparing files for GitHub...

REM Create necessary folders
mkdir archive 2>nul
mkdir src 2>nul
mkdir "reference sources" 2>nul

REM Rename revised files to standard names
copy tech2_workflow_revised.py tech2_workflow.py
copy tech2_communication_revised.py tech2_communication.py
copy process_bin_revised.py process_bin.py

REM Move revised files to archive
move tech2_workflow_revised.py archive\
move tech2_communication_revised.py archive\
move process_bin_revised.py archive\

REM Move documentation files to ensure they are in correct location
REM docs folder should already exist

echo Files have been prepared for GitHub.
echo 1. Create a new repository on GitHub
echo 2. Push these files using:
echo    git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git
echo    git branch -M main
echo    git push -u origin main

echo Done! 