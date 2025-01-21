import { BUTTON_STYLE, CHARACTER_TEXT_STYLE, LAYOUT, STYLE } from './constants.js';

// Add type imports and documentation
/**
 * @typedef {Object} Character
 * @property {string} portrait - URL/path to character portrait
 * @property {boolean} active_turn - Whether it's the character's turn
 */

// Utility functions
function createBasicGraphics(x, y, width, height, radius, color, alpha = 1) {
    const graphics = new PIXI.Graphics();
    graphics.beginFill(color, alpha);
    graphics.drawRoundedRect(x, y, width, height, radius);
    graphics.endFill();
    return graphics;
}

// Text helper functions
function applyTextStyles(textElements, styles) {
    textElements.forEach(text => {
        Object.assign(text.style, styles);
    });
}

function truncateText(text, maxWidth, style) {
    const tempText = new PIXI.Text(text, style);
    if (tempText.width <= maxWidth) {
        return text;
    }
    
    let truncated = text;
    while (tempText.width > maxWidth) {
        truncated = truncated.slice(0, -1);
        tempText.text = truncated + '...';
    }
    return truncated + '...';
} 

function createBlurSprite(width, height, x, y, alpha = STYLE.BLUR.ALPHA) {
    const blurSprite = new PIXI.Sprite(PIXI.Texture.WHITE);
    blurSprite.width = width;
    blurSprite.height = height;
    blurSprite.x = x;
    blurSprite.y = y;
    blurSprite.alpha = alpha;
    blurSprite.filters = [new PIXI.filters.BlurFilter(STYLE.BLUR.INTENSITY)];
    blurSprite.tint = STYLE.COLORS.BACKGROUND;
    return blurSprite;
}

function createBorder(x, y, width, height, radius = STYLE.BORDER.RADIUS, color = STYLE.COLORS.BORDER_DEFAULT) {
    const border = new PIXI.Graphics();
    border.lineStyle(STYLE.BORDER.WIDTH, color, 1);
    border.drawRoundedRect(x, y, width, height, radius);
    return border;
}

function createText(text, style, x, y, anchor = 0) {
    const pixiText = new PIXI.Text(text, style);
    pixiText.x = x;
    pixiText.y = y;
    pixiText.anchor.set(anchor);
    return pixiText;
}

function createBar(x, y, width, height, value, maxValue, color) {
    const percentage = value / maxValue;
    const barBg = new PIXI.Graphics();
    barBg.lineStyle(1, 0xFFFFFF, 0.5);
    barBg.beginFill(STYLE.COLORS.BAR_BACKGROUND);
    barBg.drawRoundedRect(x, y, width, height, 4);
    barBg.endFill();

    const bar = new PIXI.Graphics();
    bar.lineStyle(1, 0xFFFFFF, 0.5);
    bar.beginFill(color);
    bar.drawRoundedRect(x, y, width * percentage, height, 4);
    bar.endFill();

    const container = new PIXI.Container();
    container.addChild(barBg, bar);
    return container;
}

function createPortrait(characterOrUrl, x, y, size = 64, isDead = false) {
    const container = new PIXI.Container();
    container.x = x;
    container.y = y;

    // Handle both string URLs and character objects
    const imageUrl = typeof characterOrUrl === 'string' ? characterOrUrl : characterOrUrl.portrait;
    if (!imageUrl) return container;

    const borderRadius = 2;
    const shadow = createBasicGraphics(
        1, 1, size, size, 
        borderRadius, 0x708090, 0.5
    );

    const portrait = PIXI.Sprite.from(imageUrl);
    portrait.width = size;
    portrait.height = size;
    portrait.texture.baseTexture.scaleMode = PIXI.SCALE_MODES.NEAREST;
    portrait.roundPixels = true;

    // Apply greyscale filter if character is dead
    if (isDead) {
        const colorMatrix = new PIXI.filters.ColorMatrixFilter();
        colorMatrix.desaturate();
        colorMatrix.brightness(0.5, false);
        portrait.filters = [colorMatrix];
    }

    const mask = new PIXI.Graphics();
    mask.beginFill(0x000000);
    mask.drawRoundedRect(0, 0, size, size, borderRadius);
    mask.endFill();
    portrait.mask = mask;

    const border = new PIXI.Graphics();
    // Use active_turn border color if it's a character object, otherwise default to grey
    const borderColor = characterOrUrl.active_turn ? 0x73ffb4 : 0x708090;
    border.lineStyle(2, borderColor, 1);
    border.drawRoundedRect(0, 0, size, size, borderRadius);

    container.addChild(shadow, portrait, mask, border);
    return container;
}

function createButtonContainer(text, width = 250) {
    const buttonContainer = new PIXI.Container();
    const button = createText(text, BUTTON_STYLE, 0, 3, 0.5);

    button.style.wordWrap = true;
    button.style.wordWrapWidth = width;

    const border = createBorder(-width / 2 - 10, -button.height / 2 - 5, width + 20, button.height + 16);

    const blurSprite = createBlurSprite(width + 20, button.height + 16, -width / 2 - 10, -button.height / 2 - 5);

    buttonContainer.addChild(blurSprite, border, button);

    return buttonContainer;
}

// Add new style configuration object
const STYLE_CONFIGS = {
    default: {
        textColor: 0xFFFFFF,
        borderColor: 0xFFFFFF,
        dropShadow: false
    },
    hover: {
        textColor: 0x4dccff,
        borderColor: 0x40afdb,
        dropShadow: {
            color: 0x4dccff,
            blur: 10,
            distance: 0
        }
    },
    pressed: {
        textColor: 0x2080A0,
        borderColor: 0x2080A0,
        dropShadow: {
            color: 0x2080A0,
            blur: 5,
            distance: 0
        }
    },
    disabled: {
        textColor: 0x808080,
        borderColor: 0x808080,
        dropShadow: false
    }
};

// Generic style application function
function applyStyle(container, styleConfig, type = 'button') {
    container.children.forEach(child => {
        if (child instanceof PIXI.Text) {
            // Preserve existing text styles and merge with new ones
            const baseStyle = type === 'button' ? BUTTON_STYLE : CHARACTER_TEXT_STYLE;
            child.style = {
                ...baseStyle,
                ...child.style, // Keep existing styles including wordWrap settings
                fill: styleConfig.textColor,
                dropShadow: styleConfig.dropShadow !== false,
                dropShadowColor: styleConfig.dropShadow?.color || styleConfig.borderColor,
                dropShadowBlur: styleConfig.dropShadow?.blur || 0,
                dropShadowDistance: styleConfig.dropShadow?.distance || 0
            };
        } else if (child instanceof PIXI.Graphics) {
            child.tint = styleConfig.borderColor;
        }
    });
}

// Simplified button style functions
function applyDefaultStyleToButton(button) {
    applyStyle(button, STYLE_CONFIGS.default);
}

function applyHoverStyleToButton(button) {
    applyStyle(button, STYLE_CONFIGS.hover);
}

function applyPressedStyleToButton(button) {
    applyStyle(button, STYLE_CONFIGS.pressed);
}

// Simplified character box style functions
function applyDefaultStyleToCharacterBox(container, isDead = false) {
    applyStyle(container, isDead ? STYLE_CONFIGS.disabled : STYLE_CONFIGS.default, 'character');
}

function applyHoverStyleToCharacterBox(container, isDead = false) {
    applyStyle(container, isDead ? STYLE_CONFIGS.disabled : STYLE_CONFIGS.hover, 'character');
}

function applyPressedStyleToCharacterBox(container, isDead = false) {
    applyStyle(container, isDead ? STYLE_CONFIGS.disabled : STYLE_CONFIGS.pressed, 'character');
}

/**
 * Calculates text position and width based on container dimensions and portrait presence
 * @param {Object} params Configuration object
 * @param {number} params.containerWidth - Width of the containing box
 * @param {number} params.baseX - Base X position of the text box
 * @param {number} params.padding - Padding value
 * @param {boolean} params.hasPortrait - Whether a portrait is present
 * @param {number} [params.portraitSize] - Size of the portrait (required if hasPortrait is true)
 * @returns {Object} Object containing x position and wordWrapWidth
 */
function calculateTextPosition(params) {
    const { containerWidth, baseX, padding, hasPortrait, portraitSize } = params;
    
    if (hasPortrait) {
        return {
            x: baseX + padding * 3 + portraitSize,
            wordWrapWidth: containerWidth - portraitSize - padding * 4
        };
    }
    
    return {
        x: baseX + padding * 2,
        wordWrapWidth: containerWidth - padding * 4
    };
}

/**
 * Applies text position and width to a PIXI.Text element
 * @param {PIXI.Text} textElement - The text element to update
 * @param {Object} position - Position object from calculateTextPosition
 */
function applyTextPosition(textElement, position) {
    textElement.x = position.x;
    textElement.style.wordWrapWidth = position.wordWrapWidth;

    // Force text to rewrap
    const currentText = textElement.text;
    textElement.text = '';
    textElement.text = currentText;
}

function updateSubTextBox(app, subText, subTextBlur, subTextBorder, mainContainer, gameState) {
    const padding = LAYOUT.PADDING;
    const baseMinHeight = 95;
    const portraitSize = LAYOUT.PORTRAIT_SIZE;
    
    // Check for any portrait presence
    const hasPortrait = gameState.portrait_image_url || 
        (gameState.option_portraits && Object.keys(gameState.option_portraits).length > 0);
    const minHeight = hasPortrait ? baseMinHeight * 2 : baseMinHeight;
    
    // Get the current text and potential option details
    const currentText = gameState.sub_text || '';
    const optionDetails = gameState.option_details || [];
    const menuOptions = gameState.menu_options || [];
    
    // Find the longest possible text among:
    // 1. Current sub_text
    // 2. Option details
    // 3. Menu options themselves
    let longestText = currentText;
    
    if (gameState.input_type === 'menu') {
        // Check option details
        const longestDetail = optionDetails.reduce((longest, current) => {
            return (current && current.length > longest.length) ? current : longest;
        }, '');
        
        // Check menu options
        const longestOption = menuOptions.reduce((longest, current) => {
            return (current && current.length > longest.length) ? current : longest;
        }, '');
        
        // Compare all three to find the longest
        const candidates = [currentText, longestDetail, longestOption];
        longestText = candidates.reduce((longest, current) => {
            return (current && current.length > longest.length) ? current : longest;
        }, '');
    }
    
    // Calculate new dimensions
    const originalText = subText.text;
    subText.text = longestText;
    
    // Add extra padding for better readability
    const extraPadding = padding * 3;
    const newHeight = Math.max(minHeight, subText.height + extraPadding);
    const width = app.screen.width - (padding * 2);
    
    // Update blur sprite and border
    subTextBlur.height = newHeight;
    subTextBlur.width = width;
    subTextBlur.x = padding;
    subTextBlur.y = 80;
    
    mainContainer.removeChild(subTextBorder);
    const newBorder = createBorder(padding, 80, width, newHeight);
    mainContainer.addChild(newBorder);
    
    // Calculate and apply text position using the border's x position as baseX
    const position = calculateTextPosition({
        containerWidth: width,
        baseX: subTextBorder.x,  // Use border's x position instead of padding
        padding,
        hasPortrait,
        portraitSize
    });
    
    applyTextPosition(subText, position);
    subText.y = 100;  // Maintain vertical position
    
    // Reset text and position, accounting for portrait if present
    subText.text = originalText;
    subText.y = 100;
    
    return newBorder;
}

/**
 * Creates and positions a portrait container within a text box
 * @param {Object} params Configuration object
 * @param {number} params.x - X position of the portrait
 * @param {number} params.y - Y position of the portrait
 * @param {string} params.portraitUrl - URL of the portrait image
 * @param {number} params.size - Size of the portrait (width/height)
 * @param {boolean} params.isDead - Whether to apply dead character styling
 * @param {boolean} params.activeTurn - Whether this is the active character's turn
 * @returns {PIXI.Container} The portrait container
 */
function createSubTextPortrait(params) {
    const { x, y, portraitUrl, size = LAYOUT.PORTRAIT_SIZE } = params;
    
    if (!portraitUrl) {
        console.warn('No portrait image URL provided');
        return null;
    }

    return createPortrait(
        portraitUrl,
        x,
        y,
        size
    );
}

/**
 * Updates text box layout to accommodate a portrait
 * @param {Object} params Configuration object
 * @param {PIXI.Text} params.textElement - The text element to adjust
 * @param {number} params.boxWidth - Width of the containing box
 * @param {number} params.portraitSize - Size of the portrait
 * @param {number} params.baseX - Base X position of the text box
 * @param {number} params.padding - Padding value
 */
function adjustTextForPortrait(params) {
    const { textElement, boxWidth, portraitSize, baseX, padding } = params;
    
    const position = calculateTextPosition({
        containerWidth: boxWidth,
        baseX,
        padding,
        hasPortrait: true,
        portraitSize
    });
    
    applyTextPosition(textElement, position);
}

/**
 * Resets text element position and width when removing portrait
 * @param {Object} params Configuration object
 * @param {PIXI.Text} params.textElement - The text element to adjust
 * @param {number} params.boxWidth - Width of the containing box
 * @param {number} params.baseX - Base X position of the text box
 * @param {number} params.padding - Padding value
 */
function resetTextPosition(params) {
    const { textElement, boxWidth, baseX, padding } = params;
    
    const position = calculateTextPosition({
        containerWidth: boxWidth,
        baseX,
        padding,
        hasPortrait: false
    });
    
    applyTextPosition(textElement, position);
}

// Export all functions at the end of the file
export {
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
    truncateText,
    updateSubTextBox,
    createSubTextPortrait,
    adjustTextForPortrait,
    resetTextPosition,
};
