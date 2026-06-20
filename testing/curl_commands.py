# Archivist (read/analysis) branch
curl -sS -X POST http://localhost:8088/responses -H "Content-Type: application/json" -d '{"input": "Please analyze this email about the Q3 deadline update from SharePoint."}'

#  Secretary (meeting scheduling) branch
curl -sS -X POST http://localhost:8088/responses -H "Content-Type: application/json" -d '{"input": "Schedule a project sync meeting for next Wednesday at 2 PM, and send calendar invites."}'

# Career Coach
curl -sS -H "Content-Type: application/json" -X POST http://localhost:8088/responses -d '{"input": "I want plan ahead for my career"}'

# Fallback (no flags matched) branch
curl -sS -X POST http://localhost:8088/responses -H "Content-Type: application/json" -d '{"input": "Hello, how are you?"}'
curl -sS -X POST http://localhost:8088/responses -H "Content-Type: application/json" -d '{"input": "Hello, how are you? And what is the weather today? "}'
curl -sS -X POST http://localhost:8088/responses -H "Content-Type: application/json" -d '{"input": "Hello, what is the time now? "}'
curl -sS -X POST http://localhost:8088/responses -H "Content-Type: application/json" -d '{"input": "Hello, how to connect to the wifi in campus? Where to park my Tesla? What shuttles can I take to Shaw College? "}'


# Test email summary
curl -sS -X POST http://localhost:8088/responses -H "Content-Type: application/json" -d '{"input": "Please summarize the email in my account"}'


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

curl -sS -X POST http://localhost:8088/responses -H "Content-Type: application/json" -d '{"input": "Hello, I am going to have a job interview tomorrow for a social worker position in an NGO in Hong Kong. Prepare me with the interview with a detailed mock meeting using audio files"}'
# Test Career Coach for Quality

# Flux.2-pro
curl -X POST "https://1155236599-1444-resource.services.ai.azure.com/providers/blackforestlabs/v1/flux-2-pro?api-version=preview" \
-H "Content-Type: application/json" \
-H "Authorization: Bearer $AZURE_API_KEY" \
-d '{
    "prompt": "A photograph of a red fox in an autumn forest",
    "model": "FLUX.2-pro",
    "width": 1024,
    "height": 1024,
    "n": 1
}' | jq -r '.data[0].b64_json' | base64 --decode > generated_image.png
