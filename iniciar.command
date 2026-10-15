#!/bin/bash
# Parcialito BD: doble clic en este archivo (o ./iniciar.command en la Terminal) para abrir la app.
cd "$(dirname "$0")" || exit 1

echo ""
echo "  ==============================="
echo "    Parcialito BD - práctica SQL"
echo "  ==============================="
echo ""

if [ ! -x .venv/bin/python ]; then
  echo "  Preparando Python (solo la primera vez, tarda ~1 minuto)..."
  python3 -m venv .venv || { echo "  No pude crear el entorno de Python."; read -r -p "  Enter para salir"; exit 1; }
  .venv/bin/pip install -q --upgrade pip
  .venv/bin/pip install -q -r requirements.txt || { echo "  No pude instalar Flask/PyMySQL (¿hay internet?)."; read -r -p "  Enter para salir"; exit 1; }
fi

.venv/bin/python -m app.configurar

if ! .venv/bin/python -m app.configurar --probar; then
  echo "  Falta crear el usuario 'parcialito' en tu MySQL (solo la primera vez)."
  echo "  Escribí la contraseña de root de MySQL (la misma que usás en Workbench):"
  MYSQL_BIN="$(command -v mysql || echo /usr/local/mysql/bin/mysql)"
  "$MYSQL_BIN" -u root -p < setup/crear_usuario.sql || { echo "  No se pudo crear el usuario."; read -r -p "  Enter para salir"; exit 1; }
fi

echo "  Abriendo la app en el navegador... (dejá esta ventana abierta; Ctrl+C para cerrar)"
exec .venv/bin/python -m app.server
