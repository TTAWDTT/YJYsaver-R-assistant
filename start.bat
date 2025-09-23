@echo off
echo Starting R Language Assistant...

echo.
echo Checking Python...
python --version
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH
    pause
    exit /b 1
)

echo.
echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Setting up database...
cd r_assistant
python manage.py makemigrations
python manage.py migrate

echo.
echo Creating superuser (optional)...
set /p create_superuser="Do you want to create a superuser? (y/N): "
if /i "%create_superuser%"=="y" (
    python manage.py createsuperuser
)

echo.
echo Starting development server...
echo Open http://127.0.0.1:8000 in your browser
echo Press Ctrl+C to stop the server
python manage.py runserver

pause