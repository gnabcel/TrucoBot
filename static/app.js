let gameState = null;
let lastLogLength = 0;
let lastPhase = null;

async function startGame(targetScore = 30) {
    try {
        await fetch('/api/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ target_score: targetScore })
        });
        document.getElementById('start-menu-overlay').classList.add('hidden');
        document.getElementById('game-over-overlay').classList.add('hidden');
        document.getElementById('game-over-overlay').classList.remove('boo-effect');
        lastLogLength = 0;
        lastPhase = null;
        pollState();
    } catch (e) {
        console.error("Failed to start", e);
    }
}

async function pollState() {
    try {
        const response = await fetch('/api/state');
        if (response.ok) {
            gameState = await response.json();
            render();

            // If it's not my turn and game is playing, poll again quickly
            if (gameState.phase === 'playing' && !gameState.is_turn) {
                setTimeout(pollState, 1000);
            }
        }
    } catch (e) {
        console.error("Failed to fetch state", e);
    }
}

async function sendAction(actionStr) {
    try {
        const res = await fetch('/api/action', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: actionStr })
        });

        if (res.ok) {
            pollState();
        } else {
            const err = await res.json();
            alert("Error: " + err.error);
        }
    } catch (e) {
        console.error("Action error", e);
    }
}

// ----------------------------------------------------
// Rendering
// ----------------------------------------------------

function render() {
    if (!gameState) return;

    // Check Game Over
    if (gameState.phase === 'game_over') {
        renderGameOver();
        return;
    }

    // Clear speech bubbles if phase changes to dealing
    if (gameState.phase === 'dealing' && lastPhase !== 'dealing') {
        clearSpeechBubbles();
    }

    // Handle new log messages (Speech bubbles)
    if (gameState.log.length > lastLogLength) {
        const newLogs = gameState.log.slice(lastLogLength);
        newLogs.forEach(msg => {
            if (msg.includes('Vos:') && (msg.includes('¡') || msg.includes('No quiero') || msg.includes('mazo'))) {
                showSpeechBubble('my', msg.split('Vos:')[1].trim());
            } else if (msg.includes('TrucoBot:') && (msg.includes('¡') || msg.includes('No quiero') || msg.includes('mazo'))) {
                showSpeechBubble('opp', msg.split('TrucoBot:')[1].trim());
            }
        });
        lastLogLength = gameState.log.length;
    }

    // Handle Folding Animations and Round Summary
    if (lastPhase === 'playing' && gameState.phase === 'round_end') {
        clearSpeechBubbles(); // Clear them immediately at end of hand
        setTimeout(() => showRoundSummary(), 1000);

        const recentLog = gameState.log[gameState.log.length - 1] || '';
        const prevLog = gameState.log[gameState.log.length - 2] || '';
        if (recentLog.includes('no quiso') || prevLog.includes('Me voy al mazo') || prevLog.includes('Te la dejo') || prevLog.includes('me chicho') || prevLog.includes('me achico')) {
            if (recentLog.includes('Vos ganás') || recentLog.includes('Vos ganas')) {
                document.getElementById('opp-hand').classList.add('fold-animation-opp');
            } else if (recentLog.includes('TrucoBot gana')) {
                document.getElementById('my-hand').classList.add('fold-animation');
            }
        }
    }

    // Reset animations
    if (gameState.phase === 'dealing') {
        document.getElementById('opp-hand').classList.remove('fold-animation-opp');
        document.getElementById('my-hand').classList.remove('fold-animation');
    }

    lastPhase = gameState.phase;

    // Scores and Info
    document.getElementById('my-score').textContent = gameState.my_score;
    document.getElementById('opp-score').textContent = gameState.opp_score;
    document.getElementById('round-indicator').textContent = `Hand ${gameState.hand_number + 1}`;

    // Status Message
    const statusEl = document.getElementById('status-message');
    if (gameState.phase === 'dealing') {
        statusEl.textContent = "Dealing cards...";
    } else if (gameState.phase === 'round_end') {
        const p1w = gameState.round_winners.filter(x => x === 1).length;
        const p2w = gameState.round_winners.filter(x => x === 2).length;
        statusEl.textContent = `Round Ended! You won ${p1w} tricks, Bot won ${p2w}.`;

        // The round summary popup handles advancing.
    } else if (gameState.is_turn) {
        if (gameState.waiting_for_response === 'envido') {
            statusEl.textContent = `Opponent called Envido. What do you do? (You have ${gameState.my_envido} pts)`;
        } else if (gameState.waiting_for_response === 'truco') {
            statusEl.textContent = `Opponent called Truco. What do you do?`;
        } else {
            statusEl.textContent = "Your turn to play!";
        }
    } else {
        if (gameState.waiting_for_response) {
            statusEl.textContent = "Waiting for Opponent to respond...";
        } else {
            statusEl.textContent = "Opponent is thinking...";
        }
    }

    // Buttons
    renderButtons();

    // Cards
    renderCards();

    // Log
    renderLog();
}

function showSpeechBubble(player, text) {
    const bubble = document.getElementById(`${player}-speech`);
    if (!bubble) return;
    bubble.textContent = text;

    bubble.classList.remove('active');
    void bubble.offsetWidth; // trigger reflow
    bubble.classList.add('active');
}

function clearSpeechBubbles() {
    document.getElementById('my-speech').classList.remove('active');
    document.getElementById('opp-speech').classList.remove('active');
}

function renderLog() {
    const logContainer = document.getElementById('log-messages');

    // If it's the exact same number of logs, don't re-render completely to avoid scroll jump
    // We'll just do a simple innerHTML for now and auto-scroll
    let html = '';

    // Reverse or forward? Forward is better with auto-scroll down
    gameState.log.forEach(msg => {
        let cls = 'log-entry';
        if (msg.includes('ganá') || msg.includes('gana')) cls += ' important';
        if (msg.includes('TrucoBot')) cls += ' opp-msg'; // Optional

        html += `<div class="${cls}">${msg}</div>`;
    });

    logContainer.innerHTML = html;
    logContainer.scrollTop = logContainer.scrollHeight;
}

function renderButtons() {
    const btnContainer = document.getElementById('action-buttons');
    btnContainer.innerHTML = '';

    if (gameState.phase !== 'playing' || !gameState.is_turn) return;

    const actions = gameState.valid_actions;

    const labels = {
        'call_envido': 'Envido',
        'call_real_envido': 'Real Envido',
        'call_falta_envido': 'Falta Envido',
        'envido_quiero': 'Quiero',
        'envido_no_quiero': 'No Quiero',
        'call_truco': 'Truco!',
        'call_retruco': 'Retruco!',
        'call_vale_4': 'Vale Cuatro!',
        'truco_quiero': 'Quiero',
        'truco_no_quiero': 'Me voy al mazo',
    };

    actions.forEach(act => {
        if (act.startsWith('play_')) return; // handled by clicking cards

        const btn = document.createElement('button');
        btn.textContent = labels[act] || act;

        if (act.includes('no_quiero')) {
            btn.className = 'danger-btn';
        } else if (act.includes('quiero') && !act.includes('no_')) {
            btn.className = 'primary-btn';
        } else {
            btn.className = 'secondary-btn';
        }

        btn.onclick = () => sendAction(act);
        btnContainer.appendChild(btn);
    });
}

function renderCards() {
    const oppHand = document.getElementById('opp-hand');
    const myHand = document.getElementById('my-hand');
    const myPlayed = document.getElementById('my-played');
    const oppPlayed = document.getElementById('opp-played');

    // Clear
    oppHand.innerHTML = ''; myHand.innerHTML = '';
    myPlayed.innerHTML = ''; oppPlayed.innerHTML = '';

    // Opponent Hand (Face down)
    // To know how many cards opponent has, we assume 3 minus what they played
    const oppCardsCount = 3 - gameState.opp_played.length;
    for (let i = 0; i < oppCardsCount; i++) {
        oppHand.appendChild(createCard(null, false));
    }

    // My Hand
    gameState.my_cards.forEach((cardObj) => {
        const canPlay = gameState.is_turn && gameState.valid_actions.includes(`play_card_${cardObj.id}`);
        const el = createCard(cardObj.str, true, canPlay);
        if (canPlay) {
            el.onclick = () => sendAction(`play_card_${cardObj.id}`);
        }
        myHand.appendChild(el);
    });

    // Played Cards
    // In our simplified view, we just show all cards played this round
    // A better UI would stack them by trick.
    gameState.opp_played.forEach(cstr => {
        oppPlayed.appendChild(createCard(cstr, true));
    });

    gameState.my_played.forEach(cstr => {
        myPlayed.appendChild(createCard(cstr, true));
    });
}

function createCard(cardStr, faceUp, isPlayable = false) {
    const div = document.createElement('div');
    div.className = 'card';
    if (!faceUp) {
        div.classList.add('hidden-card');
        return div;
    }

    if (isPlayable) div.classList.add('playable');

    // Parse "1 de Espada"
    const parts = cardStr.split(' de ');
    const rank = parts[0];
    const suit = parts[1];

    div.setAttribute('data-suit', suit);

    div.innerHTML = `
        <div class="rank">${rank}</div>
        <div class="suit">${suit}</div>
        <div class="rank bottom">${rank}</div>
    `;
    return div;
}

function renderGameOver() {
    const overlay = document.getElementById('game-over-overlay');

    // Only trigger effects once
    if (overlay.classList.contains('hidden')) {
        overlay.classList.remove('hidden');

        const title = document.getElementById('game-over-title');
        const sub = document.getElementById('final-score');

        sub.textContent = `${gameState.my_score} - ${gameState.opp_score}`;

        if (gameState.my_score >= gameState.target_score || gameState.my_score > gameState.opp_score) {
            title.textContent = "¡Ganaste!";
            title.style.color = "var(--success)";

            // Fireworks!
            if (typeof confetti === 'function') {
                const duration = 3000;
                const end = Date.now() + duration;

                (function frame() {
                    confetti({
                        particleCount: 5,
                        angle: 60,
                        spread: 55,
                        origin: { x: 0 },
                        colors: ['#2ea043', '#2f81f7']
                    });
                    confetti({
                        particleCount: 5,
                        angle: 120,
                        spread: 55,
                        origin: { x: 1 },
                        colors: ['#2ea043', '#2f81f7']
                    });

                    if (Date.now() < end) {
                        requestAnimationFrame(frame);
                    }
                }());
            }
        } else {
            title.textContent = "¡Te ganaron!";
            title.style.color = "var(--danger)";

            // Boo effect (shake and red screen)
            overlay.classList.add('boo-effect');
        }
    }
}

function showRoundSummary() {
    // We construct the summary from the recent logs
    const txt = document.getElementById('round-summary-text');

    // Find logs that say "ganá" "gana" or "Sumás" since the last dealing
    let summaryText = "";
    for (let i = gameState.log.length - 1; i >= 0; i--) {
        const msg = gameState.log[i];
        if (msg.includes('--- Arranca')) break;
        if (msg.includes('ganá') || msg.includes('gana') || msg.includes('Sumás') || msg.includes('Suma')) {
            summaryText += `<p>${msg}</p>`;
        }
    }

    if (!summaryText) summaryText = "<p>Ronda completada.</p>";

    txt.innerHTML = summaryText;
    document.getElementById('round-summary-overlay').classList.remove('hidden');

    // Auto close after 2 seconds
    setTimeout(() => {
        closeRoundSummary();
    }, 2000);
}

function closeRoundSummary() {
    const overlay = document.getElementById('round-summary-overlay');
    if (!overlay.classList.contains('hidden')) {
        overlay.classList.add('hidden');
        // Tell server to advance to next round via a simple request (even an ignored action triggers state progression)
        sendAction('call_envido');
    }
}
