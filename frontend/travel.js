import { createButtonContainer } from './ui_helpers.js';
import { LAYOUT } from './constants.js';

export class TravelRenderer {
    constructor(app, menuContainer) {
        this.app = app;
        this.menuContainer = menuContainer;
        this.menuButtons = [];
    }

    render(gameState, attachButtonEvents) {
        this.clearMenuOptions();
        const options = gameState.menu_options || [];
        console.log(options);
        // Create containers for different button types
        const directionAndTravelButtons = options.filter(opt => 
            ['North', 'South', 'East', 'West'].includes(opt) ||
            opt.startsWith('Travel to ')
        );
        console.log(directionAndTravelButtons);
        const centerButton = options.find(opt => 
            !['North', 'South', 'East', 'West'].includes(opt) && 
            !opt.startsWith('Travel to ') &&
            opt !== 'Save and Exit' && 
            opt !== 'Party Menu');
        const utilityButtons = {
            save: options.find(opt => opt === 'Save and Exit'),
            party: options.find(opt => opt === 'Party Menu')
        };

        // Set up compass dimensions
        const compassCenter = {
            x: this.app.screen.width / 2,
            y: this.app.screen.height / 2 + 120
        };
        const compassRadius = LAYOUT.COMPASS.RADIUS;

        // Direction button positions
        const directionPositions = {
            'North': { x: 0, y: -1.25, symbol: '↑' },
            'South': { x: 0, y: 1.25, symbol: '↓' },
            'East': { x: 2.25, y: 0, symbol: '→' },
            'West': { x: -2.25, y: 0, symbol: '←' },
        };

        // Render direction and travel buttons
        directionAndTravelButtons.forEach((option) => {
            // Check if this is a travel option
            const isTravelOption = option.startsWith('Travel to ');
            // Extract direction from travel option or use regular direction
            const direction = isTravelOption ? 
                Object.keys(directionPositions).find(dir => 
                    !directionAndTravelButtons.includes(dir)
                ) : option;

            if (directionPositions[direction]) {
                const buttonText = `${directionPositions[direction].symbol}\n${
                    isTravelOption ? option : gameState.movement_text[direction]
                }`;
                
                const buttonContainer = createButtonContainer(buttonText, LAYOUT.BUTTON.DIRECTION_WIDTH);
                const pos = directionPositions[direction];
                buttonContainer.x = compassCenter.x + (pos.x * compassRadius);
                buttonContainer.y = compassCenter.y + (pos.y * compassRadius);
                
                buttonContainer.isDirectionButton = true;
                buttonContainer.optionIndex = options.indexOf(option);
                
                attachButtonEvents(buttonContainer, option);
                
                this.menuButtons.push(buttonContainer);
                this.menuContainer.addChild(buttonContainer);
            }
        });

        // Render center button if it exists
        if (centerButton) {
            const buttonContainer = createButtonContainer(centerButton, LAYOUT.BUTTON.CENTER_WIDTH);
            buttonContainer.x = compassCenter.x;
            buttonContainer.y = compassCenter.y;
            
            attachButtonEvents(buttonContainer, centerButton);
            
            this.menuButtons.push(buttonContainer);
            this.menuContainer.addChild(buttonContainer);
        }

        // Render utility buttons
        if (utilityButtons.save) {
            const saveButton = createButtonContainer(utilityButtons.save, 150);
            saveButton.x = this.app.screen.width - 150;
            saveButton.y = this.app.screen.height - 40;
            
            attachButtonEvents(saveButton, utilityButtons.save);
            
            this.menuButtons.push(saveButton);
            this.menuContainer.addChild(saveButton);
        }

        if (utilityButtons.party) {
            const partyButton = createButtonContainer(utilityButtons.party, 150);
            partyButton.x = 150;
            partyButton.y = this.app.screen.height - 40;
            
            attachButtonEvents(partyButton, utilityButtons.party);
            
            this.menuButtons.push(partyButton);
            this.menuContainer.addChild(partyButton);
        }

        // Add position grid in upper right corner
        if (gameState.travel_position) {
            const gridSize = 3;
            const circleRadius = 9;
            const spacing = circleRadius * 2.5;
            const padding = 15;
            const startX = this.app.screen.width - (spacing * gridSize) - padding + circleRadius; // 20px padding from right
            const startY = padding; // 20px padding from top
            
            // Create grid of circles
            for (let row = 0; row < gridSize; row++) {
                for (let col = 0; col < gridSize; col++) {
                    const circle = new PIXI.Graphics();
                    const isPlayerPosition = 
                        row === gameState.travel_position[0] && 
                        col === gameState.travel_position[1];
                    
                    // Add white border first
                    circle.lineStyle(2, 0xFFFFFF, 0.75);  // width: 2, color: white, alpha: 0.5
                    
                    // Then fill the circle
                    circle.beginFill(isPlayerPosition ? 0x4dccff : 0x000000);
                    circle.alpha = isPlayerPosition ? 0.8 : 0.5;
                    circle.drawCircle(0, 0, circleRadius);
                    circle.endFill();
                    
                    circle.x = startX + (col * spacing);
                    circle.y = startY + (row * spacing);
                    
                    this.menuContainer.addChild(circle);
                }
            }
        }

        return this.menuButtons;
    }

    clearMenuOptions() {
        this.menuButtons = [];
        this.menuContainer.removeChildren();
    }
}
