@echo off
echo ========================================
echo   Smart Parking System - Startup
echo ========================================
echo.

REM Check if database exists, if not create it from scratch
echo [1/4] Checking database...
if not exist database\parking_system.db (
    echo Database not found. Creating complete database...
    .venv\Scripts\python.exe -c "import sqlite3; conn = sqlite3.connect('database/parking_system.db'); conn.executescript(open('database/schema.sql').read()); conn.commit(); conn.close(); print('  Schema loaded')"
    
    echo   Creating Django tables...
    cd parking_web
    ..\.venv\Scripts\python.exe create_django_tables.py >nul
    cd ..
    
    echo   Fixing passwords...
    cd parking_web
    ..\.venv\Scripts\python.exe fix_passwords.py >nul
    cd ..
    
    echo OK - Database created and initialized
) else (
    echo OK - Database exists
)
echo.

REM Activate virtual environment
echo [2/4] Activating virtual environment...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)
echo OK - Virtual environment activated
echo.

REM Start Django server in background
echo [3/4] Starting Django web server...
start "Django Server" cmd /k "cd parking_web && python manage.py runserver"
timeout /t 3 /nobreak >nul
echo OK - Django server starting at http://127.0.0.1:8000/
echo.

echo [4/4] System verification...
.venv\Scripts\python.exe -c "import sqlite3; conn = sqlite3.connect('database/parking_system.db'); cursor = conn.cursor(); cursor.execute('SELECT COUNT(*) FROM users'); users = cursor.fetchone()[0]; cursor.execute('SELECT COUNT(*) FROM parking_slots'); slots = cursor.fetchone()[0]; cursor.execute('PRAGMA table_info(bookings)'); cols = len(cursor.fetchall()); conn.close(); print(f'  Users: {users}, Slots: {slots}, Booking columns: {cols}')"
echo OK - Database verified
echo.

echo ========================================
echo   ALL SERVICES STARTED!
echo ========================================
echo.
echo Services running:
echo   - Django Web Portal: http://127.0.0.1:8000/
echo   - Auto-expiry: Built into Django and Tkinter
echo.
echo To start Tkinter Admin Dashboard:
echo   python main.py
echo.
echo Press any key to open admin dashboard...
pause >nul

python main.py
