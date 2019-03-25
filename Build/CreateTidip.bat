REM $Id: CreateTidip.bat 4 2013-03-11 10:24:19Z $
REM Windows Shell Script
REM
REM Run this script to create python executable
REM for Tidip.py application (TI-me Di-stance P-arameters)
REM
REM Recommendation: run from shell command line
REM for tracking progress and identiying errrors
REM
REM Run when directory that contains the source code and the setup script
REM is PWD ( present working directory)
REM
REM
REM This version creates Tidip.
REM

cd /D "%~dp0"

REM run pyinstaller to create executable
"C:\Program Files (x86)\Microsoft Visual Studio\Shared\Python36_64\Scripts\pyinstaller.exe" --noconsole --onefile ..\Source\Tidip\Tidip.py

REM add config file
copy ..\Source\Tidip\Tidip.Conf.txt dist\

rmdir build /S /Q
del Tidip.spec

REM delete old folder if exists
rmdir ..\Release\Tidip_64bit /S /Q
REM Give the executable an appropriate name
rename dist Tidip_64bit
move Tidip_64bit ..\Release\

popd


