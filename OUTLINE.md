# 🎓 MSHK AI Agent Lab - Hackathon Project

**Student Success Multi-Agent Ecosystem for Microsoft 365 & Azure AI**

> A unified, structural breakdown mapping core student problems to a specialized **Multi-Agent Architecture**. Each sub-agent is designed with specific Microsoft/Azure tools and required skills to maximize impact for university students.

---

## 🏗️ Multi-Agent Architecture for Student Success

| **Agent Role**             | **Target Problem Solved**                                                                                                     | **Core Responsibility**                                                                                                               | **Must-Use Microsoft Tools**                                                                                                   | **Required Skills & Actions**                                                                                                        |
| --- | --- | --- | --- | --- |
| **1. 🎯 Master Orchestrator** | • Fragmented UI<br>• Student goal confusion<br>• One-for-all entry barriers                       | • Greets the user<br>• Analyzes user intent/demands<br>• Routes tasks to specialized worker agents        | • Microsoft Teams (Front-end)<br>• Microsoft Entra ID (User roles/profile authentication)                        | • Natural Language Processing (NLP)<br>• Persona Switching<br>• Multi-agent state routing                |
| **2. 📚 The Archivist**       | • "Sea of emails"<br>• Missed college weekly updates<br>• Junk/Mass mail overload                 | • Extracts and sanitizes critical info<br>• Maps queries to your 7 categories<br>• Flags hidden deadlines | • Azure AI Search (Index)<br>• Microsoft Graph API (Outlook Mail)<br>• SharePoint (Intranet files) | • Semantic categorization & routing<br>• KQL/OData query generation<br>• Text summarization & extraction |
| **3. 📅 The Executive**       | • Discrete, dull calendars<br>• Poor execution of small tasks<br>• Missed event registration      | • Automates time management<br>• Synchronizes task completion loops<br>• Handles administrative approvals | • Microsoft Graph API (Calendar)<br>• Planner / To Do<br>• Power Automate Workflows                | • Dynamic calendar time-blocking<br>• Automated task creation<br>• Trigger-based background alerts       |
| **4. 💼 The Career Coach**    | • Difficult adaptation to workplaces<br>• Low internship promotion<br>• Weak workplace simulation | • Guides career readiness<br>• Optimizes professional branding<br>• Simulated office practice             | • OneDrive (Resume storage)<br>• External LinkedIn API<br>• Code Interpreter (Sandbox)             | • Document formatting (Word OpenXML)<br>• AI mock-interview roleplaying<br>• Skill-gap analysis matching |

## 🏆 The "Hackathon Winning Workflow" Example

To show the judges how this multi-agent design operates seamlessly behind the scenes, you can present this sequence during your pitch:

1. **The Trigger:** A student clicks on the "Scholarships & Competitions" tab in your Teams interface.
    
2. **Orchestrator Action:** The **Master Orchestrator** detects the intent and awakens **The Archivist**.
    
3. **Data Retrieval:** **The Archivist** uses your `extract_relevant_emails` tool to pull recent mass emails containing keywords like _"Hackathon"_ or _"Funding"_ and isolates a deadline date.
    
4. **Task Hand-off:** The Orchestrator takes that date and hands it to **The Executive**, which automatically schedules dedicated prep time in the student's Outlook Calendar and builds a checklist in Microsoft Planner.
    
5. **Career Value Add:** Simultaneously, the Orchestrator prompts **The Career Coach** to analyze the competition guidelines and output a tailored project brainstorming draft directly into the student's OneDrive.
    

This layout clearly shows the Microsoft judges that you aren't just building an isolated chatbot—you are constructing an integrated, autonomous ecosystem that maximizes the full power of **M365 and Azure AI Foundry**.

---

## 🎯 Agent Design Guidelines & Best Practices

### Universal Principles

| Principle | Description |
| --- | --- |
| **Single Responsibility** | Each agent owns ONE primary domain (email management, scheduling, coding, etc.). Avoid scope creep. |
| **Clear State Management** | Agents must maintain context across turns. Use persistent session state stored in Azure Cosmos DB or similar. |
| **Graceful Degradation** | If an external API fails (e.g., Microsoft Graph), agents should offer cached/fallback responses. |
| **User Intent Recognition** | Implement confidence scores for intent routing. Route to backup agents if confidence < threshold. |
| **Audit Trail & Transparency** | Log all agent decisions for compliance & debugging. Show users what the agent is doing in real-time. |

---

## 🚀 Getting Started: Implementation Roadmap

### Phase 1: MVP
- [ ] Master Orchestrator core routing logic
- [ ] The Archivist email extraction pipeline
- [ ] IDE Agent basic code completion

### Phase 2: Integration
- [ ] Carefully Implement Features as Modular Components
- [ ] Graph API connections (Calendar, Mail, Tasks)
- [ ] IDE Agent Git automation

### Phase 3: Polish & Demo
- [ ] End-to-end workflow testing
- [ ] Performance optimization
- [ ] Hackathon pitch preparation