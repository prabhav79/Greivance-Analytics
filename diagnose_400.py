import requests
import json

def test_payloads():
    base_url = "http://localhost:1234/v1/chat/completions"
    model = "deepseek/deepseek-r1-0528-qwen3-8b"
    
    print(f"Testing against {base_url} with model {model}\n")

    # Test 1: Minimal + Stream False
    print("Test 1: Minimal + Stream: False")
    p1 = {
        "model": model,
        "messages": [{"role": "user", "content": "Hi"}],
        "stream": False
    }
    r1 = requests.post(base_url, json=p1)
    print(f"Status: {r1.status_code}")
    print(f"Response: {r1.text[:100]}")

    # Test 2: Minimal + Stream False + Temp
    print("\nTest 2: Minimal + Stream: False + Temp")
    p2 = {
        "model": model,
        "messages": [{"role": "user", "content": "Hi"}],
        "stream": False,
        "temperature": 0.1
    }
    r2 = requests.post(base_url, json=p2)
    print(f"Status: {r2.status_code}")

    # Test 3: Large Content (Fake)
    print("\nTest 3: Large Content (2000 chars)")
    large_text = "A" * 2000
    p3 = {
        "model": model,
        "messages": [{"role": "user", "content": large_text}],
        "stream": False
    }
    r3 = requests.post(base_url, json=p3)
    print(f"Status: {r3.status_code}")

if __name__ == "__main__":
    test_payloads()
