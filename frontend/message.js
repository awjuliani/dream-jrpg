import { createBlurSprite, createBorder, createText, createPortrait } from './ui_helpers.js';
import { TEXT_STYLE, SUB_TEXT_STYLE, MINI_TEXT_STYLE, LAYOUT, DIALOGUE_TEXT_STYLE } from './constants.js';

export class MessageRenderer {
    constructor(app, menuContainer) {
        this.app = app;
        this.menuContainer = menuContainer;
    }

    // Create a common overlay setup method
    createBaseOverlay(width, height, x, y) {
        const overlay = new PIXI.Container();
        overlay.x = x;
        overlay.y = y;
        overlay.interactive = false;
        overlay.buttonMode = false;

        const blurSprite = createBlurSprite(width, height, 0, 0);
        const border = createBorder(0, 0, width, height, 20);
        border.beginFill(0x000000, 0.5);
        border.endFill();

        overlay.addChild(blurSprite, border);
        return overlay;
    }

    // Helper method for text creation with word wrap
    createWrappedText(content, style, x, y, wrapWidth) {
        const text = createText(content || '', style, x, y);
        text.style.wordWrap = true;
        text.style.wordWrapWidth = wrapWidth;
        return text;
    }

    // Add this new helper method
    measureTextHeight(content, style, wrapWidth) {
        if (!content) return 0;
        const tempText = this.createWrappedText(content, style, 0, 0, wrapWidth);
        return tempText.height;
    }

    renderMessageOverlayWithDimensions(gameState, width, height, isSmall) {
        const LAYOUT = {
            PADDING: 20,
            TEXT_MARGIN: 30,
            PORTRAIT_SIZE: 150,
            PORTRAIT_OFFSET: 20
        };

        // Calculate heights of all elements first
        let totalHeight = LAYOUT.PADDING * 2;
        
        // Use the new helper method for main text
        const mainTextHeight = this.measureTextHeight(
            gameState.main_text,
            isSmall ? MINI_TEXT_STYLE : TEXT_STYLE,
            width - (LAYOUT.PADDING * 2)
        );
        if (mainTextHeight > 0) {
            totalHeight += mainTextHeight + LAYOUT.PADDING * 2;
        }

        // Use the helper method for subtext
        const subTextWidth = gameState.portrait_image_url 
            ? width - LAYOUT.PORTRAIT_SIZE - (LAYOUT.PADDING * 3)
            : width - (LAYOUT.PADDING * 2);
            
        const subTextHeight = !isSmall ? this.measureTextHeight(
            gameState.sub_text,
            SUB_TEXT_STYLE,
            subTextWidth
        ) : 0;

        // Calculate final content height
        if (gameState.portrait_image_url) {
            totalHeight += Math.max(LAYOUT.PORTRAIT_SIZE, subTextHeight);
        } else if (subTextHeight > 0) {
            totalHeight += subTextHeight + LAYOUT.PADDING;
        }

        // Create overlay with correct size
        const finalHeight = Math.max(height, totalHeight);
        const overlayX = (this.app.screen.width - width) / 2;
        const overlayY = (this.app.screen.height - finalHeight) / 2;
        const overlay = this.createBaseOverlay(width, finalHeight, overlayX, overlayY);

        // Now add all elements with correct positioning
        let currentY = LAYOUT.PADDING;

        if (gameState.main_text) {
            const mainText = this.createWrappedText(
                gameState.main_text,
                isSmall ? MINI_TEXT_STYLE : TEXT_STYLE,
                LAYOUT.TEXT_MARGIN,
                currentY,
                width - (LAYOUT.PADDING * 2)
            );
            overlay.addChild(mainText);
            currentY += mainTextHeight + LAYOUT.PADDING;
        }

        if (gameState.portrait_image_url) {
            const portrait = createPortrait(
                gameState.portrait_image_url,
                LAYOUT.TEXT_MARGIN,
                currentY,
                LAYOUT.PORTRAIT_SIZE
            );
            overlay.addChild(portrait);

            if (!isSmall && gameState.sub_text) {
                const subTextStyle = gameState.input_type === 'dialogue' ? DIALOGUE_TEXT_STYLE : SUB_TEXT_STYLE;
                
                const subText = this.createWrappedText(
                    gameState.sub_text,
                    subTextStyle,
                    LAYOUT.PORTRAIT_SIZE + (LAYOUT.PADDING * 3),
                    currentY,
                    width - LAYOUT.PORTRAIT_SIZE - (LAYOUT.PADDING * 4)
                );
                overlay.addChild(subText);
            }
        } else if (!isSmall && gameState.sub_text) {
            const subTextStyle = gameState.input_type === 'dialogue' ? DIALOGUE_TEXT_STYLE : SUB_TEXT_STYLE;
            
            const subText = this.createWrappedText(
                gameState.sub_text,
                subTextStyle,
                LAYOUT.TEXT_MARGIN,
                currentY,
                width - (LAYOUT.PADDING * 4)
            );
            overlay.addChild(subText);
        }

        this.menuContainer.addChild(overlay);
        this.menuContainer.interactive = false;
        this.menuContainer.buttonMode = false;

        return { overlay };
    }

    renderStatsMessage(gameState) {
        const width = this.app.screen.width - 400;
        const height = this.app.screen.height - 200;
        const overlayX = (this.app.screen.width - width) / 2;
        const overlayY = (this.app.screen.height - height) / 2;

        const overlay = this.createBaseOverlay(width, height, overlayX, overlayY);
        const { character_info: char } = gameState;

        // Add header and portrait
        overlay.addChild(
            this.createWrappedText(char.name, TEXT_STYLE, 40, 20, width - 60)
        );

        const portraitContainer = createPortrait(char.portrait, 40, 90, LAYOUT.PORTRAIT_SIZE);
        overlay.addChild(portraitContainer);

        // Info container setup
        const infoContainer = new PIXI.Container();
        infoContainer.x = LAYOUT.PORTRAIT_SIZE + 80;
        infoContainer.y = 80;

        infoContainer.addChild(
            this.createWrappedText(
                `Level ${char.level} ${char.job_class}`,
                SUB_TEXT_STYLE,
                0,
                0,
                width - LAYOUT.PORTRAIT_SIZE - 120
            ),
            this.createWrappedText(
                char.description,
                SUB_TEXT_STYLE,
                0,
                40,
                width - LAYOUT.PORTRAIT_SIZE - 120
            )
        );

        // Stats container setup
        const statsContainer = this.createStatsContainer(char, LAYOUT.PORTRAIT_SIZE, infoContainer);

        overlay.addChild(infoContainer, statsContainer);
        this.menuContainer.addChild(overlay);

        return { overlay };
    }

    // Helper method for stats container creation
    createStatsContainer(char, portraitSize, infoContainer) {
        const statsContainer = new PIXI.Container();
        statsContainer.x = portraitSize + 80;
        statsContainer.y = 70 + infoContainer.height + 30;

        let rowOffset = 0;
        if ('experience' in char && 'exp_goal' in char) {
            statsContainer.addChild(
                createText(
                    `EXP: ${char.experience}/${char.exp_goal}`,
                    SUB_TEXT_STYLE,
                    0,
                    0
                )
            );
            rowOffset = 1;
        }

        const stats = char.stats;
        Object.entries(stats)
            .filter(([key]) => !key.startsWith('max_') && key !== 'alive' && key !== 'sp')
            .forEach(([key, value], index) => {
                const column = index % 2;
                const row = Math.floor(index / 2) + rowOffset;
                
                const displayValue = key === 'hp' ? `${value}/${stats.max_hp}` :
                                   key === 'mp' ? `${value}/${stats.max_mp}` :
                                   value;
                
                statsContainer.addChild(
                    createText(
                        `${key.toUpperCase()}: ${displayValue}`,
                        SUB_TEXT_STYLE,
                        column * 250,
                        row * 30
                    )
                );
            });

        return statsContainer;
    }

    renderMessageOverlay(gameState) {
        const width = this.app.screen.width - 400;
        const minHeight = gameState.portrait_image_url ? 275 : 150;
        return this.renderMessageOverlayWithDimensions(gameState, width, minHeight, false);
    }

    renderBattleMessageOverlay(gameState) {
        const width = this.app.screen.width - 400;
        const LAYOUT = {
            PADDING: 20,
            TEXT_MARGIN: 30,
            PORTRAIT_SIZE: 150
        };

        // Calculate heights of text elements
        let totalHeight = LAYOUT.PADDING * 2; // Start with padding
        
        // Calculate main text height if it exists
        if (gameState.main_text) {
            const mainText = this.createWrappedText(
                gameState.main_text,
                TEXT_STYLE,
                LAYOUT.TEXT_MARGIN,
                0, // Temporary y position
                width - (LAYOUT.PADDING * 2)
            );
            totalHeight += mainText.height + LAYOUT.PADDING;
        }

        // Calculate sub text height if it exists
        let subTextHeight = 0;
        if (gameState.sub_text) {
            const subTextWidth = width - (LAYOUT.PORTRAIT_SIZE * 2) - (LAYOUT.PADDING * 4);
            const subText = this.createWrappedText(
                gameState.sub_text,
                SUB_TEXT_STYLE,
                0, // Temporary x position
                0, // Temporary y position
                subTextWidth
            );
            subTextHeight = subText.height;
        }

        // Final height should accommodate portraits and sub text
        const portraitHeight = LAYOUT.PORTRAIT_SIZE + (LAYOUT.PADDING * 2);
        const contentHeight = Math.max(portraitHeight, subTextHeight + (LAYOUT.PADDING * 2));
        totalHeight += contentHeight;

        // Create overlay with calculated dimensions
        const overlayX = (this.app.screen.width - width) / 2;
        const overlayY = (this.app.screen.height - totalHeight) / 2;
        const overlay = this.createBaseOverlay(width, totalHeight, overlayX, overlayY);

        // Add main text if it exists
        let currentY = LAYOUT.PADDING;
        if (gameState.main_text) {
            const mainText = this.createWrappedText(
                gameState.main_text,
                TEXT_STYLE,
                LAYOUT.TEXT_MARGIN,
                currentY,
                width - (LAYOUT.PADDING * 2)
            );
            overlay.addChild(mainText);
            currentY += mainText.height + LAYOUT.PADDING;
        }

        // Add left portrait (player/character portrait) if it exists
        if (gameState.portrait_image_url) {
            const leftPortrait = createPortrait(
                gameState.portrait_image_url,
                LAYOUT.TEXT_MARGIN,
                currentY,
                LAYOUT.PORTRAIT_SIZE
            );
            overlay.addChild(leftPortrait);
        }

        // Calculate if we should show right portrait
        const showRightPortrait = gameState.npc_portrait_url && gameState.npc_portrait_url !== gameState.portrait_image_url;

        // Add right portrait (NPC portrait) if it exists
        if (showRightPortrait) {
            const rightPortrait = createPortrait(
                gameState.npc_portrait_url,
                width - LAYOUT.PORTRAIT_SIZE - LAYOUT.TEXT_MARGIN,
                currentY,
                LAYOUT.PORTRAIT_SIZE
            );
            overlay.addChild(rightPortrait);
        }


        // Update sub text width calculation to be dynamic
        if (gameState.sub_text) {
            const subTextWidth = width - LAYOUT.PORTRAIT_SIZE - (LAYOUT.PADDING * 4) - 
                (showRightPortrait ? LAYOUT.PORTRAIT_SIZE + (LAYOUT.PADDING * 2) : 0);
            const subText = this.createWrappedText(
                gameState.sub_text,
                SUB_TEXT_STYLE,
                LAYOUT.PORTRAIT_SIZE + (LAYOUT.PADDING * 3),
                currentY,
                subTextWidth
            );
            overlay.addChild(subText);
        }

        this.menuContainer.addChild(overlay);
        this.menuContainer.interactive = false;
        this.menuContainer.buttonMode = false;

        return { overlay };
    }
}
