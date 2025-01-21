export const RESOLUTION = window.devicePixelRatio || 1;

export const TEXT_STYLE = {
    fontFamily: 'Helvetica',
    fontSize: 36,
    fill: 0xFFFFFF,
    align: 'left',
    wordWrap: true,
    wordWrapWidth: 750,
    resolution: RESOLUTION,
    letterSpacing: 1,
    padding: 4
};

export const SUB_TEXT_STYLE = {
    ...TEXT_STYLE,
    fontSize: 22,
    fill: 0xFFFFFF,
    wordWrapWidth: 700,
    wordWrap: true,
    lineHeight: 33
};

export const DIALOGUE_TEXT_STYLE = {
    ...SUB_TEXT_STYLE,
    fontStyle: 'italic'
};

export const MINI_TEXT_STYLE = {
    ...TEXT_STYLE,
    fontSize: 26,
    fill: 0xFFFFFF,
    wordWrapWidth: 400,
    wordWrap: true,
    lineHeight: 24
};

export const PLAYER_CHARACTER_TEXT_STYLE = {
    ...TEXT_STYLE,
    fontSize: 20,
    fill: 0xFFFFFF
};

export const ENEMY_CHARACTER_TEXT_STYLE = {
    ...TEXT_STYLE,
    fontSize: 16,
    fill: 0xFFFFFF
};

export const CHARACTER_TEXT_STYLE = {
    ...TEXT_STYLE,
    fontSize: 16,
    fill: 0xFFFFFF
};

export const LOADING_TEXT_STYLE = {
    ...TEXT_STYLE,
    fontSize: 36
};

export const BUTTON_STYLE = {
    fontFamily: 'Helvetica',
    fontSize: 18,
    fill: 0xFFFFFF,
    align: 'center',
    wordWrap: true,
    wordWrapWidth: 250,
};

export const HOVER_STYLE = {
    ...BUTTON_STYLE,
    fill: 0x4dccff,
    dropShadow: true,
    dropShadowColor: 0x4dccff,
    dropShadowBlur: 10,
    dropShadowDistance: 0
};

export const PRESSED_STYLE = {
    ...BUTTON_STYLE,
    fill: 0x2080A0, // Darker shade of blue
    dropShadow: true,
    dropShadowColor: 0x2080A0,
    dropShadowBlur: 5,
    dropShadowDistance: 0
};

// Layout constants
export const LAYOUT = {
    PADDING: 20,
    PORTRAIT_SIZE: 150,
    BUTTON: {
        DEFAULT_WIDTH: 250,
        DIRECTION_WIDTH: 200,
        CENTER_WIDTH: 125,
        BATTLE_WIDTH: 75,
        HEIGHT: 50
    },
    COMPASS: {
        RADIUS: 100
    }
};

// Style constants
export const STYLE = {
    BLUR: {
        INTENSITY: 10,
        ALPHA: 0.8
    },
    BORDER: {
        RADIUS: 10,
        WIDTH: 2
    },
    COLORS: {
        ACTIVE_TURN: 0x73ffb4,
        BORDER_DEFAULT: 0xFFFFFF,
        BORDER_INACTIVE: 0x708090,
        BACKGROUND: 0x000000,
        HP_BAR: 0x66CC66,
        MP_BAR: 0x6699CC,
        SP_BAR: 0xffcc00,
        BAR_BACKGROUND: 0x333333
    }
};

// Window constants
export const WINDOW = {
    DEFAULT_WIDTH: 1280,
    DEFAULT_HEIGHT: 720
};
