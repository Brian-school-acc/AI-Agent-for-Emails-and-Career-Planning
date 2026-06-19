# Archivist (read/analysis) branch
curl -sS -X POST http://localhost:8088/responses -H "Content-Type: application/json" -d '{"input": "Please analyze this email about the Q3 deadline update from SharePoint."}'

#  Executive (meeting scheduling) branch
curl -sS -X POST http://localhost:8088/responses -H "Content-Type: application/json" -d '{"input": "Schedule a project sync meeting for next Wednesday at 2 PM, and send calendar invites."}'

# Career Coach
curl -sS -H "Content-Type: application/json" -X POST http://localhost:8088/responses -d '{"input": "I want plan ahead for my career"}'

# Fallback (no flags matched) branch
curl -sS -X POST http://localhost:8088/responses -H "Content-Type: application/json" -d '{"input": "Hello, how are you?"}'
curl -sS -X POST http://localhost:8088/responses -H "Content-Type: application/json" -d '{"input": "Hello, how are you? And what is the weather today? "}'
curl -sS -X POST http://localhost:8088/responses -H "Content-Type: application/json" -d '{"input": "Hello, what is the time now? "}'
curl -sS -X POST http://localhost:8088/responses -H "Content-Type: application/json" -d '{"input": "Hello, how to connect to the wifi in campus? Where to park my Tesla? What shuttles can I take to Shaw College? "}'

# Test docx
curl -sS -X POST http://localhost:8088/responses -H "Content-Type: application/json" -d '{"input": "Hello, generate a word document on the topic of climate change. "}'

# Test xlsx
curl -sS -X POST http://localhost:8088/responses -H "Content-Type: application/json" -d '{"input": "Hello, generate a excel sheet of sample data on the topic of air pollution."}'

# Test pptx
curl -sS -X POST http://localhost:8088/responses -H "Content-Type: application/json" -d '{"input": "Hello, generate a powerpoint slides on the topic of human resources"}'

# Test pdf
curl -sS -X POST http://localhost:8088/responses -H "Content-Type: application/json" -d '{"input": "Hello, generate a pdf file for an event poster in the format of application form"}'

# Test File Upload and Vector Store
curl -sS -X POST http://localhost:8088/responses -H "Content-Type: application/json" -d '{"input": "Hello, upload the OUTLINE.md to the vector store for me"}'

curl -sS -H "Content-Type: application/json" \
 -X POST http://localhost:8088/responses \
 -d '{"input":"I need to block out next Thursday afternoon for an architecture review."}'

curl -sS -H "Content-Type: application/json" \
 -X POST http://localhost:8088/responses \
 -d '{"input":"What was the review for? I have forgotten that.","stream":false, "agent_session_id": "d3a76465b41aee9d05919d455e598c6981a40cdf4d4054c3f5f0d85aa9a91b3"}'

# Hardcore choices when deploy
0.5 CPU cores 1.0 Gi memory