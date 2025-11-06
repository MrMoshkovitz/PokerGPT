// LLMPoker Assistant - Browser Client

let ws = null;
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5;
const RECONNECT_DELAY = 2000;

// Initialize WebSocket connection
function connectWebSocket() {
    const wsUrl = `ws://${window.location.host}/ws`;
    console.log(`Connecting to ${wsUrl}...`);

    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        console.log('WebSocket connected');
        reconnectAttempts = 0;
        updateConnectionStatus(true);

        // Send heartbeat
        setInterval(() => {
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send('ping');
            }
        }, 30000);
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleMessage(data);
    };

    ws.onclose = () => {
        console.log('WebSocket disconnected');
        updateConnectionStatus(false);

        // Attempt reconnect
        if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
            reconnectAttempts++;
            setTimeout(connectWebSocket, RECONNECT_DELAY);
        }
    };

    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
    };
}

// Handle incoming messages
function handleMessage(data) {
    console.log('Received:', data.type);

    switch (data.type) {
        case 'game_state_update':
            updateGameState(data.state, data.vision_confidence);
            break;

        case 'recommendation':
            displayRecommendation(data);
            break;

        case 'system_alert':
            showAlert(data.message, data.level);
            break;

        default:
            console.warn('Unknown message type:', data.type);
    }
}

// Update game state display
function updateGameState(state, visionConfidence) {
    // Hole cards
    document.getElementById('hole-cards').textContent =
        state.hole_cards && state.hole_cards.length > 0
            ? state.hole_cards.join(' ')
            : '--';

    // Board
    document.getElementById('board').textContent =
        state.board && state.board.length > 0
            ? state.board.join(' ')
            : 'Preflop';

    // Pot
    document.getElementById('pot').textContent = `$${state.pot?.toFixed(2) || '0.00'}`;

    // Stack
    document.getElementById('stack').textContent = `$${state.your_stack?.toFixed(2) || '0.00'}`;

    // Position
    document.getElementById('position').textContent = state.position || '--';

    // Vision confidence
    const confidencePercent = (visionConfidence * 100).toFixed(0);
    document.getElementById('vision-confidence').value = confidencePercent;
    document.getElementById('vision-confidence-text').textContent = `${confidencePercent}%`;

    // Color-code confidence
    const confEl = document.getElementById('vision-confidence');
    confEl.className = visionConfidence > 0.8 ? 'high-conf' :
                       visionConfidence > 0.6 ? 'med-conf' : 'low-conf';
}

// Display recommendation
function displayRecommendation(rec) {
    const actionEl = document.getElementById('action');
    actionEl.textContent = rec.action || 'No action';

    // Color-code by confidence
    const confidence = rec.confidence || 0;
    actionEl.className = confidence > 0.8 ? 'action-high-conf' :
                         confidence > 0.6 ? 'action-med-conf' : 'action-low-conf';

    // Confidence meter
    const confidencePercent = (confidence * 100).toFixed(0);
    document.getElementById('confidence').value = confidencePercent;
    document.getElementById('confidence-text').textContent = `${confidencePercent}% confident`;

    // Reasoning
    document.getElementById('reasoning-text').textContent =
        rec.reasoning || 'No reasoning provided';

    // Provider info
    document.getElementById('provider-info').textContent =
        `LLM Provider: ${rec.llm_provider || 'unknown'}`;

    // Alternatives
    const altDiv = document.getElementById('alternatives');
    if (rec.alternatives && rec.alternatives.length > 0) {
        altDiv.innerHTML = '<h3>Alternatives:</h3>' +
            rec.alternatives.map(alt =>
                `<div class="alternative">
                    ${alt.action} (${(alt.confidence * 100).toFixed(0)}%)
                </div>`
            ).join('');
        altDiv.style.display = 'block';
    } else {
        altDiv.style.display = 'none';
    }
}

// Show system alert
function showAlert(message, level = 'info') {
    const messagesDiv = document.getElementById('messages');

    const alert = document.createElement('div');
    alert.className = `alert alert-${level}`;
    alert.textContent = message;

    messagesDiv.appendChild(alert);

    // Auto-remove after 5 seconds
    setTimeout(() => {
        alert.remove();
    }, 5000);
}

// Update connection status indicator
function updateConnectionStatus(connected) {
    const statusEl = document.getElementById('connection-status');

    if (connected) {
        statusEl.textContent = '● Connected';
        statusEl.className = 'status-connected';
    } else {
        statusEl.textContent = '● Disconnected';
        statusEl.className = 'status-disconnected';
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('LLMPoker Assistant initialized');
    connectWebSocket();
});
