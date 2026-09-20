import re
import json
import os
import requests
import ipaddress
import socket

from urllib.parse import urlparse
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
    email_match = re.search(
        r'[\w\.-]+@[\w\.-]+',
        text
    )

    if not email_match:
        return {
            "flag": False,
            "note": "no contact email found in text"
        }

    domain = email_match.group(0).split('@')[-1]

    generic = domain.lower() in [
        "gmail.com",
        "yahoo.com",
        "outlook.com",
        "hotmail.com"
    ]

    return {
        "flag": generic,
        "note": f"contact via {domain}"
    }

def validate_url(url):
    try:
        parsed = urlparse(url)

        if parsed.scheme not in ("http", "https"):
            return False, "Only HTTP and HTTPS URLs are allowed."

        if not parsed.hostname:
            return False, "Invalid URL."

        hostname = parsed.hostname.lower()

        if hostname in {
            "localhost",
            "localhost.localdomain"
        }:
            return False, "Local URLs are not allowed."

        try:
            addresses = socket.getaddrinfo(
                hostname,
                None,
                type=socket.SOCK_STREAM
            )

            for address in addresses:
                ip = ipaddress.ip_address(address[4][0])

                if (
                    ip.is_private
                    or ip.is_loopback
                    or ip.is_link_local
                    or ip.is_multicast
                    or ip.is_reserved
                    or ip.is_unspecified
                ):
                    return False, "Private or internal network URLs are not allowed."

        except socket.gaierror:
            return False, "Could not resolve the URL."

        return True, ""

    except Exception:
        return False, "Invalid URL."

def safe_get(url, timeout=8):
    valid, error = validate_url(url)

    if not valid:
        raise ValueError(error)

    return requests.get(
        url,
        timeout=timeout,
        headers={"User-Agent": "Mozilla/5.0"},
        allow_redirects=False
    )

def scrape_google_form(url):
    try:
        resp = safe_get(url)

        if resp.status_code >= 400:
            return {
                "flag": False,
                "error": "Could not access the form.",
                "all_questions": [],
                "matched_fields": []
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
                "all_questions": [],
                "matched_fields": []
            }

        raw = match.group(1)

        questions = re.findall(
            r'"([^"]{5,200})"',
            raw
        )

        questions = list(dict.fromkeys(
            q.strip()
            for q in questions
            if q.strip()
        ))

        evidence_patterns = {
            "Payment screenshot requested": [
                "payment screenshot",
                "screenshot of payment",
                "payment proof"
            ],
            "Transaction/UTR details requested": [
                "transaction id",
                "transaction number",
                "utr number",
                "utr",
                "transaction details"
            ],
            "Amount paid requested": [
                "amount paid",
                "payment amount",
                "amount you paid"
            ],
            "Bank details requested": [
                "bank account",
                "account number",
                "bank details"
            ],
            "Registration fee requested": [
                "registration fee",
                "registration fees",
                "application fee",
                "joining fee"
            ],
            "Referral code requested": [
                "referral code",
                "refer a friend"
            ]
        }

        matched_fields = []

        for question in questions:
            question_lower = question.lower()

            for label, terms in evidence_patterns.items():
                if any(term in question_lower for term in terms):
                    matched_fields.append({
                        "signal": label,
                        "evidence": question
                    })

        return {
            "flag": len(matched_fields) > 0,
            "matched_fields": matched_fields,
            "all_questions": questions[:15]
        }

    except requests.RequestException:
        return {
            "flag": False,
            "error": "Could not access the form.",
            "all_questions": [],
            "matched_fields": []
        }

    except ValueError as e:
        return {
            "flag": False,
            "error": str(e),
            "all_questions": [],
            "matched_fields": []
        }

    except Exception:
        return {
            "flag": False,
            "error": "Unexpected error while reading the form.",
            "all_questions": [],
            "matched_fields": []
        }
        
def scrape_generic_page(url):
    from bs4 import BeautifulSoup

    try:
        resp = safe_get(url)

        if resp.status_code >= 400:
            return ""

        soup = BeautifulSoup(
            resp.text,
            "html.parser"
        )

        for tag in soup([
            "script",
            "style",
            "nav",
            "footer"
        ]):
            tag.decompose()

        return soup.get_text(
            separator=" ",
            strip=True
        )[:5000]

    except requests.RequestException:
        return ""

    except ValueError:
        return ""

    except Exception:
        return ""

def call_groq_contextual(text, a_result, b_result):
    prompt = f"""You are analyzing a job, internship, scholarship, or recruitment posting.

Your job is to identify contextual risk signals using ONLY evidence explicitly present in the provided posting or form evidence.

Do not invent facts.
Do not assume an organization is fraudulent.
Do not treat Gmail, a Google Form, or any single weak signal as proof of fraud.

Pre-computed structural signal:
{json.dumps(a_result)}

Pre-computed technical signal:
{json.dumps(b_result)}

Analyze these contextual dimensions:

1. payment_context:
   - none
   - reasonable-refundable-official
   - suspicious-personal-account

2. urgency_language:
   - normal
   - artificial-pressure

3. description_specificity:
   - concrete-duties
   - vague-buzzwords

4. recruitment_process:
   - real-interview-mentioned
   - instant-selection-no-process

5. referral_incentive:
   - none
   - present

Evidence rules:

- Every item in flags_triggered MUST include the exact evidence or a faithful short quote from the posting.
- Do not create a flag unless the posting contains supporting evidence.
- If evidence is insufficient, do not flag it.
- Keep explanations concise.
- The follow_up_question must ask for something the applicant can independently verify.

Return JSON only:

{{
  "contextual_flag": true or false,
  "flags_triggered": [
    "signal: evidence from posting"
  ],
  "follow_up_question": "one specific verification question",
  "advice": "1-2 sentences based only on the available evidence"
}}

Posting and extracted evidence:

\"\"\"{text}\"\"\"
"""

    try:
        resp = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.2,
        )

        raw = resp.choices[0].message.content.strip()

        raw = re.sub(
            r'^```json\s*|\s*```$',
            '',
            raw
        )

        return json.loads(raw)

    except json.JSONDecodeError:
        return {
            "contextual_flag": False,
            "flags_triggered": ["Could not parse contextual analysis."],
            "follow_up_question": "",
            "advice": "The contextual analysis could not be parsed."
        }

    except Exception as e:
        return {
            "contextual_flag": False,
            "flags_triggered": ["Contextual analysis unavailable."],
            "follow_up_question": "Can you verify the opportunity directly through the organization's official website?",
            "advice": "Contextual AI analysis was unavailable, so verify the opportunity independently before proceeding."
        }

def fuse_verdict(a_flag, b_flag, c_flag):
    flags = sum([
        a_flag,
        b_flag,
        c_flag
    ])

    if (a_flag and c_flag) or flags >= 2:
        return "High Risk"

    elif flags == 1:
        return "Caution"

    return "Likely Safe"

def analyze_input(input_type, content, url=None):
    text_parts = []

    if content:
        text_parts.append(content)

    if url:
        if "docs.google.com/forms" in url:
            url_result = scrape_google_form(url)

            if url_result.get("all_questions"):
                text_parts.append(
                    "Google Form fields: "
                    + str(url_result["all_questions"])
                )

            if url_result.get("matched_fields"):
                text_parts.append(
                    "Google Form evidence: "
                    + str(url_result["matched_fields"])
                )

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

    if not text_parts:
        return {
            "error": "Please provide posting text or an application URL."
        }

    text_for_llm = "\n\n".join(text_parts)

    a_result = check_structural_pattern(text_for_llm)

    text_technical = check_technical_signals(text_for_llm)

    b_flag = text_technical["flag"]

    if url_technical:
        b_flag = b_flag or url_technical.get("flag", False)

    b_result = {
        "flag": b_flag,
        "text_signal": text_technical,
        "url_signal": url_technical
    }

    c_result = call_groq_contextual(
        text_for_llm,
        a_result,
        b_result
    )

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