from flask import Flask, jsonify, request, send_from_directory
import os
from game import TrucoGame, GamePhase
from player import APIPlayer, HeuristicBot

app = Flask(__name__, static_folder='static')

# Global game instance
game = None

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

@app.route('/api/start', methods=['POST'])
def start_game():
    global game
    p1 = APIPlayer("Player")
    p2 = HeuristicBot("Bot")
    game = TrucoGame(p1, p2)
    return jsonify({"status": "started"})

@app.route('/api/state', methods=['GET'])
def get_state():
    global game
    if not game:
        return jsonify({"error": "No game active"}), 400
        
    state = game.get_state_for_player(game.p1)
    
    # Check if we need bot to play
    if game.phase == GamePhase.PLAYING and game.current_turn == game.p2:
        # Bot's turn
        bot_state = game.get_state_for_player(game.p2)
        action = game.p2.get_action(bot_state)
        
        if action:
            success, msg = game.handle_action(game.p2, action)
            if success:
                # Refresh state after bot plays
                state = game.get_state_for_player(game.p1)
                state['last_bot_action'] = action
    
    return jsonify(state)

@app.route('/api/action', methods=['POST'])
def handle_action():
    global game
    if not game:
        return jsonify({"error": "No game active"}), 400
        
    data = request.json
    action = data.get('action')
    
    if not action:
        return jsonify({"error": "No action provided"}), 400
        
    success, msg = game.handle_action(game.p1, action)
    
    if not success:
        return jsonify({"error": msg}), 400
        
    return jsonify({"status": "success", "message": msg})

if __name__ == '__main__':
    # Ensure static folder exists
    if not os.path.exists('static'):
        os.makedirs('static')
    app.run(debug=True, port=5000)
