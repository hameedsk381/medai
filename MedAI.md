

# PRD

## Product Name

**MedVoice AI**

AI voice assistant for clinics and hospitals to automate patient phone calls, appointment scheduling, and administrative workflows.

---

# 1. Problem

Clinics receive **hundreds of patient calls daily** for:

* Appointment booking
* Prescription renewals
* Test results
* Doctor availability
* General inquiries

Problems today:

1. Receptionists cannot handle peak call volume.
2. Patients wait **10–40 minutes on hold**.
3. Staff spend **60–70% of time on repetitive admin work**.
4. Clinics lose appointments due to missed calls.

Result:

* poor patient experience
* higher operational cost
* overloaded staff

---

# 2. Goal

Build an **AI voice receptionist** that answers patient calls automatically and completes tasks without human intervention.

Primary outcomes:

* Reduce call center load **70–80%**
* Handle **1000+ concurrent calls**
* Automate appointment workflows
* Integrate with clinic software

---

# 3. Target Users

### Primary Users

Healthcare clinics and hospitals

Examples:

* GP clinics
* small hospitals
* diagnostic centers
* telemedicine providers

### End Users

Patients calling the clinic.

---

# 4. Key Use Cases

### 1. Appointment Booking

Patient calls clinic.

AI conversation:

```
AI: Hello, thank you for calling ABC Clinic.
How can I help you today?

Patient: I need to book an appointment.

AI: Which doctor would you like to see?

Patient: Dr Sharma.

AI: The earliest available slot is tomorrow at 10:30 AM.
Should I book it?
```

AI books appointment automatically.

---

### 2. Appointment Status

Patient asks:

* When is my appointment?
* Can I reschedule?

AI fetches data and responds.

---

### 3. Prescription Renewal

Patient:

"I need refill for my blood pressure medication."

AI:

* verifies patient
* records request
* forwards to doctor.

---

### 4. Test Results Inquiry

AI checks system and responds or routes to nurse.

---

### 5. Call Routing

If request is complex:

AI transfers call to staff.

---

# 5. Core Features

## 1. AI Voice Agent

Capabilities:

* answer incoming calls
* natural conversation
* multi-language support
* context awareness

Tech:

* speech to text
* LLM conversation
* text to speech

---

## 2. Appointment System Integration

Integrates with:

* hospital management systems
* scheduling systems
* calendars

Functions:

* check availability
* book appointment
* reschedule
* cancel

---

## 3. Patient Identity Verification

Methods:

* phone number
* date of birth
* OTP

---

## 4. Workflow Automation

Examples:

* prescription requests
* lab report notifications
* follow-up reminders

---

## 5. Human Escalation

AI transfers call when:

* patient asks for human
* medical emergency detected
* confidence score low

---

## 6. Analytics Dashboard

Clinic admins see:

* number of calls handled
* average call duration
* tasks completed
* missed calls saved

---

# 6. Non-Functional Requirements

### Latency

Voice response under **1.5 seconds**

### Reliability

99.9% uptime

### Scalability

Handle **10,000 concurrent calls**

### Compliance

Healthcare privacy standards

* HIPAA
* GDPR
* local healthcare regulations

---

# 7. Technical Architecture

## Telephony Layer

Options:

* Twilio
* Plivo
* Vonage

Handles:

* call routing
* SIP integration
* PSTN connection

---

## Voice AI Layer

Pipeline:

```
Call Audio
   ↓
Speech-to-Text
   ↓
LLM Conversation Engine
   ↓
Action Execution
   ↓
Text-to-Speech
   ↓
Response Audio
```

Technologies:

Speech recognition:

* Whisper
* Deepgram
* AssemblyAI

TTS:

* ElevenLabs
* Azure Speech

---

## LLM Layer

Responsible for:

* conversation
* intent detection
* workflow execution

Possible models:

* GPT
* Claude
* Llama

---

## RAG Knowledge Layer

Stores clinic information:

* doctors
* timings
* services
* FAQs

Database:

* vector DB
* knowledge base

---

## Workflow Engine

Handles actions:

* book appointment
* cancel appointment
* create ticket

Example stack:

* Temporal
* custom microservices

---

## Integration Layer

APIs to:

* hospital ERP
* EHR systems
* calendar systems

---

## Admin Dashboard

Web portal for clinics.

Features:

* view conversations
* configure workflows
* manage doctors
* analytics

Tech:

Next.js
Postgres
Redis

---

# 8. Data Model

Core entities:

Patient

```
id
name
phone
dob
medical_id
```

Appointment

```
doctor
date
time
status
patient_id
```

Call Log

```
call_id
patient_id
intent
duration
transcript
result
```

---

# 9. MVP Scope

Version 1 must support:

* incoming calls
* appointment booking
* appointment status
* call transfer to human
* admin dashboard
* analytics

---

# 10. Future Features

Phase 2:

* WhatsApp integration
* AI call summaries
* SMS reminders

Phase 3:

* AI triage
* symptom checking
* insurance verification

---

# 11. Monetization

SaaS pricing.

Example:

Starter
$299/month
500 calls

Growth
$999/month
5000 calls

Enterprise
custom pricing

---

# 12. Success Metrics

Measure:

Call automation rate
target: **70%**

Average call time reduction
target: **50%**

Patient satisfaction score

Missed call reduction

---

# 13. Risks

1. Speech recognition accuracy
2. medical liability
3. healthcare compliance
4. integration with legacy systems

---

# Honest Reality

The **hard part is not the LLM**.

The hard parts are:

1. telephony infrastructure
2. latency in voice conversations
3. workflow orchestration
4. hospital software integrations

Most founders underestimate this.

