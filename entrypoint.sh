#!/bin/sh

echo "🚀 Iniciando R-60 Bot..."

# Instalar dependencias
pip install --no-cache-dir -r /app-source/requirements.txt

# Copiar código fuente
cp -r /app-source/* /app/ 2>/dev/null || true

# Verificar credentials.json
if [ ! -f /app/credentials/credentials.json ]; then
    echo "❌ ERROR: No se encontró credentials.json"
    echo "Por favor, copia credentials.json al volumen r60_credentials"
    exit 1
fi

echo "✅ Configuración completa. Iniciando bot..."

# Ejecutar el bot
cd /app
python main.py
