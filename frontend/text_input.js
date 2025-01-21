import { createButtonContainer, applyDefaultStyleToButton, applyHoverStyleToButton, applyPressedStyleToButton } from './ui_helpers.js';

export class TextInput {
    constructor(app, menuContainer, game) {
        this.app = app;
        this.menuContainer = menuContainer;
        this.game = game;
        this.container = null;
        this.textInput = null;
        this.resizeHandler = null;
    }

    render() {
        if (this.container) {
            this.destroy();
        }

        this.container = new PIXI.Container();
        
        // Create HTML input element
        this.textInput = document.createElement('input');
        this.textInput.type = 'text';
        this.textInput.style.position = 'absolute';
        this.textInput.style.width = '600px';
        this.textInput.style.height = '80px';
        this.textInput.style.fontSize = '16px';
        this.textInput.style.padding = '5px';
        this.textInput.style.backgroundColor = 'rgba(0, 0, 0, 0.5)';
        this.textInput.style.color = 'white';
        this.textInput.style.border = '2px solid white';
        this.textInput.style.borderRadius = '10px';
        this.textInput.style.zIndex = '10';
        document.body.appendChild(this.textInput);

        // Create update position handler
        this.resizeHandler = () => {
            const rect = this.app.view.getBoundingClientRect();
            this.textInput.style.left = `${rect.left + (rect.width / 2) - 300}px`;
            this.textInput.style.top = `${rect.top + rect.height - 200}px`;
        };

        // Add event listeners
        window.addEventListener('resize', this.resizeHandler);
        window.addEventListener('scroll', this.resizeHandler);
        this.resizeHandler(); // Initial position

        // Create send button
        const sendButton = createButtonContainer('Send');
        sendButton.x = this.app.screen.width / 2;
        sendButton.y = 80;

        sendButton.interactive = true;
        sendButton.buttonMode = true;
        
        let isPressed = false;
        
        sendButton.on('pointerdown', () => {
            isPressed = true;
            applyPressedStyleToButton(sendButton);
        });

        sendButton.on('pointerup', () => {
            if (isPressed) {
                this.submit();
                isPressed = false;
            }
        });

        sendButton.on('pointerupoutside', () => {
            if (isPressed) {
                applyDefaultStyleToButton(sendButton);
                isPressed = false;
            }
        });

        sendButton.on('pointerover', () => {
            if (!isPressed) {
                applyHoverStyleToButton(sendButton);
            }
        });

        sendButton.on('pointerout', () => {
            if (!isPressed) {
                applyDefaultStyleToButton(sendButton);
            }
        });

        this.container.addChild(sendButton);
        this.container.position.set(0, this.app.screen.height - 150);

        // Add enter key handler
        this.textInput.addEventListener('keyup', (event) => {
            if (event.key === 'Enter') {
                this.submit();
            }
        });

        this.menuContainer.addChild(this.container);
    }

    submit() {
        this.game.handleInput(this.textInput.value);
        this.textInput.value = '';
    }

    destroy() {
        if (this.textInput) {
            this.textInput.remove();
            this.textInput = null;
        }
        if (this.resizeHandler) {
            window.removeEventListener('resize', this.resizeHandler);
            window.removeEventListener('scroll', this.resizeHandler);
            this.resizeHandler = null;
        }
        if (this.container) {
            this.menuContainer.removeChild(this.container);
            this.container = null;
        }
    }
}
