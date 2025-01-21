import { Renderer } from './renderer.js';
import { Communicator } from './communicator.js';

class Game {
    constructor() {
        this.gameState = null;
        this.renderer = new Renderer(this);
        this.communicator = new Communicator(this);
    }

    init() {
        this.communicator.init();
    }

    handleMenuOption(option) {
        this.renderer.setLoading(true);
        this.communicator.sendMenuOption(option);
    }

    handleTextInput(text) {
        this.renderer.setLoading(true);
        this.communicator.sendTextInput(text);
    }

    handleInput(input) {
        this.renderer.setLoading(true);
        if (this.gameState.input_type === 'menu') {
            this.communicator.sendMenuOption(input);
        } else {
            this.communicator.sendTextInput(input);
        }
    }

    updateGameState(newState) {
        this.gameState = newState;
        this.renderer.setLoading(false);
        this.renderer.updateDisplay();
    }
}

// Ensure the DOM is fully loaded before initializing the game
function initGame() {
    const game = new Game();
    game.init();
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initGame);
} else {
    initGame();
}