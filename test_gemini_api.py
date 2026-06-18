import requests
import json

API_KEY = "AIzaSyDgOaf22rgP5jhXR-yUTGmOwZjJrhyrxXs"
LIST_MODELS_URL = f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}"

def list_models():
    print("--- Listing Available Gemini Models ---")
    try:
        response = requests.get(LIST_MODELS_URL, timeout=30)
        
        if response.status_code == 200:
            print("✅ Success! API Key is working. Available models:")
            data = response.json()
            if 'models' in data:
                for model in data['models']:
                    if 'flash' in model['name'].lower():
                        print(f"- {model['name']} ({model.get('displayName', 'No display name')})")
            else:
                print("No 'models' key in response:", data)
        else:
            print(f"❌ Failed: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    list_models()
