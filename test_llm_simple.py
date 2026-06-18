import requests
import json

def test_llm_simple():
    print("--- Testing LLM Stability (Short Input) ---")
    
    url = "http://localhost:1234/v1/chat/completions"
    
    # 1. Very simple text
    prompt = "Extract the name: 'My name is John Doe.'"
    
    payload = {
        "model": "deepseek-r1-0528-qwen3-8b", # It might auto-detect, but let's try
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "stream": False
    }
    
    try:
        print("Sending request...")
        resp = requests.post(url, json=payload, timeout=30)
        
        if resp.status_code == 200:
            print("✅ Success!")
            print(resp.json()['choices'][0]['message']['content'])
        else:
            print(f"❌ Failed: {resp.status_code}")
            print(resp.text)
            
    except Exception as e:
        print(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    test_llm_simple()
