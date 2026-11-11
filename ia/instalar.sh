#!/bin/sh
# Activa en esta copia los hooks de git comunes (ia/githooks). Ejecutar una vez por clon:
#   sh ia/instalar.sh
# Sirve igual si trabaja Claude, Codex, Gemini CLI u otra IA con terminal, o una persona.
set -eu
root=$(git rev-parse --show-toplevel)
cd "$root"
chmod +x ia/githooks/pre-commit ia/githooks/pre-push
git config core.hooksPath ia/githooks
echo "Hooks activos: $(git config core.hooksPath). Prueba: python3 ia/test_guard.py"
