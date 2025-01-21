class Communicator {
    constructor(game) {
        this.game = game;
        this.socket = null;
    }

    init() {
        this.initWebSocket();
    }

    initWebSocket() {
        this.socket = new WebSocket(`ws://${window.location.host}/ws`);
        this.socket.onmessage = this.handleMessage.bind(this);
        this.socket.onopen = () => {
            console.log('WebSocket connection established');
            this.getGameState();
        };
    }

    handleMessage(event) {
        const data = JSON.parse(event.data);
        this.game.updateGameState(data);
    }

    getGameState() {
        this.sendMessage({ action: 'get_game_state' });
    }

    sendMenuOption(option) {
        this.sendMessage({ action: 'menu_option', option: option });
    }

    sendTextInput(text) {
        this.sendMessage({ action: 'text_input', text: text });
    }

    sendMessage(message) {
        if (this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify(message));
        } else {
            console.error('WebSocket is not open. ReadyState:', this.socket.readyState);
        }
    }
}

export { Communicator };