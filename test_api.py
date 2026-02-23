import urllib.request
import json
import time

def get_state():
    req = urllib.request.Request("http://127.0.0.1:5000/api/state")
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode())

def post_action(action):
    data = json.dumps({"action": action}).encode('utf-8')
    req = urllib.request.Request("http://127.0.0.1:5000/api/action", data=data, headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req)
        return True
    except urllib.error.HTTPError as e:
        print(f"Failed action {action}: {e.read().decode('utf-8')}")
        return False

# Start
urllib.request.urlopen(urllib.request.Request("http://127.0.0.1:5000/api/start", data=b'{"target_score": 15}', headers={"Content-Type": "application/json"}))
print("Game started")
time.sleep(0.5)

state = get_state()
if "call_truco" in state["valid_actions"]:
    print("Can call Truco. Calling it...")
    post_action("call_truco")

    # Bot responds
    time.sleep(1)
    # The API might be waiting for the bot to poll and respond
    # in this simple framework, the bot is triggered on /api/state poll.
    state = get_state()
    time.sleep(1)
    state = get_state() # Poll twice to ensure bot has played
    print("State after bot response:", state["truco_state"])
    print("Truco turn is player:", state["truco_turn"])
    print("Valid actions:", state["valid_actions"])
    
    if "call_retruco" in state["valid_actions"]:
        print("Success! Player can call Retruco.")
        post_action("call_retruco")
        time.sleep(1)
        state = get_state()
        time.sleep(1)
        state = get_state()
        print("State after retruco bot response:", state["truco_state"])
    elif state["waiting_for_response"] == "truco":
        print("Bot called Retruco! We must accept.")
        post_action("truco_quiero")
        time.sleep(1)
        state = get_state()
        time.sleep(1)
        state = get_state()
        if "call_vale_4" in state["valid_actions"]:
            print("Success! Player can call Vale 4 after accepting Retruco.")
else:
    print("Could not call Truco.")
