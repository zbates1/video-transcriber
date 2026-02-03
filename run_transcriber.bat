@echo off
setlocal enabledelayedexpansion

echo ============================================
echo  Video Transcriber - Setup and Run
echo ============================================
echo.

:: Configuration
set CONDA_ENV_NAME=video_transcriber
set FFMPEG_PATH=C:\Users\zanet\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.0.1-full_build\bin
set TEMP_DIR=E:\temp
set DEFAULT_OUTPUT_DIR=E:\temp

:: Parse arguments
set VIDEO_PATH=
set OUTPUT_DIR=%DEFAULT_OUTPUT_DIR%
set FORMAT=default
set USE_POPUP=0

:parse_args
if "%~1"=="" goto :done_parsing
if /i "%~1"=="--popup" (
    set USE_POPUP=1
    shift
    goto :parse_args
)
if /i "%~1"=="--browse" (
    set USE_POPUP=1
    shift
    goto :parse_args
)
if /i "%~1"=="--cmu-bme" (
    set FORMAT=cmu-bme-seminar
    shift
    goto :parse_args
)
if /i "%~1"=="--format" (
    set FORMAT=%~2
    shift
    shift
    goto :parse_args
)
if /i "%~1"=="--output-dir" (
    set OUTPUT_DIR=%~2
    shift
    shift
    goto :parse_args
)
if /i "%~1"=="-o" (
    set OUTPUT_DIR=%~2
    shift
    shift
    goto :parse_args
)
if /i "%~1"=="--help" goto :show_help
if /i "%~1"=="-h" goto :show_help

:: If not a flag, assume it's the video path
if "%VIDEO_PATH%"=="" (
    set VIDEO_PATH=%~1
)
shift
goto :parse_args

:done_parsing

:: Show file browser popup if requested or no video path provided
if %USE_POPUP%==1 goto :show_popup
if "%VIDEO_PATH%"=="" goto :show_popup
goto :continue_setup

:show_popup
echo [INFO] Opening file browser...
for /f "delims=" %%I in ('powershell -NoProfile -Command "Add-Type -AssemblyName System.Windows.Forms; $f = New-Object System.Windows.Forms.OpenFileDialog; $f.Title = 'Select Video File'; $f.Filter = 'Video Files (*.mp4;*.mkv;*.avi;*.mov;*.wmv)|*.mp4;*.mkv;*.avi;*.mov;*.wmv|All Files (*.*)|*.*'; $f.InitialDirectory = [Environment]::GetFolderPath('MyVideos'); if ($f.ShowDialog() -eq 'OK') { $f.FileName } else { 'CANCELLED' }"') do set VIDEO_PATH=%%I

if "%VIDEO_PATH%"=="CANCELLED" (
    echo [INFO] File selection cancelled.
    exit /b 0
)
if "%VIDEO_PATH%"=="" (
    echo [ERROR] No file selected.
    exit /b 1
)
echo [OK] Selected: %VIDEO_PATH%
echo.
goto :continue_setup

:show_help
echo.
echo Usage: run_transcriber.bat [OPTIONS] [video_path]
echo.
echo Options:
echo   --popup, --browse    Open file browser to select video
echo   --cmu-bme            Use CMU BME seminar summary format
echo   --format FORMAT      Set output format (default, cmu-bme-seminar)
echo   --output-dir, -o DIR Set output directory (default: E:\temp)
echo   --help, -h           Show this help message
echo.
echo Examples:
echo   run_transcriber.bat --popup
echo   run_transcriber.bat --popup --cmu-bme
echo   run_transcriber.bat "D:\videos\lecture.mkv"
echo   run_transcriber.bat "D:\videos\lecture.mkv" --cmu-bme
echo   run_transcriber.bat "D:\videos\lecture.mkv" --output-dir "E:\output"
echo.
echo Formats:
echo   default          - Standard summary format
echo   cmu-bme-seminar  - CMU BME seminar notes format with required fields
echo.
exit /b 0

:continue_setup

echo [1/5] Checking conda installation...
where conda >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Conda is not installed or not in PATH.
    echo Please install Miniconda or Anaconda first.
    exit /b 1
)
echo [OK] Conda found.
echo.

echo [2/5] Checking conda environment '%CONDA_ENV_NAME%'...
call conda env list | findstr /C:"%CONDA_ENV_NAME%" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Environment not found. Creating '%CONDA_ENV_NAME%'...
    call conda env create -f environment.yml
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create conda environment.
        exit /b 1
    )
    echo [OK] Environment created.
) else (
    echo [OK] Environment exists.
)
echo.

echo [3/5] Checking ffmpeg...
:: Add ffmpeg to PATH for this session
set PATH=%PATH%;%FFMPEG_PATH%

where ffmpeg >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] ffmpeg not found at: %FFMPEG_PATH%
    echo.
    echo Please install ffmpeg:
    echo   winget install ffmpeg
    echo.
    echo Or update FFMPEG_PATH in this script to match your installation.
    exit /b 1
)
echo [OK] ffmpeg found.
echo.

echo [4/5] Setting up directories...
:: Create temp directory if it doesn't exist
if not exist "%TEMP_DIR%" (
    mkdir "%TEMP_DIR%"
    echo [OK] Created temp directory: %TEMP_DIR%
) else (
    echo [OK] Temp directory exists: %TEMP_DIR%
)

:: Create output directory if it doesn't exist
if not exist "%OUTPUT_DIR%" (
    mkdir "%OUTPUT_DIR%"
    echo [OK] Created output directory: %OUTPUT_DIR%
) else (
    echo [OK] Output directory exists: %OUTPUT_DIR%
)

:: Set environment variable for temp directory
set TRANSCRIBER_TEMP_DIR=%TEMP_DIR%
echo [OK] TRANSCRIBER_TEMP_DIR=%TEMP_DIR%
echo.

echo [5/5] Checking video file...
if not exist "%VIDEO_PATH%" (
    echo [ERROR] Video file not found: %VIDEO_PATH%
    exit /b 1
)
echo [OK] Video file found: %VIDEO_PATH%
echo [INFO] Output format: %FORMAT%
echo.

echo ============================================
echo  All checks passed! Starting transcription...
echo ============================================
echo.

:: Activate conda environment and run
call conda activate %CONDA_ENV_NAME%
if %errorlevel% neq 0 (
    echo [ERROR] Failed to activate conda environment.
    exit /b 1
)

:: Change to script directory
cd /d "%~dp0"

:: Run the transcriber with format option
python src/main.py "%VIDEO_PATH%" --output-dir "%OUTPUT_DIR%" --format "%FORMAT%"

:: Capture exit code
set EXIT_CODE=%errorlevel%

echo.
if %EXIT_CODE% equ 0 (
    echo ============================================
    echo  Transcription completed successfully!
    echo  Output saved to: %OUTPUT_DIR%
    echo ============================================
) else (
    echo ============================================
    echo  Transcription failed with error code: %EXIT_CODE%
    echo ============================================
)

exit /b %EXIT_CODE%
