#!/bin/bash
echo "🐧 Instalando para Arch Linux"

# Instalar dependencias
sudo pacman -S python-pip python-virtualenv

# Crear entorno virtual
python -m venv .venv
source .venv/bin/activate

# Instalar PySide6
pip install pyside6

echo "✅ Listo! Ejecuta: python organizador_pyside.py"