@echo off
echo ========================================
echo   Creando ejecutable para Windows
echo ========================================
echo.

echo Instalando PyInstaller...
pip install pyinstaller

echo.
echo Creando ejecutable...
pyinstaller --onefile --windowed ^
    --name="OrganizadorArchivos" ^
    --hidden-import=PySide6.QtCore ^
    --hidden-import=PySide6.QtGui ^
    --hidden-import=PySide6.QtWidgets ^
    organizador_pyside.py

echo.
echo ========================================
echo   ¡COMPLETADO!
echo ========================================
echo.
echo El ejecutable esta en: dist\OrganizadorArchivos.exe
echo.
pause