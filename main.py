@app.post("/honeypot")
def honeypot(data: dict = None, x_api_key: str = Header(None)):

    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

    # If no body sent (tester case)
    if data is None:
        return {
            "scam_detected": False,
            "agent_activated": False,
            "reply": "Honeypot API is alive",
            "extracted_intelligence": {
                "bank_accounts": [],
                "upi_ids": [],
                "phishing_links": []
            }
        }

    cid = data.get("conversation_id")
    msg = data.get("message")

    if not cid or not msg:
        return {
            "scam_detected": False,
            "agent_activated": False,
            "reply": "Invalid input format",
            "extracted_intelligence": {
                "bank_accounts": [],
                "upi_ids": [],
                "phishing_links": []
            }
        }

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
