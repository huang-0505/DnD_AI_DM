// main.js - DnD Combat Frontend
const BASE_API_URL = 'http://localhost:9000';

// Create axios instance
const api = axios.create({
    baseURL: BASE_API_URL
});

// Data service for API calls
const DataService = {
    StartCombat: async function () {
        const response = await api.post('/combat/start', {});
        return response.data;
    },
    GetState: async function (sessionId) {
        const response = await api.get(`/combat/state/${sessionId}`);
        return response.data;
    },
    SendAction: async function (sessionId, action) {
        const response = await api.post(`/combat/action/${sessionId}`, { action });
        return response.data;
    },
    EndCombat: async function (sessionId) {
        const response = await api.delete(`/combat/session/${sessionId}`);
        return response.data;
    }
};

// Combat App
class CombatApp {
    constructor() {
        this.sessionId = null;
        this.currentState = null;
        this.isPlayerTurn = false;

        // DOM elements
        this.startBtn = document.getElementById('startCombatBtn');
        this.endBtn = document.getElementById('endCombatBtn');
        this.actionPanel = document.getElementById('actionPanel');
        this.actionInput = document.getElementById('actionInput');
        this.submitBtn = document.getElementById('submitActionBtn');
        this.dialogueScroll = document.getElementById('dialogueScroll');
        this.playersContainer = document.getElementById('playersContainer');
        this.enemiesContainer = document.getElementById('enemiesContainer');
        this.currentTurnDisplay = document.getElementById('currentTurn');
        this.roundDisplay = document.getElementById('roundNumber');

        this.setupEventListeners();
    }

    setupEventListeners() {
        this.startBtn.addEventListener('click', () => this.startCombat());
        this.endBtn.addEventListener('click', () => this.endCombat());
        this.submitBtn.addEventListener('click', () => this.submitAction());

        this.actionInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !this.submitBtn.disabled) {
                this.submitAction();
            }
        });

        this.actionInput.addEventListener('input', () => {
            this.submitBtn.disabled = !this.actionInput.value.trim();
        });
    }

    async startCombat() {
        try {
            this.startBtn.disabled = true;
            this.startBtn.textContent = 'Starting...';

            const response = await DataService.StartCombat();
            this.sessionId = response.session_id;
            this.currentState = response.state;

            // Clear welcome message
            this.dialogueScroll.innerHTML = '';

            // Add initial message
            this.addNarrative(response.message);

            // Show action panel and end button
            this.actionPanel.style.display = 'block';
            this.endBtn.style.display = 'block';

            // Update UI
            this.updateUI();

            // Check if it's player turn
            this.checkTurn();

        } catch (error) {
            console.error('Error starting combat:', error);
            alert('Failed to start combat. Make sure the backend is running.');
            this.startBtn.disabled = false;
            this.startBtn.textContent = 'Start Combat';
        }
    }

    async submitAction() {
        const action = this.actionInput.value.trim();
        if (!action) return;

        try {
            // Disable input
            this.actionInput.disabled = true;
            this.submitBtn.disabled = true;

            // Send action
            const response = await DataService.SendAction(this.sessionId, action);

            // Update state
            this.currentState = response.state;

            // Add narrative to dialogue
            this.addNarrative(response.narrative);

            // Clear input
            this.actionInput.value = '';

            // Update UI
            this.updateUI();

            // Check if battle is over
            if (response.state.battle_over) {
                this.handleBattleEnd(response.state.winner);
                return;
            }

            // Check next turn
            this.checkTurn();

        } catch (error) {
            console.error('Error submitting action:', error);
            alert('Failed to submit action.');
            this.actionInput.disabled = false;
            this.submitBtn.disabled = false;
        }
    }

    checkTurn() {
        if (!this.currentState) return;

        const currentActor = this.currentState.current_actor;
        if (!currentActor) return;

        // Find the actor in players or enemies
        const isPlayer = this.currentState.players.some(p => p.name === currentActor && p.alive);
        const isEnemy = this.currentState.enemies.some(e => e.name === currentActor && e.alive);

        if (isPlayer) {
            this.isPlayerTurn = true;
            this.currentTurnDisplay.textContent = `${currentActor}'s Turn - Choose your action!`;
            this.currentTurnDisplay.style.color = '#2d5016';
            this.actionInput.disabled = false;
            this.actionInput.focus();
        } else if (isEnemy) {
            this.isPlayerTurn = false;
            this.currentTurnDisplay.textContent = `${currentActor}'s Turn - Enemy is deciding...`;
            this.currentTurnDisplay.style.color = '#8b0000';
            this.actionInput.disabled = true;
            this.submitBtn.disabled = true;

            // Automatically trigger enemy turn
            setTimeout(() => this.triggerEnemyTurn(), 1500);
        }
    }

    async triggerEnemyTurn() {
        try {
            const response = await DataService.SendAction(this.sessionId, 'enemy_turn');

            // Update state
            this.currentState = response.state;

            // Add narrative
            this.addNarrative(response.narrative);

            // Update UI
            this.updateUI();

            // Check if battle is over
            if (response.state.battle_over) {
                this.handleBattleEnd(response.state.winner);
                return;
            }

            // Check next turn
            this.checkTurn();

        } catch (error) {
            console.error('Error in enemy turn:', error);
        }
    }

    updateUI() {
        if (!this.currentState) return;

        // Update round
        this.roundDisplay.textContent = this.currentState.round;

        // Update players
        this.renderCharacters(this.currentState.players, this.playersContainer);

        // Update enemies
        this.renderCharacters(this.currentState.enemies, this.enemiesContainer);
    }

    renderCharacters(characters, container) {
        container.innerHTML = '';

        characters.forEach(char => {
            const card = document.createElement('div');
            card.className = 'character-card';

            if (char.name === this.currentState.current_actor && char.alive) {
                card.classList.add('active');
            }

            if (!char.alive) {
                card.classList.add('defeated');
            }

            const hpPercent = (char.hp / char.max_hp) * 100;

            card.innerHTML = `
                <div class="character-name">${char.name}</div>
                <div class="character-stats">
                    AC: ${char.ac} | ATK: +${char.attack_bonus} | DMG: ${char.damage}
                </div>
                <div class="hp-bar-container">
                    <div class="hp-bar" style="width: ${hpPercent}%">
                        ${char.hp}/${char.max_hp} HP
                    </div>
                </div>
            `;

            container.appendChild(card);
        });
    }

    addNarrative(text) {
        const entry = document.createElement('div');
        entry.className = 'narrative-entry';
        entry.innerHTML = `<div class="narrative-text">${text}</div>`;
        this.dialogueScroll.appendChild(entry);

        // Scroll to bottom
        this.dialogueScroll.scrollTop = this.dialogueScroll.scrollHeight;
    }

    handleBattleEnd(winner) {
        this.actionInput.disabled = true;
        this.submitBtn.disabled = true;

        const resultDiv = document.createElement('div');
        resultDiv.className = 'battle-result';

        if (winner === 'players') {
            resultDiv.innerHTML = `
                <h2>🎉 Victory! 🎉</h2>
                <p>The heroes have triumphed over their foes!</p>
            `;
        } else {
            resultDiv.innerHTML = `
                <h2>💀 Defeat 💀</h2>
                <p>The enemies have prevailed...</p>
            `;
        }

        this.dialogueScroll.appendChild(resultDiv);
        this.dialogueScroll.scrollTop = this.dialogueScroll.scrollHeight;
    }

    async endCombat() {
        if (!this.sessionId) return;

        try {
            await DataService.EndCombat(this.sessionId);
            location.reload();
        } catch (error) {
            console.error('Error ending combat:', error);
            location.reload();
        }
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.combatApp = new CombatApp();
});
