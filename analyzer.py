import requests
import json
import re
from pdf_extractor import extract_raw_text, get_base64_pdf, extract_links, trim_to_token_budget

# NOTE: PDF text extraction is now handled by pdf_extractor.py
# which uses lightweight pypdf for Groq text, and base64 encoding for Gemini native PDF ingestion.

def analyze_atr(pdf_path, api_key="", provider="gemini", model_name="gemini-flash-latest"):
    """
    Main function to analyze a single ATR PDF using Gemini or Groq API.
    Returns error if API fails.
    """
    
    # 1. Prepare Inputs
    text_content = extract_raw_text(pdf_path)
    links = extract_links(pdf_path)
    
    if not text_content:
        return {"status": "error", "error": "No text extracted from PDF"}

    text_content = trim_to_token_budget(text_content, max_chars=30000)
    
    base64_pdf = None
    if provider == "gemini":
        base64_pdf = get_base64_pdf(pdf_path)
        if not base64_pdf:
            return {"status": "error", "error": "PDF read failed"}

    # 2. Try Analysis
    try:
        if not api_key:
            raise ValueError("API Key is missing")

        prompt = f"""
        You are a Government Grievance Analyst. The document below is a CPGRAMS ATR (Action Taken Report).
        Use its contents to locate the relevant information precisely.

        INSTRUCTIONS FOR SUCCESS STORY FORMATTING:
        If the case is a SUCCESS (relief provided, action taken), you MUST format the story as follows:

        1. 'success_headline':
           - Short, factual, news-style headline.
           - Reflects the grievance type and concrete outcome.
           - No emotional/promotional language.
           - Example: "CPGRAMS Intervention Restores Delayed Family Pension to Widow in Assam"

        2. 'success_narrative':
           - A SINGLE consolidated narrative paragraph.
           - Must cover: Grievance background -> Failure of regular channels -> CPGRAMS intervention -> Concrete outcome.
           - Tone: Factual, concise, administrative.
           - No bullet points. Subtly highlight CPGRAMS as the turning point.

        FIELD EXTRACTION RULES:
        - 'grievance_id'     -> Registration number (e.g. DOAAC/E/2024/...) from the document header.
        - 'grievance_type'   -> Classify the document intent as "Grievance", "Suggestion", or "Request".
        - 'has_attachment'   -> true if the document explicitly mentions attached documents or annexures, false otherwise.
        - 'citizen_problem'  -> From the Grievance Description section.
        - 'resolution_summary' -> From the last desk's Action Taken or Remarks section.
        - 'is_success_story' -> true if fully resolved with tangible action, false otherwise.
        - 'success_headline' -> As per formatting instructions (or null).
        - 'success_narrative'-> As per formatting instructions (or null).
        - 'status'           -> Always 'analyzed'.
        - 'desk_count'       -> Count distinct desks/offices the grievance passed through.
        - 'ping_pong_count'  -> Count how many times a grievance returned to an already-visited desk.
        - 'ping_pong_desks'  -> List the specific desks involved in ping-pong transfers.
        - 'bottleneck_desk'  -> Office that held the grievance the longest without action.
        - 'final_resolver'   -> Officer name from the last Officer Details entry (if stated).
        - 'resolved_desk'    -> Office/desk name that finally resolved it.
        - 'citizen_feedback' -> Verbatim or near-verbatim feedback from the citizen, if present.
        - 'intelligent_issue_summary'  -> Concise, intelligent paraphrase of the citizen's grievance.
        - 'intelligent_officer_summary'-> Intelligent summary of ONLY the final officer's remarks/action.
        - 'intelligent_citizen_feedback_summary' -> Concise summary of citizen feedback (or null).

        EXTRA INSIGHTS FIELDS:
        - 'citizen_sentiment' -> Initial emotion of citizen (e.g., Distressed, Angry, Neutral, Assertive)
        - 'officer_tone' -> Tone of the resolving officer (e.g., Empathetic, Bureaucratic, Dismissive, Helpful)
        - 'citizen_feedback_sentiment' -> Emotion at closure (e.g., Satisfied, Frustrated, Escalating, None)
        - 'delay_root_cause' -> Probable reason for delay/bottleneck (e.g., Missing documents, Jurisdictional dispute, Officer inaction)
        - 'jurisdiction_accuracy' -> Did the citizen initially route it correctly or was delay caused by bad routing?
        - 'standardized_theme' -> Broad category (e.g., Pension Arrears, Financial Fraud, Workplace Harassment, Infrastructure)
        - 'urgency_score' -> Integer 1 to 5 indicating severity/risk (5 = critical emergency/destitution)
        - 'is_systemic_issue' -> Boolean true if this grievance represents a repeated wider policy flaw rather than an isolated error.
        - 'policy_recommendation' -> One-sentence recommendation to fix root cause so this type of grievance doesn't repeat.

        OUTPUT FORMAT:
        Return ONLY valid JSON.
        {{
            "grievance_id": "...",
            "grievance_type": "Grievance",
            "has_attachment": true,
            "citizen_problem": "...",
            "resolution_summary": "...",
            "is_success_story": true,
            "success_headline": "...",
            "success_narrative": "...",
            "status": "analyzed",
            "language": "english",
            "desk_count": 0,
            "ping_pong_count": 0,
            "ping_pong_desks": ["Desk A", "Desk B"],
            "bottleneck_desk": "...",
            "final_resolver": "...",
            "resolved_desk": "...",
            "citizen_feedback": "...",
            "intelligent_issue_summary": "...",
            "intelligent_officer_summary": "...",
            "intelligent_citizen_feedback_summary": "...",
            "citizen_sentiment": "...",
            "officer_tone": "...",
            "citizen_feedback_sentiment": "...",
            "delay_root_cause": "...",
            "jurisdiction_accuracy": "...",
            "standardized_theme": "...",
            "urgency_score": 1,
            "is_systemic_issue": false,
            "policy_recommendation": "..."
        }}
        """
        
        if provider == "groq":
            prompt_with_text = prompt + f"\n\nDOCUMENT:\n{text_content}"
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            payload = {
                "model": model_name,
                "messages": [{"role": "user", "content": prompt_with_text}],
                "response_format": {"type": "json_object"},
                "temperature": 0.1
            }
        else:
            model = model_name
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [{"parts": [
                    {"text": prompt},
                    {"inline_data": {"mime_type": "application/pdf", "data": base64_pdf}}
                ]}],
                "generationConfig": {"response_mime_type": "application/json"}
            }
        
        import time
        max_retries = 5
        for attempt in range(max_retries):
            response = requests.post(url, json=payload, headers=headers, timeout=120)
            if response.status_code in [503, 429]:
                if attempt < max_retries - 1:
                    time.sleep(4 ** attempt)
                    continue
            break
            
        if response.status_code != 200:
            print(f"API Error {response.status_code}: {response.text}")
            return {"status": "error", "error": f"API Error {response.status_code}"}
        else:
            data = response.json()
            try:
                if provider == "groq":
                    content = data['choices'][0]['message']['content']
                else:
                    content = data['candidates'][0]['content']['parts'][0]['text']
                    
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    content = json_match.group(0)
                
                result = json.loads(content)
            except (KeyError, IndexError, json.JSONDecodeError) as e:
                print(f"Parsing Error: {e}")
                return {"status": "error", "error": "JSON Parsing Failed"}

    except Exception as e:
        print(f"LLM Failed/Timed Out ({e})")
        return {"status": "error", "error": f"Exception: {str(e)}"}

    # Final Polish
    result['attachment_links'] = links
    
    # Ensure keys exist
    defaults = {
        'grievance_id': None, 'grievance_type': 'Unknown', 'has_attachment': False, 'citizen_problem': 'Unknown', 'resolution_summary': 'Unknown', 
        'is_success_story': False, 'desk_count': 0, 'status': 'analyzed', 
        'final_resolver': 'Unknown', 'bottleneck_desk': 'None',
        'resolved_desk': 'Unknown', 'citizen_feedback': 'None', 'ping_pong_desks': [],
        'success_headline': None, 'success_narrative': None,
        'intelligent_issue_summary': None, 'intelligent_officer_summary': None, 'intelligent_citizen_feedback_summary': None
    }
    for k, v in defaults.items():
        if k not in result: result[k] = v
        
    # Final cleanup if ID missing
    if not result.get('grievance_id'):
        gid_match = re.search(r"([A-Z]{3,5}/[A-Z]/\d{4}/\d{5,})", text_content)
        if gid_match:
            result['grievance_id'] = gid_match.group(1)
            
    return result

def analyze_vigilance(pdf_path, api_key="", provider="gemini", model_name="gemini-flash-latest"):
    """
    Analyzes a single ATR PDF to determine if a vigilance angle is present.
    """
    
    text_content = extract_raw_text(pdf_path)

    if not text_content:
        return {"status": "error", "error": "No text extracted from PDF"}

    text_content = trim_to_token_budget(text_content, max_chars=30000)

    base64_pdf = None
    if provider == "gemini":
        base64_pdf = get_base64_pdf(pdf_path)
        if not base64_pdf:
            return {"status": "error", "error": "PDF read failed"}

    try:
        if not api_key:
            raise ValueError("API Key is missing")

        prompt = f"""
        You are a Government Grievance Analyst. Based on Central Vigilance Commission (CVC) guidelines,
        examine the document to determine if a "vigilance angle" is involved.

        CVC Guidelines for Vigilance Angle:
        A vigilance angle is perceptible if a public servant:
        1. Demanded and/or accepted gratification other than legal remuneration.
        2. Obtained a valuable thing without consideration or with inadequate consideration from a person
           with whom they have or are likely to have official dealings.
        3. Obtained for themselves or any other person any valuable thing or pecuniary advantage by
           corrupt or illegal means or by abusing their position.
        4. Possesses assets disproportionate to their known sources of income.
        5. Is involved in cases of misappropriation, forgery, or cheating or other similar criminal offences.

        Assess whether a vigilance angle is involved ONLY based on the document provided.
        Return a perfectly formatted JSON with exactly three fields:
        - "grievance_id": The registration number from the document header (e.g. DOAAC/E/...), else null.
        - "is_vigilance": "Yes" if a vigilance angle is clearly present per CVC guidelines, else "No".
        - "vigilance_reasoning": Brief explanation citing which guideline applies (or why none do).

        OUTPUT FORMAT:
        Return ONLY valid JSON.
        {{
            "grievance_id": "...",
            "is_vigilance": "Yes",
            "vigilance_reasoning": "..."
        }}
        """
        
        if provider == "groq":
            prompt_with_text = prompt + f"\n\nDOCUMENT:\n{text_content}"
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            payload = {
                "model": model_name,
                "messages": [{"role": "user", "content": prompt_with_text}],
                "response_format": {"type": "json_object"},
                "temperature": 0.1
            }
        else:
            model = model_name
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [{"parts": [
                    {"text": prompt},
                    {"inline_data": {"mime_type": "application/pdf", "data": base64_pdf}}
                ]}],
                "generationConfig": {"response_mime_type": "application/json"}
            }
        
        import time
        max_retries = 5
        for attempt in range(max_retries):
            response = requests.post(url, json=payload, headers=headers, timeout=120)
            if response.status_code in [503, 429]:
                if attempt < max_retries - 1:
                    time.sleep(4 ** attempt)
                    continue
            break
            
        if response.status_code != 200:
            return {"status": "error", "error": f"API Error {response.status_code}"}
        else:
            data = response.json()
            try:
                if provider == "groq":
                    content = data['choices'][0]['message']['content']
                else:
                    content = data['candidates'][0]['content']['parts'][0]['text']
                    
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    content = json_match.group(0)
                
                result = json.loads(content)
            except (KeyError, IndexError, json.JSONDecodeError) as e:
                return {"status": "error", "error": "JSON Parsing Failed"}

    except Exception as e:
        return {"status": "error", "error": f"Exception: {str(e)}"}

    defaults = {
        'grievance_id': None, 'is_vigilance': 'No', 'vigilance_reasoning': 'Analysis failed or no reason provided.'
    }
    for k, v in defaults.items():
        if k not in result: result[k] = v
        
    if not result.get('grievance_id'):
        gid_match = re.search(r"([A-Z]{3,5}/[A-Z]/\d{4}/\d{5,})", text_content)
        if gid_match:
            result['grievance_id'] = gid_match.group(1)
            
    return result

def analyze_darpg_routing(pdf_path, api_key="", provider="gemini", model_name="gemini-flash-latest"):
    """
    Analyzes a single ATR PDF to resolve grievance pendency for DARPG, determine routing
    (Dispose vs Transfer), draft ATR remarks, and detect ping-pongs and negligence.
    """
    text_content = extract_raw_text(pdf_path)

    if not text_content:
        return {"status": "error", "error": "No text extracted from PDF"}

    text_content = trim_to_token_budget(text_content, max_chars=30000)

    base64_pdf = None
    if provider == "gemini":
        base64_pdf = get_base64_pdf(pdf_path)
        if not base64_pdf:
            return {"status": "error", "error": "PDF read failed"}

    try:
        if not api_key:
            raise ValueError("API Key is missing")

        prompt = f"""
        You are a highly skilled Government Grievance Analyst for DARPG (Department of Administrative Reforms and Public Grievances). 

        You must comply with the Comprehensive Guidelines for Grievance Redressal (DARPG, 2024). Specifically:
        1. Grievances must be resolved objectively, fairly, and with a citizen-centric approach.
        2. Superficial, evasive, or repetitive replies are unacceptable.
        3. If a grievance pertains to a subordinate organization, the nodal Ministry must ensure adequate resolution rather than repeatedly returning it.
        4. Cases of ping-ponging require clear jurisdictional justification.

        INSTRUCTIONS:
        1. Complainant Name: Extract the complainant's name from the document header.
        2. Routing Logic (routing_action & transfer_to_dept):
           - Is this a DARPG Case? If the grievance fundamentally targets DARPG's own internal operations/staff, set 'routing_action' to "Dispose" and 'transfer_to_dept' to null. Draft ATR remarks stating this is a DARPG matter retained for internal review.
           - Is this a Non-DARPG Case? If the grievance belongs to another Ministry/Department/State/UT, set 'routing_action' to "Transfer" and identify the precise 'transfer_to_dept'. 
           - Negligence Exception: If it is a Non-DARPG case but exhibits UNACCEPTABLE levels of negligence by the line ministry (e.g., repeatedly closing without any actual action despite obvious facts), set 'negligence_flag' to true, and 'routing_action' to "Dispose" so DARPG can intervene manually.
        3. Ping-Pong Threshold Logic (is_ping_pong_flag):
           - Examine the transfer/routing history in the ATR.
           - Threshold >= 3: If the grievance has bounced between Department A and Department B 3 or more times (e.g. A->B, B->A, A->B), set 'is_ping_pong_flag' to true. The drafted ATR remark must sternly flag this ping-pong for human intervention.
           - Threshold 1 or 2: If it is the 2nd or 3rd time routing to a department, 'is_ping_pong_flag' is false. However, the drafted ATR remark MUST include a polite, formal notice such as: "This is the [Nth] time this grievance is being routed to your Ministry/Department. We kindly request a specialized view of this matter to ensure accurate jurisdictional resolution."
        4. Draft ATR Remarks: Write a professional, citizen-centric, and objective Draft ATR Reply based on the above logic. Ensure it is rooted in the specificity of the Action Taken Report.
        5. General Metrics: Extract desk_count, ping_pong_count, delay_root_cause, standardized_theme, and urgency_score as you normally would.

        OUTPUT FORMAT:
        Return ONLY valid JSON.
        {{
            "grievance_id": "DOAAC/E/...",
            "complainant_name": "...",
            "routing_action": "Dispose" or "Transfer",
            "transfer_to_dept": "...",
            "draft_atr_remarks": "...",
            "is_ping_pong_flag": false,
            "negligence_flag": false,
            "desk_count": 0,
            "ping_pong_count": 0,
            "delay_root_cause": "...",
            "standardized_theme": "...",
            "urgency_score": 1
        }}
        """
        
        if provider == "groq":
            prompt_with_text = prompt + f"\n\nDOCUMENT:\n{text_content}"
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            payload = {
                "model": model_name,
                "messages": [{"role": "user", "content": prompt_with_text}],
                "response_format": {"type": "json_object"},
                "temperature": 0.1
            }
        else:
            model = model_name
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [{"parts": [
                    {"text": prompt},
                    {"inline_data": {"mime_type": "application/pdf", "data": base64_pdf}}
                ]}],
                "generationConfig": {"response_mime_type": "application/json"}
            }
        
        import time
        max_retries = 5
        for attempt in range(max_retries):
            response = requests.post(url, json=payload, headers=headers, timeout=120)
            if response.status_code in [503, 429]:
                if attempt < max_retries - 1:
                    time.sleep(4 ** attempt)
                    continue
            break
            
        if response.status_code != 200:
            return {"status": "error", "error": f"API Error {response.status_code}"}
        else:
            data = response.json()
            try:
                if provider == "groq":
                    content = data['choices'][0]['message']['content']
                else:
                    content = data['candidates'][0]['content']['parts'][0]['text']
                    
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    content = json_match.group(0)
                
                result = json.loads(content)
            except (KeyError, IndexError, json.JSONDecodeError) as e:
                return {"status": "error", "error": "JSON Parsing Failed"}

    except Exception as e:
        return {"status": "error", "error": f"Exception: {str(e)}"}

    defaults = {
        'grievance_id': None, 'complainant_name': 'Unknown', 'routing_action': 'Transfer',
        'transfer_to_dept': 'Unknown', 'draft_atr_remarks': 'No remarks generated.',
        'is_ping_pong_flag': False, 'negligence_flag': False,
        'desk_count': 0, 'ping_pong_count': 0, 'delay_root_cause': 'Unknown',
        'standardized_theme': 'Unknown', 'urgency_score': 1
    }
    for k, v in defaults.items():
        if k not in result: result[k] = v
        
    if not result.get('grievance_id'):
        gid_match = re.search(r"([A-Z]{3,5}/[A-Z]/\d{4}/\d{5,})", text_content)
        if gid_match:
            result['grievance_id'] = gid_match.group(1)
            
    return result
