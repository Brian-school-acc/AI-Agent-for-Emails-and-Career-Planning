# Student Success Multi‑Agent Ecosystem

A hackathon project for **MSHK AI Agent Lab** – an intelligent multi‑agent workflow that routes user requests to specialized agents (Archivist, Executive, Career Coach) using Azure AI Foundry and Microsoft Graph integration.

![MIT License](https://img.shields.io/badge/license-MIT-green)

---

## 📖 What This Project Does

Students face information overload, fragmented calendars, and unclear career guidance. This system orchestrates four AI agents:

| Agent | Role |
|-------|------|
| **Triage Manager** | Analyzes intent and routes to the correct specialist |
| **Archivist** | Extracts deadlines and insights from emails/documents |
| **Executive** | Creates schedules, tasks, and operational plans |
| **Career Coach** | Improves resumes and provides career roadmaps |

All agents run locally via a **Responses API server** on `http://localhost:8088`. Send a request, the workflow routes it, and you receive a structured answer.

---

## 🛠️ Setup Instructions (for programmers new to Git)

### 1. Install Git & Python

- **Git**: Download from [git-scm.com](https://git-scm.com/). Verify with `git --version`.
- **Python 3.10+**: Download from [python.org](https://python.org). Verify with `python --version`.

### 2. Clone the repository

```bash
git clone https://github.com/your-org/student-success-agent.git
cd student-success-agent
```

### 3. Manage branches and changes (basic Git workflow)

```bash
# Create your own branch to work safely
git checkout -b feature/your-name

# After making changes, see what changed
git status

# Stage all changes
git add .

# Commit with a meaningful message
git commit -m "Add: improved triage prompt"

# Push your branch to the remote repository
git push origin feature/your-name
```

> **Tip**: Never commit directly to `main`. Always work on a feature branch and later create a Pull Request.

### 4. Set up Python environment

```bash
# Create a virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 5. Configure environment variables (`.env` file)

Create a file named `.env` in the project **root folder** (same level as `server.py`). Open it with any text editor and add the following lines:

```ini
FOUNDRY_PROJECT_ENDPOINT=https://your-foundry-project.openai.azure.com/
AZURE_AI_MODEL_DEPLOYMENT_NAME=gpt-oss-120b
```

> **Explanation**:
> - `FOUNDRY_PROJECT_ENDPOINT` – Your Azure AI Foundry project endpoint (e.g., `https://<region>.api.cognitive.microsoft.com/` or a custom domain).
> - `AZURE_AI_MODEL_DEPLOYMENT_NAME` – The deployment name of your model in Azure AI Foundry. Here we use `gpt-oss-120b` (a placeholder – replace with your actual deployment name).

If you also need to authenticate via Azure CLI or service principal, add these optional variables:

```ini
AZURE_CLIENT_ID=your-client-id
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_SECRET=your-client-secret
```

But the simplest is to run `az login` once – `DefaultAzureCredential()` will then work without extra variables.

---

## 🚀 How to Run the Server

```bash
python server.py
```

You should see:

```
🚀 Starting local Agent Response Server interface on http://localhost:8088...
```

The server stays running until you press `Ctrl+C`. It exposes a single endpoint: `POST /responses`.

---

## 🧪 Testing with `curl` Commands

Open a **new terminal** (keep the server running) and run the following examples.

### 1. Archivist branch (read/analysis)

```bash
curl -sS -X POST http://localhost:8088/responses \
  -H "Content-Type: application/json" \
  -d '{"input": "Please analyze this email about the Q3 deadline update from SharePoint.", "stream": false}'
```

### 2. Executive branch (meeting scheduling)

```bash
curl -sS -X POST http://localhost:8088/responses \
  -H "Content-Type: application/json" \
  -d '{"input": "Schedule a project sync meeting for next Wednesday at 2 PM, and send calendar invites.", "stream": false}'
```

### 3. Career Coach branch

```bash
curl -sS -X POST http://localhost:8088/responses \
  -H "Content-Type: application/json" \
  -d '{"input": "I want to plan ahead for my career", "stream": false}'
```

### 4. Fallback branch (no flags matched)

```bash
curl -sS -X POST http://localhost:8088/responses \
  -H "Content-Type: application/json" \
  -d '{"input": "Hello, how are you?", "stream": false}'
```

### 5. Multi-turn conversation (using `agent_session_id`)

First request creates a session; copy the returned `agent_session_id`. Use it in later requests to maintain context:

```bash
# Request 1
curl -sS -X POST http://localhost:8088/responses \
  -H "Content-Type: application/json" \
  -d '{"input": "I need to block out next Thursday afternoon for an architecture review.", "stream": false}'

# Request 2 (continuing the same session)
curl -sS -X POST http://localhost:8088/responses \
  -H "Content-Type: application/json" \
  -d '{"input": "What was the review for? I have forgotten that.", "stream": false, "agent_session_id": "d3a76465b41aee9d05919d455e598c6981a40cdf4d4054c3f5f0d85aa9a91b3"}'
```

> Replace the session ID with the one you received from the first response.

---

## 📝 TODO List (`todo.md`)

The following items are planned for future iterations. We maintain a separate `todo.md` file in the repository. Its current content:

```markdown
# TODO

## Agents
- [ ] Add a fallback **FrontDeskAgent** for general conversation
- [ ] Integrate tools:
  - [ ] Web search (Bing / Tavily)
  - [ ] File search (local / SharePoint)
- [ ] Improve response output format (currently raw JSON in playground)
- [ ] Refine prompts for better accuracy

## Microsoft Services Integration
- [ ] Outlook (calendar read/write)
- [ ] Word (document generation)
- [ ] PowerPoint (slide creation)

## Testing
- [ ] Quality of document content analysis
- [ ] Accuracy of CUHK‑specific data retrieval

## Out of Scope (Will NOT do)
- Memory (short/long term) → requires Redis, too heavy
- Persistent storage → built on memory only
- Conversation orchestration → Copilot should handle that
```

---

## 🧑‍💻 Developer Notes

- The workflow is defined in `server.py` using `WorkflowBuilder`. It’s a DAG with conditional edges.
- Structured outputs (`TriageResult`, `EmailResponse`) guarantee type safety.
- Monkeypatching of `FileCheckpointStorage` allows serialization of Azure SDK enums (MessageRole) and streaming events.
- All agents use the same `FoundryChatClient` – swap the model by changing `AZURE_AI_MODEL_DEPLOYMENT_NAME` in `.env`.

---

## 📄 License

MIT – feel free to use and extend for your own hackathon or production project.

---

**Built with ❤️ for MSHK AI Agent Lab**