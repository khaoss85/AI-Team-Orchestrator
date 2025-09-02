#!/bin/bash

echo "Testing conversational API with document query..."

curl -X POST "http://localhost:8000/api/conversation/workspaces/0de74da8-d2a6-47c3-9f08-3824bf1604e0/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Can you summarize book.pdf for me?", "chat_id": "knowledge-base"}'

echo ""
echo "Done."