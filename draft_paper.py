curl -sS -H "Content-Type: application/json" -X POST http://localhost:8088/responses -d '{"input": "Write a haiku about deploying cloud applications.", "stream": false}'
curl -sS -H "Content-Type: application/json" -X POST http://localhost:8088/responses -d '{"input": "Tell me about your how I can use your service.", "stream": false}'
curl -sS -H "Content-Type: application/json" -X POST http://localhost:8088/responses -d '{"input": "I want plan ahead for my career", "stream": false}'
curl -X POST http://localhost:8080/run -H "Content-Type: application/json" -d '{"message": "I would like to plan for the conference meeting next week"}'
curl -X POST -H "Content-Type: application/json" -d '{"message":"dev123"}' http://localhost:8088/responses


# Archivist (read/analysis) branch
curl -sS -X POST http://localhost:8088/responses -H "Content-Type: application/json" -d '{"input": "Please analyze this email about the Q3 deadline update from SharePoint."}'

#  Executive (meeting scheduling) branch
curl -sS -X POST http://localhost:8088/responses -H "Content-Type: application/json" -d '{"input": "Schedule a project sync meeting for next Wednesday at 2 PM, and send calendar invites."}'

# Career Coach
curl -sS -H "Content-Type: application/json" -X POST http://localhost:8088/responses -d '{"input": "I want plan ahead for my career"}'

# Fallback (no flags matched) branch
curl -sS -X POST http://localhost:8088/responses -H "Content-Type: application/json" -d '{"input": "Hello, how are you?"}'


curl -sS -H "Content-Type: application/json" \
 -X POST http://localhost:8088/responses \
 -d '{"input":"I need to block out next Thursday afternoon for an architecture review."}'

curl -sS -H "Content-Type: application/json" \
 -X POST http://localhost:8088/responses \
 -d '{"input":"What was the review for? I have forgotten that.","stream":false, "agent_session_id": "d3a76465b41aee9d05919d455e598c6981a40cdf4d4054c3f5f0d85aa9a91b3"}'