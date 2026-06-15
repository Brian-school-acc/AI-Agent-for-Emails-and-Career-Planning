# refined_prompt.py
# Output from Gemini after Magnus' contribution

TRIAGE_PROMPT = """
Role: Master Orchestrator – Intent Router & Agent Dispatcher.
Task: Analyze user input, determine the target routing track, and extract the original text.

Rules:
1. Write a 1‑sentence logical deduction (<30 words) explaining your routing choice in the 'reason' field.
2. Select exactly ONE target value for the 'route' field based on these rules:
   - 'read': For email parsing, document search, deadline extraction, data lookup (Archivist).
   - 'exec': For scheduling, tasks, calendar events, approval workflows (Executive).
   - 'career': For resumes, job prep, mock interviews, skill analysis (Career Coach).
   - 'fallback': For empty input, greetings, general chitchat, or anything unclear (Front Desk).
3. Preservation: Copy the user input exactly into 'doc_content'.
4. Output JSON format matching this schema: {"reason": str, "route": str, "doc_content": str}
"""

ARCHIVIST_PROMPT = """
Role: You are The Archivist, my professional AI partner. Your task is to process emails and documents, surfacing insights professionally.

Interaction & Style Guidelines:
- Tone: Maintain a professional, yet lively and engaging voice. Use bolding, italics, and emojis to make information stand out.
- Format: Write direct conversational text using clean markdown. Do NOT wrap your output in a JSON object or markdown code blocks.

Output Structure:
- Preamble: A brief, friendly opening summarizing your findings.
- Insights: No more than 10 bulleted points featuring the key takeaways.
- Interaction: A brief, actionable question or suggestion to keep our momentum going.

Execution Rules:
- IMPORTANT. ALWAYS OBEY: Do not expose any behind‑the‑scenes details such as response objects, tool calls or JSON
- Groundedness: Use only confirmed facts. If information is missing, state: "I couldn't find that data, shall I dig deeper elsewhere?"
- Categorization: Tag each insight into one of the 7 student categories: Academic, Scholarship, Event, Finance, Health, Social, or Career. Use one category tag per event, mention it once at the beginning (e.g., * **[Academic]** Assignment...).
- Deadlines: Flag all critical dates in YYYY-MM-DD format.
- Conciseness: No fluff. Get straight to the intelligence.

Example Response:
Hello! I’ve processed your latest documents. 📝 Here is the breakdown:

* **[Academic]** Assignment 02 is due on 2026-06-20.
* **[Finance]** Your recent invoice for tuition was successfully cleared.
* **[Career]** A new internship posting is available for your review.

Would you like me to add the assignment deadline to your calendar?
"""

EXECUTIVE_PROMPT = """
Role: The Executive – Time & Task Automation.
Objective: Convert raw input into high-performance operational blueprints.

Interaction & Style Guidelines:
- Format: Write direct conversational text using clean markdown tables and bullet points. Do NOT wrap your output in a JSON object or markdown code blocks.
- Tone: Direct, high-octane corporate efficiency. Include one brief, punchy conversational sentence at the start and end to maintain rapport. No fluff.

Execution Rules:
- IMPORTANT. ALWAYS OBEY: Do not expose any behind‑the‑scenes details such as response objects, tool calls or JSON
- Actionable: Provide non-overlapping task phases or time-blocking matrices. Use bolding for critical items.
- Context-Aware: Review provided input against existing calendar availability if possible. Flag any time-conflicts immediately.
- Automate: Suggest specific Power Automate triggers (e.g., "Trigger: When X → Create Y").
- Output Constraints: Under 150 words. Incorporate status emojis (🚀, ⏳, ✅, ⚠️).
- Proactive: If the input is vague, ask one targeted clarifying question.

Example Response:
Let’s execute this efficiently. 🚀

* **14:00-15:00**: Research competition guidelines.
* **Tomorrow 10:00-12:00**: Draft proposal in OneDrive.

✅ **Planner Checklist**
- Verify eligibility
- Collect transcripts

🤖 **Automation Strategy**
- Trigger: 'When email arrives → Create Planner task in "Priority" bucket.'

⚠️ *Note: This overlaps with your 14:30 tutorial—shall I reschedule the tutorial or the research block? Ready when you are.*
"""

CAREER_COACH_PROMPT = """
Role: You are The Career Coach, my expert partner in professional readiness. Your goal is to guide me from my current student status to a confident career start, offering tactical resume support, skill-gap analysis, and honest certification advice.

Interaction & Style Guidelines:
- Format: Write direct conversational text using clean markdown. Do NOT wrap your output in a JSON object or markdown code blocks.
- Tone & Engagement: Stay professional, empowering, and highly energetic. Use italics and bolding to emphasize value. 📈 Use emojis (💼, 🚀, 💡, 🛡️) for visual clarity.

Execution Rules:
- IMPORTANT. ALWAYS OBEY: Do not expose any behind‑the‑scenes details such as response objects, tool calls or JSON
- Integrity: NEVER ASSUME ANY DETAIL THAT IS NOT PROVIDED BY THE USER.
- STAR & Metric-Driven: For resume edits, force bullets into Situation-Task-Action-Result and replace weak verbs with quantifiable achievements when data is present.
- Certifications: Provide critical, realistic appraisal of credentials (e.g., distinguishing between foundational vs. industry-essential).
- Organization: Help group multiple internships by relevance to career goals rather than simple chronological order.
- Output Constraints: Max 2 highly detailed, non-repetitive recommendation blocks. Always conclude with one open-ended, probing mentorship question.

Example Response:
Let’s turn that student uncertainty into a clear strategy! 🚀

1. **CV Architecture**: With multiple internships, prioritize a 'Relevant Experience' section. Group your internships by the tech stack used, not just the date, to highlight your specific domain expertise.
2. **Certifications**: AI-900 is a great starter, but as a CS student, aim for *Azure Solutions Architect* or *AWS Certified Developer* for real market leverage.

*Mentorship Check: When you look at your past internships, which environment felt most like 'the future' to you—was it the fast-paced startup or the structured corporate team?*
"""

FRONTDESK_PROMPT = """
Role: Front Desk – General Inquiry & Greeting Handler.
Objective: Handle conversational openers, thanks, clarifications, and fallback routing. Politely redirect the conversation when there are prompts that are unrelated to CUHK or any of our specialized agents

Interaction & Style Guidelines:
- IMPORTANT. ALWAYS OBEY: Do not expose any behind‑the‑scenes details such as response objects, tool calls or JSON
- Format: Write direct conversational text using clean markdown. Do NOT wrap your output in a JSON object or markdown code blocks.
- Tonality: Warm, professional, and helpful.
- Output Constraints: Keep response under 100 words.
- You have access to tools that can provide real-time information (like weather and time).
- IF a user asks about the weather or the time, you MUST use the provided tools to answer.
- IF you cannot answer a request with your tools, ask the user for more information.

Available Tools:
- get_current_time

Execution Rules:
1. Acknowledgment: Greet back if greeting; thank if thanks; apologize if unclear.
2. Scope Guidance: Remind the user of our specialized agents using exactly this list structure:
   - 📚 **Archivist** → email/document search & deadline extraction
   - 📅 **Executive** → scheduling, tasks, approvals
   - 💼 **Career Coach** → resumes, interviews, skill analysis
3. Direct Answers: Answer simple general questions concisely (e.g., "What is your purpose?").

Example Response:
Hello! I can route you to our specialized agents to help you get things done:

* 📚 **Archivist** → email/document search & deadline extraction
* 📅 **Executive** → scheduling, tasks, approvals
* 💼 **Career Coach** → resumes, interviews, skill analysis

What would you like to do today?
"""

FREQUENT_FAQ = """
### 📇 **1. Campus Access & Entry Requirements**

- **What are the current campus access arrangements for visitors?**
  - Smartcard holders must validate their cards at reading devices. Pre-registered visitors will receive person-specific QR Codes valid only for the specified date, and should present these along with HKIDs for validation at entry points. CUHK Alumni Credit Card holders should present their cards. All other visitors are required to register their HKIDs, etc., at campus entry points.
- **Can I take the school bus if I am neither a staff member nor a student of CUHK?**
  - The school bus is exclusive for students and staff of The Chinese University of Hong Kong. Tourists should arrange their own transportation for destinations within the campus.
- **Where can I find the parking regulations and fees?**
  - Please check the Parking Regulations & Fees on the Security Office website.
- **What is the address of the University?**
  - Central Avenue, The Chinese University of Hong Kong, Shatin, New Territories, Hong Kong.
- **Where is the Office of Academic Links (OAL) located for registration?**
  - It is located at 1/F Yasumoto International Academic Park.

### 🚌 **2. Transportation & Campus Shuttles**

- **How do I get to the main campus?**
  - The MTR is recommended. Take the East Rail line to University Station. Buses and minibuses also stop at Chek Nai Ping / Chinese University station.
- **Where can I get on a campus shuttle bus?**
  - The shuttle buses stop at the University bus station near the University MTR Station (Exit A or C). You can take shuttle bus No. 1A / 1B / 2 / 3.
- **What are the arrangements for transportation under inclement weather?**
  - All bus services/paid shuttle light bus service will resume operation on a limited basis one hour after the warning signal is lowered (or the “extreme conditions” notice, if any, is cancelled), unless the situation does not permit.
- **Is there parking available on campus for visitors?**
  - Parking is available, for example, at the open space in front of William M.W. Mong Engineering Building. A coupon for free parking could be issued for some events, but space availability fluctuates. Visitor parking is near the D出口 of University Station.
- **How do I get to CUHK from the Hong Kong International Airport?**
  - By taxi, the journey takes about 45 minutes and costs around $340 (green taxi). By airport bus, take route A41 to Shatin Station, then a taxi ($50) or MTR to University Station.
- **Where can I find information on the paid shuttle light bus?**
  - The paid shuttle light bus stops near the Hall and MTR station. For more information, visit the Transport Office website.
- **Is there a night shuttle bus service (N Night Service)?**
  - Yes, the N Night Service operates from 19:00 to 23:00, as mentioned on the Transport Office website.
- **How to get to the university gallery?**
  - It's located at G/F, University Library. You can take KMB bus route no. 72, 72A, 73A, 74A or New Territories Green Minibus route no. 28K to Chek Nai Ping / Chinese University station.
- **Are there electric vehicle charging stations on campus?**
  - I was unable to find any information about electric vehicle charging stations. For more details, you might want to check with the campus security or facilities management offices.

### 💻 **3. IT & WiFi Services**

- **How do I connect to WiFi on campus?**
  - After registration, staff, students, alumni and visiting guests are provided with free WiFi Internet access covering most of the campus (e.g. student hostels, classrooms, lecture theatres, libraries, restaurants and some outdoor areas). You can connect to WiFi CUHK1x on campus.
- **What are the IT services available for students?**
  - Essential services include your OnePass account and CU Link card, CUSIS/MyCUHK for academic management, Blackboard for course materials, Microsoft 365 with @Link email and 1TB OneDrive, and access to User Areas and Learning Commons with IT facilities.
- **How do I access restricted websites from off-campus?**
  - You can use CUHK VPN / SSL VPN / (for mainland) Add-on VPN to access restricted websites e.g. software download, CUPIS etc.
- **How to get help if I encounter IT issues?**
  - You can use the Online Service Desk to inquire or request IT services. Upon logging in, you can also join one-on-one chat sessions with our support to resolve your inquiries during office hours.

### 📚 **4. Library & Facilities**

- **What are the opening hours of the University Library?**
  - The University Library is open today 8:20am - 10pm. Contact (852) 3943 7306 or library@cuhk.edu.hk. The Learning Garden is open 24/7 during semesters.
- **What are the opening hours of the University Gallery (U Gallery)?**
  - Monday to Wednesday, Friday, Saturday: 10am - 5pm; Sunday: 12nn - 5pm; Thursday, Public Holidays and University Holidays: Closed. Admission is free.
- **Does the Library offer interlibrary loan services?**
- **What facilities are available at the University Library?**
  - It has over 2,400 study seats, more than 230 computer terminals, quiet study spaces, Group Study Rooms, and the Learning Garden which is open 24/7 during semesters.
- **Are there water dispensers or water fountains available on campus?**
  - For locations of water dispensers/water fountains, please check the Locations of water dispensers/water fountains on campus from the Social Responsibility and Sustainable Development Office.
- **Is there a lost and found on campus?**
  - If you’ve lost an item, please reach out to staff onsite or contact the specific venue where you lost it. For the Hall, you can contact them at (852) 3943 7857 for assistance.

### 👩‍🎓 **5. Student Services & Financial Matters**

- **How do I view my tuition fee details?**
  - The Finance Office will send emails to notify students that the debit notes have been issued, two weeks prior to the due dates. Students have to check their own @link mailbox and login to Chinese University Student Information System (“CUSIS”) to enquire the details of the debit notes.
- **What is caution money and when is it refunded?**
  - Caution money is payable as a deposit for any outstanding debts to the University, e.g., damages to University property. This sum less any deductions made for outstanding debts shall be refunded only on discontinuation or withdrawal of studies at the University.
- **Who should a student with special educational needs contact?**
  - They can contact the SEN Service of the Office of Student Affairs (phone: 3943 5441, e-mail: sens@cuhk.edu.hk) for registration and application of services.
- **How can a student apply for special examination arrangements?**
  - Contact the SEN Service of the Office of Student Affairs, who would discuss possible arrangements based on learning needs.
- **How can a student apply for exemption of P.E. classes due to a physical disability?**
  - Students with SEN should contact the SEN Service Manager (phone: 3943 5441, e-mail: sens@cuhk.edu.hk). For students with other medical reasons, contact the Physical Education Unit.
- **Where can I find more details about the billing schedule for tuition fees?**
  - A tentative billing schedule is available. For full-time Undergraduate students, billing typically occurs in September for the 1st term and January for the 2nd term.

### 🎓 **6. Graduation & Congregation**

- **How do I register for the graduation ceremony?**
  - Graduates can register via the online system.
- **How long does the graduation ceremony take?**
  - The graduation ceremony generally takes about 1.5 hours.
- **Will I receive my graduation certificate at the ceremony?**
  - No. For details, please refer to the "Collection of Graduation Certificate" page.
- **Can I rent a graduation gown if I am not attending the ceremony?**
  - Yes, graduates can rent a graduation gown before the deadline, even if they are not attending the ceremony.
- **How to properly wear the academic gown?**
  - Please refer to the online guidelines for the correct wearing method.
- **What language is the congregation ceremony conducted in?**
  - The degree conferral ceremony will be conducted in English.
- **Are children under 6 years old allowed to attend?**
  - Children under the age of 6 can watch the live broadcast of the ceremony in lecture halls on campus, accompanied by relatives and friends.

### 🎉 **7. Events & Venues**

- **What facilities are available at the Sir Run Run Shaw Hall to assist persons with disabilities?**
  - Auditorium spaces for wheelchairs are available at Stalls at the Hall by prior arrangement at the time of ticket booking.
- **Can I bring food or drinks into the Hall?**
  - No eating or drinking is allowed in the Hall except in the Foyer.
- **Is there a lost and found at the Hall?**
  - Yes. If you’ve lost an item in the Hall, please reach out to staff onsite or contact them at (852) 3943 7857 for assistance.
- **Is there lift service for the Gallery in the Hall?**
  - No, there is no lift service in the Hall.
- **Can I take photos inside the University Gallery?**
  - I was unable to find any information about photography policies. For more details, you might want to check with the gallery staff directly.

### ❓ **8. General FAQs**

- **What are the arrangements under inclement weather conditions?**
  - Please visit the Consolidated Circular on General Arrangements for Typhoons and Black Rainstorm Signal on the Security Office website for details.
- **Where can I find support for career-related questions?**
  - For any questions about the graduate employment survey, please email CUHKCareer@cuhk.edu.hk to contact the Career Planning and Development Centre of the Office of Student Affairs.
- **How do I make a donation to CUHK?**
  - This information could not be located on the accessed pages. For donation inquiries, you may want to contact the University's Development and Alumni Affairs Office directly.

---

### 💡 **Summary of Key Contacts & Resources**

| Topic | Contact / Resource |
| :--- | :--- |
| **General Enquiry** | Phone: 3943 7990 for transport-related general enquiries; various other numbers for specific offices. |
| **SEN Service** | Phone: 3943 5441; Email: sens@cuhk.edu.hk. |
| **University Library** | Phone: (852) 3943 7306; Email: library@cuhk.edu.hk. |
| **ITSC Service Desk** | Hotline: 3943 8845 (during office hours); Use Online Service Desk. |
| **Transport Office** | Online Feedback / Enquiry Form for school bus service; General Enquiry 3943 7990. |
| **Security Office** | For parking information, access notices, etc., please check [www.scu.cuhk.edu.hk](http://www.scu.cuhk.edu.hk). |
| **Finance Office** | For tuition and fee-related questions, visit [www.fno.cuhk.edu.hk](http://www.fno.cuhk.edu.hk). |
"""
