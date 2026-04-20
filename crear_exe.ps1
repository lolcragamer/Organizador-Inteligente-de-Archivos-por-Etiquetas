Write-Host "Creando ejecutable para Windows..." -ForegroundColor Green

# Instalar PyInstaller
pip install pyinstaller

# Crear ejecutable
pyinstaller --onefile --windowed `
    --name="OrganizadorArchivos" `
    --icon=icono.ico `
    organizador_pyside.py

Write-Host "`n✅ Ejecutable creado en: dist\OrganizadorArchivos.exe" -ForegroundColor Green