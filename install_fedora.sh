#!/bin/bash
echo "🦊 Instalando para Fedora"

# Instalar dependencias
sudo dnf install python3-pip python3-virtualenv

# Crear entorno virtual
python3 -m venv .venv
source .venv/bin/activate

# Instalar PySide6
pip install pyside6

echo "✅ Listo! Ejecuta: python3 organizador_pyside.py"