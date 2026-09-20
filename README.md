# ScamCheck

### Verify Before You Trust

AI-assisted scam-risk analysis for jobs, internships, and scholarship opportunities.

🔗 **Live Demo:** https://scam-check-zeta.vercel.app/

---

## 🚨 Problem

Students frequently encounter fake internships, jobs, and scholarship opportunities that use:

- Registration or application fees
- Requests for payment screenshots or transaction IDs
- Instant-selection claims
- Referral incentives
- Suspicious forms and contact details
- Urgency-based messaging

ScamCheck helps users analyze these opportunities before sharing personal information or making payments.

---

## 💡 Solution

ScamCheck combines multiple signals instead of relying on a single keyword or AI response.

### Multi-Signal Analysis

**1. Structural Signals**
- Welcome-letter patterns
- Batch codes
- Annexure references
- Instant selection language
- Referral incentives
- Flexible joining dates

**2. Technical Signals**
- Contact email/domain analysis
- Google Form field analysis
- Payment-related fields
- UPI / transaction ID / UTR requests
- Registration fees
- Referral codes

**3. Contextual Signals**
- AI-assisted analysis using Groq
- Payment context
- Urgency
- Recruitment process
- Referral patterns

Python-based deterministic rules combine these signals to produce:

- 🟢 Likely Safe
- 🟡 Caution
- 🔴 High Risk

---

## 🛠️ Tech Stack

### Frontend
- React
- Vite
- CSS

### Backend
- Python
- Flask
- Gunicorn

### AI
- Groq API
- LLM-based contextual reasoning

### Analysis
- BeautifulSoup
- Regex-based detection
- Google Forms parsing
- URL validation
- Deterministic risk fusion

---

## 🔄 How It Works

```text
User Input
    ↓
Content / URL Analysis
    ↓
Signal Collection
    ↓
Structural + Technical + Contextual Analysis
    ↓
Deterministic Risk Fusion
    ↓
Risk Verdict + Evidence + Actionable Advice
```

---

## 🎯 Use Cases

- Internship verification
- Job posting analysis
- Scholarship opportunity checking
- Suspicious Google Form analysis
- Scam message analysis

---

## 🚀 Live Demo

Try ScamCheck here:

https://scam-check-zeta.vercel.app/

---

## ⚠️ Disclaimer

ScamCheck is a risk-analysis and verification assistant. It does not guarantee that an opportunity is legitimate or fraudulent. Users should independently verify organizations through official and trusted sources before sharing personal information or making payments.

---

## 👨‍💻 Built For

**HACKDAY 1.0 — DECODEP**

Theme: **Tech for a Better Tomorrow**
