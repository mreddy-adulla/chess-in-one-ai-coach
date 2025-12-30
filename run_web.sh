#!/bin/bash
source env.sh
if [ -d "web" ]; then
  cd web
fi
npm start
