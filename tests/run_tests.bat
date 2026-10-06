@echo off
setlocal

echo ========================================================
echo Running Bharath::GeometryTools Automated Tests
echo ========================================================

:: Check for hython
where hython >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    if defined HFS (
        set "PATH=%HFS%\bin;%PATH%"
    ) else (
        echo WARNING: 'hython' not found in PATH and HFS not set.
        echo Please run this from a Houdini Command Line environment or set HFS.
        pause
        exit /b 1
    )
)

:: Run the test script
hython "%~dp0test_scale_points.py"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Tests completed successfully.
) else (
    echo.
    echo Tests failed with exit code %ERRORLEVEL%.
)

endlocal
