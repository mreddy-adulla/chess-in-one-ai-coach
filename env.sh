#!/bin/bash
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
nvm use default
source backend/venv/bin/activate
export REACT_APP_API_BASE_URL="http://localhost:8080"
export DATABASE_URL="sqlite+aiosqlite:///$(pwd)/chess_coach.db"
