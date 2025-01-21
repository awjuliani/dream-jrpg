import { LOADING_TEXT_STYLE } from './constants.js';
import { createBlurSprite, createBorder, createText } from './ui_helpers.js';

export class LoadingScreen {
    constructor(app) {
        this.app = app;
        this.loadingContainer = null;
        this.loadingBackground = null;
        this.loadingText = null;
        this.ellipsisText = null;
        this.ellipsisAnimation = 0;
        this.ellipsisSpeed = 0.03;
        this.isVisible = false;
        
        // Create a container for game content that will be blurred
        this.gameContentContainer = new PIXI.Container();
        
        // Move all existing children to the new container
        while (this.app.stage.children.length > 0) {
            this.gameContentContainer.addChild(this.app.stage.removeChildAt(0));
        }
        
        // Add the game content container to the stage
        this.app.stage.addChild(this.gameContentContainer);
        
        this.createLoadingElements();
    }

    createLoadingElements() {
        // Create container first but don't add to stage yet
        this.loadingContainer = new PIXI.Container();
        this.loadingContainer.visible = false;

        // Create and add background first (so it's behind)
        this.loadingBackground = createBlurSprite(
            this.app.screen.width,
            this.app.screen.height,
            0,
            0
        );
        this.loadingBackground.alpha = 0.5;
        this.loadingBackground.visible = false;
        this.app.stage.addChild(this.loadingBackground);

        // Now add the loading container to stage (so it's in front)
        this.app.stage.addChild(this.loadingContainer);

        // Calculate dimensions for loading box
        const padding = Math.min(20, this.app.screen.width * 0.02);
        const width = Math.min(220, this.app.screen.width * 0.3) + padding * 2;
        const height = Math.min(50, this.app.screen.height * 0.1) + padding * 2;
        const borderRadius = Math.min(10, Math.min(width, height) * 0.1);

        // Create background blur and border
        const blurSprite = createBlurSprite(width, height, 0, 0);
        this.loadingContainer.addChild(blurSprite);

        const border = createBorder(0, 0, width, height, borderRadius);
        this.loadingContainer.addChild(border);

        // Create the loading text
        this.loadingText = createText('Dreaming', LOADING_TEXT_STYLE, width / 2, height / 2, 0.5);
        this.loadingContainer.addChild(this.loadingText);

        // Create a separate text for the ellipsis
        this.ellipsisText = createText('', LOADING_TEXT_STYLE, this.loadingText.x + this.loadingText.width / 2 + 2, height / 2 - 15, 0);
        this.loadingContainer.addChild(this.ellipsisText);

        // Center the loading container on screen
        this.loadingContainer.x = (this.app.screen.width - width) / 2;
        this.loadingContainer.y = (this.app.screen.height - height) / 2;
    }

    show() {
        if (this.isVisible) return;
        
        this.isVisible = true;
        this.loadingContainer.visible = true;
        this.loadingBackground.visible = true;
        
        // Apply blur filter to the game content container only
        const blurFilter = new PIXI.filters.BlurFilter(5);
        this.gameContentContainer.filters = [blurFilter];
        
        // Make the loading background semi-transparent black
        this.loadingBackground.tint = 0x000000;
        this.loadingBackground.alpha = 0.5;
        
        // Disable interactivity on stage
        this.app.stage.interactiveChildren = false;
        
        // Disable text input if it exists
        const textInput = document.querySelector('input[type="text"]');
        if (textInput) {
            textInput.disabled = true;
            textInput.style.backgroundColor = 'rgba(0, 0, 0, 0.7)';
            textInput.style.color = 'rgba(255, 255, 255, 0.2)';
            textInput.style.borderColor = 'rgba(255, 255, 255, 0.1)';
        }

        // Start animation
        this.app.ticker.add(this.animateEllipsis, this);
    }

    hide() {
        if (!this.isVisible) return;
        
        this.isVisible = false;
        this.loadingContainer.visible = false;
        this.loadingBackground.visible = false;
        
        // Remove blur filter from game content container
        this.gameContentContainer.filters = null;
        
        // Re-enable interactivity on stage
        this.app.stage.interactiveChildren = true;
        
        // Re-enable text input if it exists
        const textInput = document.querySelector('input[type="text"]');
        if (textInput) {
            textInput.disabled = false;
            textInput.style.backgroundColor = 'rgba(0, 0, 0, 0.5)';
            textInput.style.color = 'white';
            textInput.style.borderColor = 'white';
        }

        // Stop animation
        this.app.ticker.remove(this.animateEllipsis, this);
    }

    animateEllipsis = () => {
        this.ellipsisAnimation += this.ellipsisSpeed;
        if (this.ellipsisAnimation > 4) {
            this.ellipsisAnimation = 0;
        }
        
        const dots = '.'.repeat(Math.floor(this.ellipsisAnimation));
        this.ellipsisText.text = dots;
    }

    destroy() {
        this.app.ticker.remove(this.animateEllipsis, this);
        if (this.loadingContainer) {
            this.loadingContainer.destroy({ children: true });
        }
        if (this.loadingBackground) {
            this.loadingBackground.destroy();
        }
    }
}
