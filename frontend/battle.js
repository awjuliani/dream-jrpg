import { STYLE, LAYOUT, PLAYER_CHARACTER_TEXT_STYLE, ENEMY_CHARACTER_TEXT_STYLE, CHARACTER_TEXT_STYLE, SUB_TEXT_STYLE } from './constants.js';
import {
    createBlurSprite,
    createBorder,
    createText,
    createBar,
    createPortrait,
    createButtonContainer,
    applyDefaultStyleToButton,
    applyHoverStyleToButton,
    applyPressedStyleToButton,
    applyDefaultStyleToCharacterBox,
    applyHoverStyleToCharacterBox,
    applyPressedStyleToCharacterBox,
    truncateText
} from './ui_helpers.js';

const BATTLE_UI = {
    PORTRAIT: {
        SIZE: 128,
        BOSS_SIZE: 178,
        PADDING: 20
    },
    BOX: {
        PLAYER: {
            WIDTH: 375,
            HEIGHT: 170,
            ACTIVE_HEIGHT: 280
        },
        ENEMY: {
            WIDTH: 160,
            BOSS_WIDTH: 210,
            HEIGHT: LAYOUT.PORTRAIT_SIZE + 50,
            BOSS_HEIGHT: LAYOUT.PORTRAIT_SIZE + 100
        },
        SPACING: 15,
        BORDER_RADIUS: 10
    },
    STATS: {
        BAR_WIDTH: 190,
        BAR_HEIGHT: 10
    },
    MENU: {
        COLUMNS: 3,
        ROWS: 2,
        COLUMN_SPACING: 40,
        ROW_SPACING: 8
    }
};

export class BattleRenderer {
    constructor(app, mainContainer, game) {
        this.app = app;
        this.mainContainer = mainContainer;
        this.game = game;
        this.characterContainer = new PIXI.Container();
        this.battleMenuContainer = new PIXI.Container();
        this.menuButtons = [];
        
        this.mainContainer.addChild(this.characterContainer);
        this.mainContainer.addChild(this.battleMenuContainer);
    }

    getCharacterContainer() {
        return this.characterContainer;
    }

    getCharacterBoxes() {
        return this.characterContainer.children;
    }

    renderBattleState() {
        this.clearContainers();
        // Render main text at the top of the screen
        if (this.game.gameState.main_text) {
            const padding = 20;
            const height = 45;
            const mainTextBlur = createBlurSprite(this.app.screen.width - (padding * 2), height, padding, padding);
            const mainTextBorder = createBorder(padding, padding, this.app.screen.width - (padding * 2), height);
            const mainTextElement = createText(this.game.gameState.main_text, SUB_TEXT_STYLE, padding * 2, padding + 10);
            
            this.battleMenuContainer.addChild(mainTextBlur, mainTextBorder, mainTextElement);
        }

        // Render player party
        if (this.game.gameState.player_party?.characters) {
            this.renderParty(this.game.gameState.player_party.characters, true);
        }

        // Render enemy party
        if (this.game.gameState.enemy_party?.characters) {
            this.renderParty(this.game.gameState.enemy_party.characters, false);
        }

        // Find and render battle menu for active character
        const activeCharacterIndex = this.game.gameState.player_party.characters.findIndex(char => char.active_turn);
        if (activeCharacterIndex !== -1) {
            this.renderBattleMenu(activeCharacterIndex);
        }
    }

    renderBattleTargetState() {
        this.clearContainers();
        const { player_party, enemy_party, main_text } = this.game.gameState;
        
        // Render main text at the top of the screen
        if (main_text) {
            const padding = 20;
            const height = 45;
            const mainTextBlur = createBlurSprite(this.app.screen.width - (padding * 2), height, padding, padding);
            const mainTextBorder = createBorder(padding, padding, this.app.screen.width - (padding * 2), height);
            const mainTextElement = createText(main_text, SUB_TEXT_STYLE, padding * 2, padding + 10);
            
            this.battleMenuContainer.addChild(mainTextBlur, mainTextBorder, mainTextElement);
        }
        
        // For battle_target input type, render both parties
        if (player_party?.characters) {
            this.renderParty(player_party.characters, true);
        }
        if (enemy_party?.characters) {
            this.renderParty(enemy_party.characters, false);
        }

        // Add Back button
        const buttonContainer = createButtonContainer('Back');
        
        // Position at bottom of screen with padding
        const bottomPadding = 60;
        buttonContainer.y = this.app.screen.height - bottomPadding;
        buttonContainer.x = this.app.screen.width / 2;

        const onClickHandler = () => {
            this.game.handleInput(null);
        };

        // Attach events using the same pattern as other buttons
        this.attachButtonEvents(buttonContainer, onClickHandler);
        buttonContainer.onClick = onClickHandler;

        this.battleMenuContainer.addChild(buttonContainer);
    }

    renderParty(characters, isPlayer) {
        // Skip if no characters
        if (!characters || characters.length === 0) return;

        const boxes = characters.map(char => ({
            width: isPlayer ? BATTLE_UI.BOX.PLAYER.WIDTH : 
                (char.enemy_type === "boss" ? BATTLE_UI.BOX.ENEMY.BOSS_WIDTH : BATTLE_UI.BOX.ENEMY.WIDTH),
            height: isPlayer ? BATTLE_UI.BOX.PLAYER.HEIGHT : 
                (char.enemy_type === "boss" ? BATTLE_UI.BOX.ENEMY.BOSS_HEIGHT : BATTLE_UI.BOX.ENEMY.HEIGHT)
        }));

        // Calculate total width including spacing
        const totalWidth = boxes.reduce((sum, box, i) => 
            sum + box.width + (i < boxes.length - 1 ? BATTLE_UI.BOX.SPACING : 0), 0);
        
        const startX = (this.app.screen.width - totalWidth) / 2;
        const yPosition = isPlayer ? this.app.screen.height - boxes[0].height - 140 : 90;

        let currentX = startX;
        characters.forEach((character, index) => {
            const characterBox = this.createCharacterBox(character, index, isPlayer);
            characterBox.x = currentX;
            characterBox.y = yPosition;
            this.characterContainer.addChild(characterBox);
            
            currentX += boxes[index].width + BATTLE_UI.BOX.SPACING;
        });
    }

    createCharacterBox(character, index, isPlayer) {
        const boxContainer = new PIXI.Container();
        const isCharacterDead = character.stats.hp <= 0;
        const isActiveTurn = character.active_turn;
        const isBoss = !isPlayer && character.enemy_type === "boss";
        
        const textColor = isCharacterDead ? 0x808080 : 0xFFFFFF;
        const borderColor = isCharacterDead ? 0x808080 : 
            (isActiveTurn ? STYLE.COLORS.ACTIVE_TURN : STYLE.COLORS.BORDER_DEFAULT);

        const boxWidth = isPlayer ? BATTLE_UI.BOX.PLAYER.WIDTH : 
            (isBoss ? BATTLE_UI.BOX.ENEMY.BOSS_WIDTH : BATTLE_UI.BOX.ENEMY.WIDTH);
        const boxHeight = isPlayer 
            ? (isActiveTurn && this.game.gameState.input_type !== 'battle_target' 
                ? BATTLE_UI.BOX.PLAYER.ACTIVE_HEIGHT 
                : BATTLE_UI.BOX.PLAYER.HEIGHT) 
            : (isBoss ? BATTLE_UI.BOX.ENEMY.BOSS_HEIGHT : BATTLE_UI.BOX.ENEMY.HEIGHT);

        const border = createBorder(0, 0, boxWidth, boxHeight, BATTLE_UI.BOX.BORDER_RADIUS, borderColor);
        const blurSprite = createBlurSprite(boxWidth, boxHeight, 0, 0);

        boxContainer.addChild(blurSprite, border);

        if (isPlayer) {
            this.renderPlayerCharacterBox(boxContainer, character, textColor);
        } else {
            this.renderEnemyCharacterBox(boxContainer, character, textColor, boxWidth);
        }

        boxContainer.interactive = this.game.gameState.input_type === 'battle_target';
        boxContainer.buttonMode = this.game.gameState.input_type === 'battle_target';
        boxContainer.onClick = () => this.activateCharacterBox(character);

        this.attachCharacterBoxEvents(boxContainer, character);

        return boxContainer;
    }

    renderPlayerCharacterBox(boxContainer, character, textColor) {
        const { SIZE: portraitSize, PADDING: padding } = BATTLE_UI.PORTRAIT;
        const portrait = createPortrait(character, padding, padding, portraitSize, character.stats.hp <= 0);
        boxContainer.addChild(portrait);

        const textStartX = portraitSize + (padding * 2);
        const nameText = createText(
            truncateText(character.name, 170, { ...PLAYER_CHARACTER_TEXT_STYLE, fill: textColor }), 
            { ...PLAYER_CHARACTER_TEXT_STYLE, fill: textColor }, 
            textStartX, 
            padding
        );
        boxContainer.addChild(nameText);

        // Stats text
        const statsConfig = [
            { label: 'HP', value: character.stats.hp, max: character.stats.max_hp, color: STYLE.COLORS.HP_BAR },
            { label: 'MP', value: character.stats.mp, max: character.stats.max_mp, color: character.stats.hp <= 0 ? STYLE.COLORS.BORDER_INACTIVE : STYLE.COLORS.MP_BAR },
            { label: 'SP', value: character.stats.sp, max: character.stats.max_sp, color: character.stats.hp <= 0 ? STYLE.COLORS.BORDER_INACTIVE : STYLE.COLORS.SP_BAR }
        ];

        statsConfig.forEach((stat, index) => {
            const yOffset = index * 35;
            const text = createText(
                `${stat.label}: ${stat.value} / ${stat.max}`,
                { ...CHARACTER_TEXT_STYLE, fill: textColor },
                textStartX,
                padding + 30 + yOffset
            );
            const bar = createBar(
                textStartX,
                padding + 50 + yOffset,
                BATTLE_UI.STATS.BAR_WIDTH,
                BATTLE_UI.STATS.BAR_HEIGHT,
                stat.value,
                stat.max,
                stat.color
            );
            boxContainer.addChild(text, bar);
        });
    }

    renderEnemyCharacterBox(boxContainer, character, textColor, boxWidth) {
        const isBoss = character.enemy_type === "boss";
        const portraitSize = isBoss ? BATTLE_UI.PORTRAIT.BOSS_SIZE : BATTLE_UI.PORTRAIT.SIZE;
        
        // Center the portrait in the box
        const portrait = createPortrait(
            character, 
            (boxWidth - portraitSize) / 2, 
            15, 
            portraitSize, 
            character.stats.hp <= 0
        );
        boxContainer.addChild(portrait);

        // Fix: Correct object syntax for nameStyle
        const nameStyle = {
            ...ENEMY_CHARACTER_TEXT_STYLE,
            fill: textColor,
            wordWrap: true,
            wordWrapWidth: boxWidth - 20,
            align: 'center',
            fontSize: isBoss ? ENEMY_CHARACTER_TEXT_STYLE.fontSize + 4 : ENEMY_CHARACTER_TEXT_STYLE.fontSize // Slightly larger text for bosses
        };

        const nameText = createText(
            character.name, 
            nameStyle, 
            boxWidth / 2, 
            (isBoss ? BATTLE_UI.PORTRAIT.BOSS_SIZE + 20 : LAYOUT.PORTRAIT_SIZE) + 20, 
            0.5
        );
        boxContainer.addChild(nameText);
    }

    renderBattleMenu(activeCharacterIndex) {
        const activeCharacterBox = this.characterContainer.children[activeCharacterIndex];
        const options = this.game.gameState.menu_options || [];
        
        const { COLUMNS, ROWS, COLUMN_SPACING, ROW_SPACING } = BATTLE_UI.MENU;
        const buttonWidth = LAYOUT.BUTTON.BATTLE_WIDTH;
        const buttonHeight = LAYOUT.BUTTON.HEIGHT;
        
        const totalGridWidth = (buttonWidth * COLUMNS) + (COLUMN_SPACING * (COLUMNS - 1));
        const totalGridHeight = (buttonHeight * ROWS) + (ROW_SPACING * (ROWS - 1));
        
        const startX = activeCharacterBox.x + (activeCharacterBox.width / 2) - (totalGridWidth / 2);
        const startY = activeCharacterBox.y + (activeCharacterBox.height / 2) - (totalGridHeight / 2) + 100;

        options.forEach((option, index) => {
            const row = Math.floor(index / COLUMNS);
            const col = index % COLUMNS;
            
            const buttonContainer = createButtonContainer(option, buttonWidth);
            buttonContainer.x = startX + (col * (buttonWidth + COLUMN_SPACING)) + buttonWidth / 2;
            buttonContainer.y = startY + (row * (buttonHeight + ROW_SPACING));

            const onClickHandler = () => this.game.handleInput(option);
            this.attachButtonEvents(buttonContainer, onClickHandler);
            buttonContainer.onClick = onClickHandler;
            
            this.menuButtons.push(buttonContainer);
            this.battleMenuContainer.addChild(buttonContainer);
        });
    }

    attachCharacterBoxEvents(boxContainer, character) {
        let isPressed = false;

        boxContainer.on('pointerdown', () => {
            if (this.game.gameState.input_type === 'battle_target' && !this.game.renderer.isLoading) {
                isPressed = true;
                applyPressedStyleToCharacterBox(boxContainer, character.stats.hp <= 0);
            }
        });

        boxContainer.on('pointerup', () => {
            if (this.game.gameState.input_type === 'battle_target' && !this.game.renderer.isLoading && isPressed) {
                boxContainer.onClick();
                applyDefaultStyleToCharacterBox(boxContainer, character.stats.hp <= 0);
                isPressed = false;
            }
        });

        boxContainer.on('pointerupoutside', () => {
            if (isPressed) {
                applyDefaultStyleToCharacterBox(boxContainer, character.stats.hp <= 0);
                isPressed = false;
            }
        });

        boxContainer.on('pointerover', () => {
            if (this.game.gameState.input_type === 'battle_target' && !this.game.renderer.isLoading && !isPressed) {
                applyHoverStyleToCharacterBox(boxContainer, character.stats.hp <= 0);
            }
        });

        boxContainer.on('pointerout', () => {
            if (!isPressed) {
                applyDefaultStyleToCharacterBox(boxContainer, character.stats.hp <= 0);
            }
        });
    }

    attachButtonEvents(buttonContainer, onClick) {
        let isPressed = false;

        buttonContainer.interactive = true;
        buttonContainer.buttonMode = true;

        buttonContainer.on('pointerdown', () => {
            if (!this.game.renderer.isLoading) {
                isPressed = true;
                applyPressedStyleToButton(buttonContainer);
            }
        });

        buttonContainer.on('pointerup', () => {
            if (!this.game.renderer.isLoading && isPressed) {
                onClick();
                isPressed = false;
            }
        });

        buttonContainer.on('pointerupoutside', () => {
            if (isPressed) {
                applyDefaultStyleToButton(buttonContainer);
                isPressed = false;
            }
        });

        buttonContainer.on('pointerover', () => {
            if (!this.game.renderer.isLoading && !isPressed) {
                applyHoverStyleToButton(buttonContainer);
            }
        });

        buttonContainer.on('pointerout', () => {
            if (!isPressed) {
                applyDefaultStyleToButton(buttonContainer);
            }
        });
    }

    activateCharacterBox(character) {
        this.game.handleInput(character.name);
    }

    clearContainers() {
        this.characterContainer.removeChildren();
        this.battleMenuContainer.removeChildren();
        this.menuButtons = [];
    }

    destroy() {
        this.clearContainers();
        this.mainContainer.removeChild(this.characterContainer);
        this.mainContainer.removeChild(this.battleMenuContainer);
    }

    clearBattleState() {
        this.clearContainers();
        this.menuButtons = [];
    }
}
