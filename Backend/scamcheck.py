import re
import json
import requests
import os

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

SCAM_TEMPLATE_MARKERS = {
    "Welcome letter language": r"welcome letter",
    "Batch code": r"batch code",
    "Annexure A/B": r"annexure\s*[-–]\s*[ab]",
    "Enrolment confirmation request": r"to confirm your enrol?ment",
    "Flexible joining date": r"flexible joining date",
    "Instant selection language": r"selected for the internship program",
    "Referral incentive": r"refer\s+(a\s+)?friend",
    "Referral bonus/reward": r"referral\s+(bonus|reward|code)",
}

def check_structural_pattern(text):
    text_l = text.lower()

    hits = [
        label
        for label, pattern in SCAM_TEMPLATE_MARKERS.items()
        if re.search(pattern, text_l)
    ]

    return {
        "flag": len(hits) >= 2,
        "matched": hits
    }

def check_technical_signals(text):
    email_match = re.search(r'[\w\.-]+@[\w\.-]+', text)
    if not email_match:
        return {"flag": False, "note": "no contact email found in text"}
    domain = email_match.group(0).split('@')[-1]
    generic = domain.lower() in ['gmail.com','yahoo.com','outlook.com','hotmail.com']
    return {"flag": generic, "note": f"contact via {domain}"}

def scrape_google_form(url):
    try:
        resp = requests.get(
            url,
            timeout=8,
            headers={"User-Agent": "Mozilla/5.0"},
            allow_redirects=True
        )

        if resp.status_code >= 400:
            return {
                "flag": False,
                "error": "Could not access the form.",
                "all_questions": []
            }

        match = re.search(
            r'FB_PUBLIC_LOAD_DATA_\s*=\s*(\[.*?\]);',
            resp.text,
            re.DOTALL
        )

        if not match:
            return {
                "flag": False,
                "error": "Could not parse form.",
                "all_questions": []
            }

        raw = match.group(1)

        questions = re.findall(
            r'"([^"]{5,200})"',
            raw
        )

        red_flag_terms = [
            "upi",
            "payment screenshot",
            "transaction id",
            "amount paid",
            "utr number",
            "bank account",
            "registration fee",
            "refer a friend",
            "referral code"
        ]

        hits = [
            q for q in questions
            if any(term in q.lower() for term in red_flag_terms)
        ]

        return {
            "flag": len(hits) > 0,
            "matched_fields": hits,
            "all_questions": questions[:15]
        }

    except requests.RequestException:
        return {
            "flag": False,
            "error": "Could not access the form.",
            "all_questions": []
        }
    except Exception:
        return {
            "flag": False,
            "error": "Unexpected error while reading the form.",
            "all_questions": []
        }

def scrape_generic_page(url):
    from bs4 import BeautifulSoup

    try:
        resp = requests.get(
            url,
            timeout=8,
            headers={"User-Agent": "Mozilla/5.0"},
            allow_redirects=True
        )

        if resp.status_code >= 400:
            return ""

        soup = BeautifulSoup(resp.text, "html.parser")

        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()

        return soup.get_text(
            separator=" ",
            strip=True
        )[:5000]

    except requests.RequestException:
        return ""
    except Exception:
        return ""

def call_groq_contextual(text, a_result, b_result):
    prompt = f"""You are given a job/internship posting and two pre-computed signal checks (weak, non-decisive alone):
- structural_pattern: {json.dumps(a_result)}
- technical_signal: {json.dumps(b_result)}

Analyze ONLY these contextual signals:
1. payment_context: none / reasonable-refundable-official / suspicious-personal-account
2. urgency_language: normal / artificial-pressure
3. description_specificity: concrete-duties / vague-buzzwords
4. recruitment_process: real-interview-mentioned / instant-selection-no-process
5. referral_incentive: none / present

Return JSON only, no markdown fences:
{{
  "contextual_flag": true or false,
  "flags_triggered": ["reason: explanation"],
  "follow_up_question": "one specific verification question",
  "advice": "1-2 sentences"
}}

Posting: \"\"\"{text}\"\"\""""

    resp = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    raw = resp.choices[0].message.content.strip()
    raw = re.sub(r'^```json\s*|\s*```$', '', raw)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"contextual_flag": False, "flags_triggered": ["parse_error"], "follow_up_question": "", "advice": ""}

def fuse_verdict(a_flag, b_flag, c_flag):
    flags = sum([a_flag, b_flag, c_flag])
    if (a_flag and c_flag) or flags >= 2:
        return "High Risk"
    elif flags == 1:
        return "Caution"
    return "Likely Safe"

def analyze_input(input_type, content, url=None):
    # Collect text from the user and/or the supplied URL
    text_parts = []

    if content:
        text_parts.append(content)

    # If a URL is supplied, inspect it
    if url:
        if "docs.google.com/forms" in url:
            url_result = scrape_google_form(url)

            if url_result.get("all_questions"):
                text_parts.append(
                    "Google Form fields: "
                    + str(url_result["all_questions"])
                )

            # Google Form payment/referral findings are a technical signal
            url_technical = url_result
        else:
            scraped_text = scrape_generic_page(url)

            if scraped_text:
                text_parts.append(scraped_text)

            url_technical = check_technical_signals(
                scraped_text if scraped_text else ""
            )
    else:
        url_technical = None

    # We need at least some content to analyze
    if not text_parts:
        return {
            "error": "Please provide posting text or an application URL."
        }

    text_for_llm = "\n\n".join(text_parts)

    # Category A — Structural
    a_result = check_structural_pattern(text_for_llm)

    # Category B — Technical
    text_technical = check_technical_signals(text_for_llm)

    # Combine technical evidence from text + URL
    b_flag = text_technical["flag"]

    if url_technical:
        b_flag = b_flag or url_technical.get("flag", False)

    b_result = {
        "flag": b_flag,
        "text_signal": text_technical,
        "url_signal": url_technical
    }

    # Category C — Contextual LLM
    c_result = call_groq_contextual(
        text_for_llm,
        a_result,
        b_result
    )

    # Deterministic fusion remains the final authority
    verdict = fuse_verdict(
        a_result["flag"],
        b_result["flag"],
        c_result["contextual_flag"]
    )

    return {
        "verdict": verdict,
        "structural": a_result,
        "technical": b_result,
        "contextual": c_result
    }