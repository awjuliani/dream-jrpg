import { RESOLUTION, TEXT_STYLE, SUB_TEXT_STYLE, LAYOUT, STYLE, WINDOW } from './constants.js';
import {
    createBlurSprite,
    createBorder,
    createText,
    createPortrait,
    createButtonContainer,
    applyDefaultStyleToButton,
    applyHoverStyleToButton,
    applyPressedStyleToButton,
    applyDefaultStyleToCharacterBox,
    applyHoverStyleToCharacterBox,
    applyPressedStyleToCharacterBox,
    updateSubTextBox,
    createSubTextPortrait,
    adjustTextForPortrait,
    resetTextPosition,
} from './ui_helpers.js';
import { LoadingScreen } from './loading.js';
import { TitleScreen } from './title.js';
import { TextInput } from './text_input.js';
import { MessageRenderer } from './message.js';
import { TravelRenderer } from './travel.js';
import { BattleRenderer } from './battle.js';
import { ConversationRenderer } from './conversation.js';

class Renderer {
    constructor(game) {
        this.game = game;
        this.initializeApp();
        this.createMainContainers();
        this.createTextElements();
        this.menuButtons = [];
        this.isLoading = false;
        this.textInputContainer = null;
        this.backgroundTextureCache = {};

        // Properties for keyboard control
        this.selectedButtonIndex = -1; // No button selected initially
        this.selectedCharacterIndex = -1; // No character selected initially
        this.keyDownHandler = this.onKeyDown.bind(this);
        this.keyUpHandler = this.onKeyUp.bind(this);
        this.enableKeyboardControl();
        this.isEnterKeyDown = false;

        this.titleContainer = null;  // Add this line to track the title container
        this.loadingScreen = new LoadingScreen(this.app);
        this.titleScreen = new TitleScreen(this.app, this.mainContainer);
        this.textInput = null;
        this.messageRenderer = new MessageRenderer(this.app, this.menuContainer);
        this.travelRenderer = new TravelRenderer(this.app, this.menuContainer);
        this.battleRenderer = new BattleRenderer(this.app, this.mainContainer, this.game);
        this.conversationRenderer = new ConversationRenderer(this.app, this.mainContainer);
    }

    initializeApp() {
        this.app = new PIXI.Application({
            width: WINDOW.DEFAULT_WIDTH,
            height: WINDOW.DEFAULT_HEIGHT,
            backgroundColor: STYLE.COLORS.BACKGROUND,
            view: document.getElementById('game-canvas'),
            resolution: RESOLUTION,
            autoDensity: true
        });

        // Create the game content container first
        this.gameContentContainer = new PIXI.Container();
        this.app.stage.addChild(this.gameContentContainer);

        // Initialize loading screen with the app
        this.loadingScreen = new LoadingScreen(this.app);
    }

    enableKeyboardControl() {
        // Add keydown and keyup event listeners for keyboard navigation
        window.addEventListener('keydown', this.keyDownHandler);
        window.addEventListener('keyup', this.keyUpHandler);
    }

    onKeyDown(event) {
        if (this.isLoading) return;

        switch(event.key) {
            case 'ArrowUp':
            case 'ArrowLeft':
            case 'ArrowDown':
            case 'ArrowRight':
                this.navigateInteractiveElements(event.key);
                break;
            case 'Enter':
                if (!this.isEnterKeyDown) {
                    this.isEnterKeyDown = true;
                    if (this.selectedButtonIndex >= 0 && this.selectedButtonIndex < this.menuButtons.length) {
                        const selectedButton = this.menuButtons[this.selectedButtonIndex];
                        applyPressedStyleToButton(selectedButton);
                        if (selectedButton.onClick) {
                            selectedButton.onClick();
                        }
                    } else if (this.selectedCharacterIndex >= 0) {
                        const characterBoxes = this.battleRenderer.getCharacterBoxes();
                        if (this.selectedCharacterIndex < characterBoxes.length) {
                            const boxContainer = characterBoxes[this.selectedCharacterIndex];
                            applyPressedStyleToCharacterBox(boxContainer);
                            if (boxContainer.onClick) {
                                boxContainer.onClick();
                            }
                        }
                    }
                }
                break;
        }
    }

    onKeyUp(event) {
        if (event.key === 'Enter' && this.isEnterKeyDown) {
            this.isEnterKeyDown = false;
            if (this.selectedButtonIndex >= 0 && this.selectedButtonIndex < this.menuButtons.length) {
                const selectedButton = this.menuButtons[this.selectedButtonIndex];
                applyHoverStyleToButton(selectedButton);
            } else if (this.selectedCharacterIndex >= 0) {
                const characterBoxes = this.battleRenderer.getCharacterBoxes();
                if (this.selectedCharacterIndex < characterBoxes.length) {
                    const boxContainer = characterBoxes[this.selectedCharacterIndex];
                    applyHoverStyleToCharacterBox(boxContainer);
                }
            }
        }
    }

    navigateInteractiveElements(key) {
        // Determine if we are in a state where characters are selectable
        const charactersSelectable = this.game.gameState.input_type === 'battle_target';

        if (charactersSelectable) {
            // Navigate character boxes
            this.navigateCharacterBoxes(key);
        } else {
            // Navigate menu buttons
            const delta = (key === 'ArrowUp' || key === 'ArrowLeft') ? -1 : 1;
            this.navigateButtons(delta);
        }
    }

    navigateButtons(delta) {
        // Deselect current button if exists
        if (this.selectedButtonIndex >= 0 && this.selectedButtonIndex < this.menuButtons.length) {
            const currentButton = this.menuButtons[this.selectedButtonIndex];
            applyDefaultStyleToButton(currentButton);
        }

        // Update selectedButtonIndex
        this.selectedButtonIndex += delta;
        if (this.selectedButtonIndex < 0) {
            this.selectedButtonIndex = this.menuButtons.length - 1;
        } else if (this.selectedButtonIndex >= this.menuButtons.length) {
            this.selectedButtonIndex = 0;
        }

        // Select and style new button
        if (this.selectedButtonIndex >= 0 && this.selectedButtonIndex < this.menuButtons.length) {
            const selectedButton = this.menuButtons[this.selectedButtonIndex];
            applyHoverStyleToButton(selectedButton);
            
            // Handle option details and portraits for different states
            if (this.game.gameState.input_type === 'travel') {
                if (selectedButton.isDirectionButton && this.game.gameState.option_details) {
                    this.subText.text = this.game.gameState.option_details[selectedButton.optionIndex] || this.subText.text;
                    this.setSubTextVisibility(true);
                    this.updateSubTextBox();
                }
            } else if (this.game.gameState.input_type === 'conversation') {
                if (this.game.gameState.option_details && this.game.gameState.option_details[this.selectedButtonIndex]) {
                    this.conversationRenderer.showOptionDetail(this.game.gameState.option_details[this.selectedButtonIndex]);
                }
            } else if (this.game.gameState.input_type === 'menu') {
                // Update portrait first if option_portraits exists
                if (this.game.gameState.option_portraits && this.game.gameState.option_portraits[this.selectedButtonIndex]) {
                    this.renderPortraitInSubText(this.game.gameState.option_portraits[this.selectedButtonIndex]);
                }
                
                // Then update sub_text with option details
                if (this.game.gameState.option_details && this.game.gameState.option_details[this.selectedButtonIndex]) {
                    this.subText.text = this.game.gameState.option_details[this.selectedButtonIndex];
                    this.setSubTextVisibility(true);
                    this.updateSubTextBox();
                }
            }
        }
    }

    navigateCharacterBoxes(key) {
        const characterBoxes = this.battleRenderer.getCharacterBoxes();
        
        // Deselect current character box
        if (this.selectedCharacterIndex >= 0 && this.selectedCharacterIndex < characterBoxes.length) {
            const boxContainer = characterBoxes[this.selectedCharacterIndex];
            const character = this.getCharacterByIndex(this.selectedCharacterIndex);
            const isCharacterDead = character.stats.hp <= 0;
            applyDefaultStyleToCharacterBox(boxContainer, isCharacterDead);
        }

        // Determine movement direction
        const delta = (key === 'ArrowUp' || key === 'ArrowLeft') ? -1 : 1;

        // Update selectedCharacterIndex
        this.selectedCharacterIndex += delta;
        if (this.selectedCharacterIndex < 0) {
            this.selectedCharacterIndex = characterBoxes.length - 1;
        } else if (this.selectedCharacterIndex >= characterBoxes.length) {
            this.selectedCharacterIndex = 0;
        }

        // Select new character box
        if (this.selectedCharacterIndex >= 0 && this.selectedCharacterIndex < characterBoxes.length) {
            const boxContainer = characterBoxes[this.selectedCharacterIndex];
            const character = this.getCharacterByIndex(this.selectedCharacterIndex);
            const isCharacterDead = character.stats.hp <= 0;
            applyHoverStyleToCharacterBox(boxContainer, isCharacterDead);
        }
    }

    createMainContainers() {
        // Add all game content to the gameContentContainer instead of stage
        this.backgroundSprite = new PIXI.Sprite();
        this.gameContentContainer.addChild(this.backgroundSprite);

        this.mainContainer = new PIXI.Container();
        this.gameContentContainer.addChild(this.mainContainer);

        this.menuContainer = new PIXI.Container();
        this.mainContainer.addChild(this.menuContainer);
    }

    createTextElements() {
        const padding = LAYOUT.PADDING;
        
        // Main text elements - create text first but add it last
        this.mainText = createText('', TEXT_STYLE, padding * 2, 20);

        // Create blur and border without initial width
        this.mainTextBlur = createBlurSprite(0, 60, padding, 10);
        this.mainContainer.addChild(this.mainTextBlur);

        this.mainTextBorder = createBorder(padding, 10, 0, 60);
        this.mainContainer.addChild(this.mainTextBorder);

        // Add main text last so it appears on top
        this.mainContainer.addChild(this.mainText);

        // Sub text elements (unchanged)
        const mainTextWidth = this.app.screen.width - (padding * 2);
        this.subTextBlur = createBlurSprite(mainTextWidth, 200, padding, 80);
        this.mainContainer.addChild(this.subTextBlur);

        this.subTextBorder = createBorder(padding, 80, mainTextWidth, 200);
        this.mainContainer.addChild(this.subTextBorder);

        this.subText = createText('', SUB_TEXT_STYLE, padding * 2, 100);
        this.mainContainer.addChild(this.subText);
    }

    attachButtonEvents(container, onClick) {
        container.interactive = true;
        container.buttonMode = true;
        container.onClick = onClick;

        let isPressed = false;

        container.on('pointerdown', () => {
            if (!this.isLoading) {
                isPressed = true;
                applyPressedStyleToButton(container);
            }
        });

        container.on('pointerup', () => {
            if (!this.isLoading && isPressed) {
                onClick();
                isPressed = false;
                this.selectedButtonIndex = this.menuButtons.indexOf(container);
            }
        });

        container.on('pointerupoutside', () => {
            if (isPressed) {
                applyDefaultStyleToButton(container);
                isPressed = false;
            }
        });

        container.on('pointerover', () => {
            if (!this.isLoading && !isPressed) {
                applyHoverStyleToButton(container);
                this.selectedButtonIndex = this.menuButtons.indexOf(container);
                
                // Handle option details and portraits for different states
                if (this.game.gameState.input_type === 'travel') {
                    if (container.isDirectionButton && this.game.gameState.option_details) {
                        this.subText.text = this.game.gameState.option_details[container.optionIndex] || this.subText.text;
                        this.setSubTextVisibility(true);
                        this.updateSubTextBox();
                    }
                } else if (this.game.gameState.input_type === 'conversation') {
                    const buttonIndex = this.menuButtons.indexOf(container);
                    if (this.game.gameState.option_details && this.game.gameState.option_details[buttonIndex]) {
                        this.conversationRenderer.showOptionDetail(this.game.gameState.option_details[buttonIndex]);
                    }
                } else if (this.game.gameState.input_type === 'menu') {
                    const buttonIndex = this.menuButtons.indexOf(container);
                    
                    // Update portrait first if option_portraits exists
                    if (this.game.gameState.option_portraits && this.game.gameState.option_portraits[buttonIndex]) {
                        this.renderPortraitInSubText(this.game.gameState.option_portraits[buttonIndex]);
                    }
                    
                    // Then update sub_text with option details
                    if (this.game.gameState.option_details && this.game.gameState.option_details[buttonIndex]) {
                        this.subText.text = this.game.gameState.option_details[buttonIndex];
                        this.setSubTextVisibility(true);
                        this.updateSubTextBox();
                    }
                }
            }
        });

        container.on('pointerout', () => {
            if (!isPressed) {
                applyDefaultStyleToButton(container);
                this.selectedButtonIndex = -1;
                
                // Handle text and portrait reset for different states
                if (this.game.gameState.input_type === 'conversation') {
                    this.conversationRenderer.resetPlayerText();
                } else if (this.game.gameState.input_type === 'menu' || this.game.gameState.input_type === 'travel') {
                    this.subText.text = this.game.gameState.sub_text || '';
                    this.setSubTextVisibility(true);
                    // Reset portrait to default if it exists, otherwise remove it
                    if (this.game.gameState.portrait_image_url) {
                        this.renderPortraitInSubText(this.game.gameState.portrait_image_url);
                    } else {
                        this.removePortraitFromSubText();
                    }
                } else {
                    this.setSubTextVisibility(false);
                }
            }
        });
    }

    updateDisplay() {
        // Hide title screen when switching to other screens
        this.titleScreen.hide();

        // Add this line to clean up conversation UI when switching states
        if (this.game.gameState.input_type !== 'conversation') {
            this.conversationRenderer.setVisibility(false);
        }

        this.clearMenuOptions();
        this.clearCharacterBoxes();
        this.selectedCharacterIndex = -1;

        // Add this line to properly clear battle state
        this.battleRenderer.clearBattleState();

        if (this.game.gameState) {
            this.setBackgroundImage(this.game.gameState.background_image_url);
            this.renderBasedOnInputType();

            // Update interactivity of character boxes based on input_type
            this.updateCharacterBoxInteractivity();

            // Handle portrait display or removal
            if (['menu', 'travel'].includes(this.game.gameState.input_type) && this.game.gameState.portrait_image_url) {
                this.renderPortraitInSubText(this.game.gameState.portrait_image_url);
            } else {
                this.removePortraitFromSubText();
            }
        } else {
            this.removePortraitFromSubText();
        }
    }

    renderBasedOnInputType() {
        const { input_type } = this.game.gameState;
        switch (input_type) {
            case 'title':
                this.renderTitleScreen();
                break;
            case 'battle':
                this.renderBattleState();
                break;
            case 'battle_target':
                this.renderBattleTargetState();
                break;
            case 'stats_message':
                this.renderStatsMessage();
                break;
            case 'message':
                this.renderMessageOverlay();
                break;
            case 'message_mini':
                this.renderMessageOverlay(400, 150, true);
                break;
            case 'text':
                this.renderTextInputState();
                break;
            case 'travel':
                this.renderTravelState();
                break;
            case 'conversation':
                this.renderConversationState();
                break;
            case 'battle_message':
                this.renderBattleMessageOverlay();
                break;
            case 'dialogue':
                this.renderMessageOverlay();
                break;
            default:
                this.renderDefaultState();
        }
    }

    renderDefaultState() {
        this.mainTextBlur.visible = true;
        this.mainText.text = this.game.gameState.main_text || '';
        this.mainTextBorder.visible = true;

        // Update main text box dimensions
        this.updateMainTextBox();

        // Only show sub_text elements for menu type or when there's actual sub_text content
        const hasSubText = this.game.gameState.sub_text && this.game.gameState.sub_text.trim() !== '';
        const isMenuType = this.game.gameState.input_type === 'menu';
        
        // Set sub_text visibility and content
        if (isMenuType || hasSubText) {
            this.setSubTextVisibility(true);
            this.subText.text = this.game.gameState.sub_text || '';
            
            // Render portrait first if it exists for menu type
            if (isMenuType && this.game.gameState.portrait_image_url) {
                console.log('Rendering portrait in sub_text');
                console.log('Portrait URL:', this.game.gameState.portrait_image_url);
                this.renderPortraitInSubText(this.game.gameState.portrait_image_url);
            } else {
                this.removePortraitFromSubText();
            }

            // Update sub_text box after handling the portrait
            this.updateSubTextBox();
        } else {
            this.setSubTextVisibility(false);
            this.removePortraitFromSubText();
        }

        // Render menu options if input_type is 'menu'
        if (isMenuType) {
            this.renderMenuOptions(this.game.gameState.menu_options || []);
        }
    }

    /**
     * Renders the portrait image on the left side of the sub_text box.
     */
    renderPortraitInSubText(portraitUrl) {
        // Remove existing portrait if it exists
        this.removePortraitFromSubText();

        const padding = LAYOUT.PADDING;
        const portraitSize = LAYOUT.PORTRAIT_SIZE;

        // Create new portrait
        console.log(portraitUrl);
        this.portraitContainer = createSubTextPortrait({
            x: this.subTextBorder.x + padding * 2,
            y: this.subTextBorder.y + padding * 1.2 + portraitSize / 2,
            portraitUrl,
            size: portraitSize
        });

        if (this.portraitContainer) {
            this.mainContainer.addChild(this.portraitContainer);

            // Adjust text position and width
            adjustTextForPortrait({
                textElement: this.subText,
                boxWidth: this.subTextBorder.width,
                portraitSize,
                baseX: this.subTextBorder.x,
                padding
            });
        }
    }

    removePortraitFromSubText() {
        if (this.portraitContainer) {
            this.mainContainer.removeChild(this.portraitContainer);
            this.portraitContainer = null;
        }

        // Reset text position
        resetTextPosition({
            textElement: this.subText,
            boxWidth: this.subTextBorder.width,
            baseX: this.subTextBorder.x,
            padding: LAYOUT.PADDING
        });
    }

    setBackgroundImage(url) {
        if (!url || !url.trim()) {
            this.backgroundSprite.texture = PIXI.Texture.EMPTY;
            return;
        }

        if (this.backgroundTextureCache[url]) {
            this.applyBackgroundTexture(this.backgroundTextureCache[url]);
        } else {
            const texture = PIXI.Texture.from(url);
            this.backgroundTextureCache[url] = texture;
            this.applyBackgroundTexture(texture);
        }
    }

    applyBackgroundTexture(texture) {
        this.backgroundSprite.texture = texture;
        this.backgroundSprite.width = this.app.screen.width;
        this.backgroundSprite.height = this.app.screen.height;
        this.backgroundSprite.texture.baseTexture.scaleMode = PIXI.SCALE_MODES.NEAREST;
    }

    renderBattleState() {
        this.hideMainTexts();
        this.setSubTextVisibility(false);
        this.clearMenuOptions();
        this.battleRenderer.renderBattleState();
    }

    renderBattleTargetState() {
        this.hideMainTexts();
        this.battleRenderer.renderBattleTargetState();
    }

    hideMainTexts() {
        this.mainTextBlur.visible = false;
        this.subTextBlur.visible = false;
        this.mainText.text = '';
        this.subText.text = '';

        this.mainTextBorder.visible = false;
        this.subTextBorder.visible = false;
    }

    renderMenuOptions(options) {
        this.clearMenuOptions();
        
        // Skip if no options
        if (!options.length) return;

        // Calculate button dimensions and layout
        const buttonHeight = Math.min(50, this.app.screen.height * 0.08);
        const buttonWidth = this.game.gameState.input_type === 'battle' ? 
            Math.min(75, this.app.screen.width * 0.08) : 
            Math.min(250, this.app.screen.width * 0.28);
        const padding = 10;
        const columnSpacing = padding * 4;
        
        // Determine grid layout - use single column for single option
        const columns = this.game.gameState.input_type === 'battle' ? 6 : 
            (options.length === 1 ? 1 : 2);
        const rows = Math.ceil(options.length / columns);
        
        // Calculate total width and height of button grid
        const totalGridWidth = (buttonWidth * columns) + (columnSpacing * (columns - 1));
        const totalGridHeight = (buttonHeight * rows) + (padding * (rows - 1));
        
        // Calculate starting position to center the entire grid
        const startX = (this.app.screen.width - totalGridWidth) / 2;
        const startY = this.app.screen.height - totalGridHeight - padding * 2;

        options.forEach((option, index) => {
            const column = index % columns;
            const row = Math.floor(index / columns);
            
            const buttonContainer = createButtonContainer(option, buttonWidth);
            
            // Position button within grid, using columnSpacing between columns
            buttonContainer.x = startX + (column * (buttonWidth + columnSpacing)) + buttonWidth / 2;
            buttonContainer.y = startY + (row * (buttonHeight + padding));

            const onClickHandler = () => {
                this.game.handleInput(option);
            };

            this.attachButtonEvents(buttonContainer, onClickHandler);
            buttonContainer.onClick = onClickHandler;
            
            this.menuButtons.push(buttonContainer);
            this.menuContainer.addChild(buttonContainer);
        });

        // Don't select any button by default
        this.selectedButtonIndex = -1;
    }

    highlightButton(index) {
        if (this.selectedButtonIndex !== -1 && this.selectedButtonIndex !== index) {
            this.unhighlightButton(this.selectedButtonIndex);
        }
        this.selectedButtonIndex = index;
        applyHoverStyleToButton(this.menuButtons[index]);
    }

    unhighlightButton(index) {
        applyDefaultStyleToButton(this.menuButtons[index]);
        if (this.selectedButtonIndex === index) {
            this.selectedButtonIndex = -1;
        }
    }

    clearMenuOptions() {
        this.menuButtons.forEach(button => button.destroy());
        this.menuButtons = [];
        this.selectedButtonIndex = -1;
        this.menuContainer.removeChildren();
        if (this.battleMenuContainer) {  // Add this check
            this.battleMenuContainer.removeChildren();
        }
        if (this.textInput) {
            this.textInput.destroy();
            this.textInput = null;
        }
    }

    clearCharacterBoxes() {
        this.battleRenderer.getCharacterBoxes().forEach(boxContainer => {
            boxContainer.destroy();
        });
    }

    setLoading(isLoading) {
        this.isLoading = isLoading;
        if (isLoading) {
            this.loadingScreen.show();
        } else {
            this.loadingScreen.hide();
        }
    }

    renderContinueButton() {
        const buttonContainer = createButtonContainer('Continue');
        
        // Position at bottom of screen with some padding
        const bottomPadding = 60;
        buttonContainer.y = this.app.screen.height - bottomPadding;
        buttonContainer.x = this.app.screen.width / 2;

        const onClickHandler = () => {
            this.game.handleInput('Continue');
        };

        this.attachButtonEvents(buttonContainer, onClickHandler);
        buttonContainer.onClick = onClickHandler;

        this.menuButtons.push(buttonContainer);
        this.menuContainer.addChild(buttonContainer);

        // Select the continue button by default
        this.selectedButtonIndex = this.menuButtons.length - 1;
        applyHoverStyleToButton(buttonContainer);
    }

    renderMessageOverlay(forcedWidth, forcedHeight, isSmall = false) {
        this.hideMainTexts();
        const { overlay } = this.messageRenderer.renderMessageOverlay(
            this.game.gameState,
            forcedWidth,
            forcedHeight,
            isSmall
        );
        this.renderContinueButton();
    }

    renderTextInputState() {
        this.renderDefaultState();
        if (!this.textInput) {
            this.textInput = new TextInput(this.app, this.menuContainer, this.game);
        }
        this.textInput.render();
    }

    // Clean up the event listener when destroying the renderer
    destroy() {
        window.removeEventListener('keydown', this.keyDownHandler);
        window.removeEventListener('keyup', this.keyUpHandler);
        if (this.battleRenderer) {
            this.battleRenderer.destroy();
        }
        if (this.conversationRenderer) {
            this.conversationRenderer.destroy();
        }
    }

    getCharacterByIndex(index) {
        const { player_party, enemy_party, input_type } = this.game.gameState;
        let characters;

        if (input_type === 'battle_target') {
            characters = player_party.characters.concat(enemy_party.characters);
        } else {
            characters = player_party.characters;
        }

        return characters[index];
    }

    updateCharacterBoxInteractivity() {
        const isTargetSelection = this.game.gameState.input_type === 'battle_target';
        const characterBoxes = this.battleRenderer.getCharacterBoxes();
        characterBoxes.forEach(boxContainer => {
            boxContainer.interactive = isTargetSelection;
            boxContainer.buttonMode = isTargetSelection;
        });
    }

    renderStatsMessage() {
        this.hideMainTexts();
        const { overlay } = this.messageRenderer.renderStatsMessage(this.game.gameState);
        this.renderContinueButton();
    }

    renderTitleScreen() {
        // Hide all standard text elements
        this.hideMainTexts();
        
        // Ensure subtext elements are hidden
        this.setSubTextVisibility(false);
        
        // Hide any existing title screen first
        this.titleScreen.hide();

        // Render the title screen
        this.titleScreen.render(this.game.gameState);

        // Render menu options if they exist
        if (this.game.gameState.menu_options?.length > 0) {
            this.renderMenuOptions(this.game.gameState.menu_options);
        }
    }

    updateSubTextBox() {
        this.subTextBorder = updateSubTextBox(
            this.app,
            this.subText,
            this.subTextBlur,
            this.subTextBorder,
            this.mainContainer,
            this.game.gameState
        );
    }

    renderTravelState() {
        this.renderDefaultState();
        this.clearMenuOptions();

        // Create a wrapper for the attachButtonEvents method
        const attachButtonEvents = (buttonContainer, option) => {
            this.attachButtonEvents(buttonContainer, () => {
                this.game.handleInput(option);
            });
        };

        // Get the menu buttons from the travel renderer
        this.menuButtons = this.travelRenderer.render(this.game.gameState, attachButtonEvents);
    }

    // Add this new helper method
    setSubTextVisibility(visible) {
        this.subText.visible = visible;
        this.subTextBorder.visible = visible;
        this.subTextBlur.visible = visible;
    }

    // Add new method to handle main text box sizing
    updateMainTextBox() {
        const padding = LAYOUT.PADDING;
        const extraPadding = padding * 3; // Add extra padding for better readability
        const maxWidth = this.app.screen.width - (padding * 2); // Maximum allowed width
        
        // Store current text style properties
        const currentStyle = { ...this.mainText.style };
        
        // Set word wrap width to maximum allowed width while preserving other style properties
        this.mainText.style = {
            ...TEXT_STYLE,
            ...currentStyle,
            wordWrapWidth: maxWidth - (padding * 4)
        };
        
        // Calculate new width based on text width
        const newWidth = Math.min(this.mainText.width + extraPadding, maxWidth);
        
        // Update blur sprite
        this.mainTextBlur.width = newWidth;
        
        // Update border
        this.mainContainer.removeChild(this.mainTextBorder);
        this.mainTextBorder = createBorder(padding, 10, newWidth, 60);
        this.mainContainer.addChild(this.mainTextBorder);
    }

    renderConversationState() {
        this.hideMainTexts();
        this.conversationRenderer.render(this.game.gameState);
        
        // Render menu options in a single row with 4 columns
        if (this.game.gameState.menu_options?.length > 0) {
            const options = this.game.gameState.menu_options;
            
            // Calculate button dimensions and layout
            const buttonHeight = 50;
            const buttonWidth = 150;
            const horizontalPadding = LAYOUT.PADDING * 4; // Increased horizontal spacing
            const verticalPadding = LAYOUT.PADDING; // Original vertical spacing
            
            // Position buttons at the bottom
            const startY = this.app.screen.height - buttonHeight - verticalPadding * 2;
            const totalWidth = (buttonWidth * Math.min(4, options.length)) + (horizontalPadding * (Math.min(4, options.length) - 1));
            const startX = (this.app.screen.width - totalWidth) / 2;

            options.forEach((option, index) => {
                if (index < 4) { // Limit to 4 options
                    const buttonContainer = createButtonContainer(option, buttonWidth);
                    buttonContainer.x = startX + (index * (buttonWidth + horizontalPadding)) + buttonWidth / 2;
                    buttonContainer.y = startY;

                    const onClickHandler = () => {
                        this.game.handleInput(option);
                    };

                    this.attachButtonEvents(buttonContainer, onClickHandler);
                    buttonContainer.onClick = onClickHandler;
                    
                    this.menuButtons.push(buttonContainer);
                    this.menuContainer.addChild(buttonContainer);
                }
            });
        }
    }

    renderBattleMessageOverlay() {
        this.hideMainTexts();
        const { overlay } = this.messageRenderer.renderBattleMessageOverlay(this.game.gameState);
        this.renderContinueButton();
    }
}

export { Renderer };
