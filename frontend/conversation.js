import { LAYOUT, TEXT_STYLE, SUB_TEXT_STYLE, STYLE } from './constants.js';
import { 
    createBlurSprite, 
    createBorder, 
    createText,
    createPortrait 
} from './ui_helpers.js';

export class ConversationRenderer {
    constructor(app, mainContainer) {
        this.app = app;
        this.mainContainer = mainContainer;
        this.defaultPlayerText = '';
        this.createConversationElements();
    }

    createConversationElements() {
        const padding = LAYOUT.PADDING;
        const portraitSize = LAYOUT.PORTRAIT_SIZE;
        const boxHeight = LAYOUT.PORTRAIT_SIZE + padding * 2;
        const firstBoxY = padding * 5;
        
        this.mainTextBlur = createBlurSprite(
            this.app.screen.width - (padding * 8),
            60,
            padding * 4,
            padding
        );
        
        this.mainTextBorder = createBorder(
            padding * 4,
            padding,
            this.app.screen.width - (padding * 8),
            60
        );
        
        this.mainText = createText('', TEXT_STYLE,
            padding * 5,
            padding * 1.5
        );
        
        this.npcBlur = createBlurSprite(
            this.app.screen.width - (padding * 8),
            boxHeight,
            padding * 4,
            firstBoxY
        );
        
        this.npcBorder = createBorder(
            padding * 4,
            firstBoxY,
            this.app.screen.width - (padding * 8),
            boxHeight
        );
        
        this.npcText = createText('', SUB_TEXT_STYLE, 
            padding * 6 + portraitSize,
            firstBoxY + padding
        );

        this.playerBlur = createBlurSprite(
            this.app.screen.width - (padding * 8),
            boxHeight,
            padding * 4,
            firstBoxY + boxHeight + padding
        );
        
        this.playerBorder = createBorder(
            padding * 4,
            firstBoxY + boxHeight + padding,
            this.app.screen.width - (padding * 8),
            boxHeight
        );
        
        this.playerText = createText('', SUB_TEXT_STYLE,
            padding * 5,
            firstBoxY + boxHeight + padding + padding
        );
        
        this.setVisibility(false);
    }

    render(gameState) {
        this.setVisibility(true);

        this.mainText.text = gameState.main_text || '';

        this.npcText.text = gameState.npc_text || '';
        this.defaultPlayerText = gameState.player_text || '';
        this.playerText.text = this.defaultPlayerText;

        const textWrapWidth = this.app.screen.width - (LAYOUT.PADDING * 12) - LAYOUT.PORTRAIT_SIZE;
        this.npcText.style.wordWrapWidth = textWrapWidth;
        this.playerText.style.wordWrapWidth = textWrapWidth;
        
        this.addBaseElements();

        this.updatePortrait('npc', gameState.npc_portrait_url);
        this.updatePortrait('player', gameState.player_portrait_url);
    }

    updatePortrait(type, portraitUrl) {
        if (!portraitUrl) return;

        const padding = LAYOUT.PADDING;
        const portraitSize = LAYOUT.PORTRAIT_SIZE;
        const mainTextHeight = 60;
        const firstBoxY = padding * 3 + mainTextHeight;
        const yPos = type === 'npc' ? firstBoxY : firstBoxY + LAYOUT.PORTRAIT_SIZE + padding * 3;
        
        const xPos = type === 'npc' ? 
            padding * 5 : 
            this.app.screen.width - (padding * 5) - portraitSize;

        if (this[`${type}Portrait`]) {
            this.mainContainer.removeChild(this[`${type}Portrait`]);
        }

        this[`${type}Portrait`] = createPortrait(
            portraitUrl,
            xPos,
            yPos,
            portraitSize
        );
        
        if (type === 'player') {
            this[`${type}Portrait`].scale.x = -1;
            this[`${type}Portrait`].x += portraitSize;
        }
        
        this.mainContainer.addChild(this[`${type}Portrait`]);
    }

    addBaseElements() {
        const elements = [
            this.mainTextBlur,
            this.mainTextBorder,
            this.mainText,
            this.npcBlur,
            this.npcBorder,
            this.npcText,
            this.playerBlur,
            this.playerBorder,
            this.playerText
        ];

        elements.forEach(element => {
            if (!this.mainContainer.children.includes(element)) {
                this.mainContainer.addChild(element);
            }
        });
    }

    setVisibility(visible) {
        const elements = [
            this.mainTextBlur,
            this.mainTextBorder,
            this.mainText,
            this.npcBlur,
            this.npcBorder,
            this.npcText,
            this.playerBlur,
            this.playerBorder,
            this.playerText
        ];

        elements.forEach(element => {
            if (element) element.visible = visible;
        });

        if (this.npcPortrait) {
            this.npcPortrait.visible = visible;
        }
        if (this.playerPortrait) {
            this.playerPortrait.visible = visible;
        }

        if (!visible) {
            this.resetPlayerText();
            this.mainText.text = '';
            this.npcText.text = '';
        }
    }

    destroy() {
        const elements = [
            this.mainTextBlur,
            this.mainTextBorder,
            this.mainText,
            this.npcBlur,
            this.npcBorder,
            this.npcText,
            this.playerBlur,
            this.playerBorder,
            this.playerText,
            this.npcPortrait,
            this.playerPortrait
        ];

        elements.forEach(element => {
            if (element) {
                this.mainContainer.removeChild(element);
                element.destroy();
            }
        });
    }

    showOptionDetail(detail) {
        if (detail) {
            this.playerText.text = detail;
        }
    }

    resetPlayerText() {
        this.playerText.text = this.defaultPlayerText;
    }
} 