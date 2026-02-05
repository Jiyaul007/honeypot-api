from fastapi import FastAPI, Header, HTTPException
import requests, re, os
from dotenv import load_dotenv

load_dotenv()

HF_API_KEY = os.getenv("HF_API_KEY")
API_KEY = os.getenv("API_KEY")

app = FastAPI()

conversations = {}

def is_scam(text):
    keywords = ["lottery", "prize", "kyc", "urgent", "blocked", "verify", "account", "winner"]
    return any(word in text.lower() for word in keywords)

def extract_info(text):
    bank = re.findall(r"\d{9,18}", text)
    upi = re.findall(r"\w+@\w+", text)
    links = re.findall(r"https?://\S+", text)
    return bank, upi, links

def ai_reply(history):
    prompt = f"""
You are a normal Indian user.
You are confused and polite.
Slowly ask for payment or bank details.
Never reveal that you suspect scam.

Conversation:
{history}

Reply:
"""
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    data = {"inputs": prompt}

    try:
        res = requests.post(
            "https://api-inference.huggingface.co/models/google/flan-t5-large",
            headers=headers,
            json=data,
            timeout=20
        )

        result = res.json()

        if isinstance(result, list) and len(result) > 0:
            if "generated_text" in result[0]:
                return result[0]["generated_text"]

        if isinstance(result, dict):
            if "generated_text" in result:
                return result["generated_text"]

        return "Please share your bank or UPI details for verification."

    except:
        return "Please share your bank or UPI details for verification."

@app.post("/honeypot")
def honeypot(data: dict, x_api_key: str = Header(None)):

    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

    cid = data.get("conversation_id")
    msg = data.get("message")

    if not cid or not msg:
        raise HTTPException(status_code=400, detail="conversation_id and message required")

    if cid not in conversations:
        conversations[cid] = []

    conversations[cid].append(f"Scammer: {msg}")

    scam = is_scam(msg)
    reply = ""

    if scam:
        reply = ai_reply("\n".join(conversations[cid]))
        conversations[cid].append(f"Agent: {reply}")

    bank, upi, links = extract_info("\n".join(conversations[cid]))

    return {
        "scam_detected": scam,
        "agent_activated": scam,
        "reply": reply,
        "extracted_intelligence": {
            "bank_accounts": bank,
            "upi_ids": upi,
            "phishing_links": links
        }
    }
