import requests

def test_connection():
    url = "http://localhost:1234/v1/models"
    print(f"Testing connection to LM Studio at {url}...")
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            model_id = data['data'][0]['id']
            print("\n✅ SUCCESS! Connected to LM Studio.")
            print(f"   Loaded Model: {model_id}")
            print("\nYou are ready to run the dashboard!")
        else:
            print(f"\n❌ Connection established, but received error: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("\n❌ FAILED to connect.")
        print("   Make sure LM Studio is running and the 'Local Server' is STARTED.")
        print("   1. Open LM Studio")
        print("   2. Click the double-arrow icon (<->) or 'Local Server' on the left")
        print("   3. Click the green 'Start Server' button")
        print("   4. Ensure the port is 1234")

if __name__ == "__main__":
    test_connection()
