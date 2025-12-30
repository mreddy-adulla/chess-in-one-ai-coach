#!/bin/bash
source env.sh
cd backend && uvicorn api.main:app --reload --port 8080
