@echo off
set "APP_NAME=Addon translate"
set "APP_VERSION=1.0.1"
set "COMPANY_NAME=Smileheart Company"

echo --- Starting Nuitka Compilation for %APP_NAME% ---

python -m nuitka ^
    --standalone ^
    --main=main.py ^
    --output-dir=build ^
    --remove-output ^
    --jobs=8 ^
    --assume-yes-for-downloads ^
    --windows-console-mode=disable ^
    --windows-icon-from-ico=resource/images/logo.ico ^
    --enable-plugin=pyqt6 ^
    --include-data-dir=resource=resource ^
    --deployment ^
    --lto=yes ^
    --product-name="%APP_NAME%" ^
    --company-name="%COMPANY_NAME%" ^
    --file-version="%APP_VERSION%" ^
    --product-version="%APP_VERSION%" ^
    --file-description="%APP_NAME% - A fantastic application." ^
    --copyright="Copyright (c) 2025 %COMPANY_NAME%. All rights reserved."

echo --- Nuitka Compilation Finished ---

pause
