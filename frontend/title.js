import { createBlurSprite, createBorder, createText } from './ui_helpers.js';
import { LOADING_TEXT_STYLE } from './constants.js';

export class TitleScreen {
    constructor(app, mainContainer) {
        this.app = app;
        this.mainContainer = mainContainer;
        this.titleContainer = null;
    }

    render(gameState) {
        // Define title text style with larger font
        const titleStyle = {
            ...LOADING_TEXT_STYLE,
            fontSize: 48,
            align: 'center'
        };

        // Create the title text first to get its dimensions
        const titleText = createText(
            gameState.main_text || '',
            titleStyle,
            0,
            0,
            0.5  // Center anchor
        );

        // Calculate container dimensions based on text size
        const padding = 20;
        const width = Math.max(400, titleText.width + padding * 2 + 20);
        const height = titleText.height + padding * 2;

        // Create a container for the title elements
        this.titleContainer = new PIXI.Container();
        this.titleContainer.visible = true;

        // Create background blur and border
        const blurSprite = createBlurSprite(width, height, 0, 0);
        const border = createBorder(0, 0, width, height, 10);

        // Position the title text in the center of the container
        titleText.x = width / 2;
        titleText.y = height / 2;

        // Add elements to container
        this.titleContainer.addChild(blurSprite, border, titleText);

        // Center the container on screen
        this.titleContainer.x = (this.app.screen.width - width) / 2;
        this.titleContainer.y = (this.app.screen.height - height) / 3;  // Position slightly above center

        this.mainContainer.addChild(this.titleContainer);
    }

    hide() {
        if (this.titleContainer) {
            this.mainContainer.removeChild(this.titleContainer);
            this.titleContainer = null;
        }
    }
} 