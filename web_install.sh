#!/bin/bash
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
nvm use default
cd web && npm install --legacy-peer-deps && npm i --save-dev @types/node --legacy-peer-deps
