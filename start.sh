#!/bin/bash

echo "🚀 Step 0: Source ENV..."
cd /root/Projects/bitkub-dca-line
source venv/bin/activate
sleep 5

echo "🚀 Step 1: Start FastAPI server..."
cd /root/Projects/bitkub-dca-line/backend
nohup uvicorn main:app --reload --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
sleep 10

echo "🌐 Step 2: Start Ngrok on port 8000..."
nohup ngrok http 8000 > ngrok.log 2>&1 &
sleep 10

echo "🔎 Step 3: Extract Ngrok URL..."
cd /root/Projects/bitkub-dca-line
python get_ngrok_url.py
sleep 5

echo "🌍 Step 4: Deploy frontend to Netlify..."
cd /root/Projects/bitkub-dca-line/frontend
netlify deploy --prod

echo "✅ Done! Your Bitkub DCA app is live."
