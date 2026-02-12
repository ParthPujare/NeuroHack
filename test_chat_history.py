import requests
import time
import json

BASE_URL = "http://localhost:8000"

def test_chat_flow():
    print("Testing Chat Flow...")
    
    # 1. Check Health
    try:
        res = requests.get(f"{BASE_URL}/health")
        print(f"Health Check: {res.status_code}")
    except Exception as e:
        print(f"Server not running? {e}")
        return

    # 2. Get User
    res = requests.get(f"{BASE_URL}/user")
    user_id = res.json()['user_id']
    print(f"User ID: {user_id}")

    # 3. Create Conversation
    res = requests.post(f"{BASE_URL}/conversations", json={"user_id": user_id, "title": "Test Chat"})
    conv = res.json()
    conv_id = conv['id']
    print(f"Created Conversation: {conv_id} - {conv['title']}")

    # 4. Send Message
    print("Sending message...")
    chat_req = {
        "message": "Hello, how are you?",
        "user_id": user_id,
        "conversation_id": conv_id
    }
    res = requests.post(f"{BASE_URL}/chat", json=chat_req)
    print(f"Chat Response: {res.status_code}")
    print(res.json().get('response', 'No response'))

    # 5. Check Messages Persistence
    print("Checking persistence...")
    res = requests.get(f"{BASE_URL}/conversations/{conv_id}/messages")
    messages = res.json()
    print(f"Messages count: {len(messages)}")
    for m in messages:
        print(f" - {m['role']}: {m['content'][:30]}...")

    # 6. Check Conversations List
    res = requests.get(f"{BASE_URL}/conversations/{user_id}")
    convs = res.json()
    print(f"User Conversations: {len(convs)}")
    
    # 7. Cleanup
    requests.delete(f"{BASE_URL}/conversations/{conv_id}")
    print("Cleanup done.")

if __name__ == "__main__":
    test_chat_flow()
