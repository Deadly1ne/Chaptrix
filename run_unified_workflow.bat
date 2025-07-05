@echo off
echo Chaptrix Unified Workflow
echo =======================
echo.
echo Running unified workflow (check, download, crop, stitch, upload)...
python unified_workflow.py

IF %ERRORLEVEL% NEQ 0 (
    echo.
    echo Unified workflow failed. See logs for details.
    exit /b 1
) ELSE (
    echo.
    echo Unified workflow completed successfully!
    echo All steps have been processed: checking for new chapters, downloading,
    echo removing watermarks, stitching, and uploading/notifications.
)

pause