#!/bin/bash
# Script de instalación para Linux

echo "🐧 Instalando Organizador de Archivos para Linux"

# Instalar dependencias del sistema para PySide6
echo "📦 Instalando dependencias del sistema..."
sudo apt update
sudo apt install -y python3-pip python3-venv libxcb-xinerama0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 libxcb-shape0 libxcb-xfixes0

# Crear entorno virtual
echo "🐍 Creando entorno virtual..."
python3 -m venv .venv
source .venv/bin/activate

# Instalar dependencias Python
echo "📥 Instalando dependencias Python..."
pip install -r requirements.txt

echo "✅ Instalación completada!"
echo "🚀 Para ejecutar: python3 organizador_pyside.py"