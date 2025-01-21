![Banner](banner.png)

# One Trillion and One Nights

An experiment in using LLMs to procedurally generate browser-based Japanese-style RPGs.

## Installation

### Prerequisites

1. **Python Installation**
   - Download and install Python 3.10 or higher from [python.org](https://python.org)
   - For Windows: Make sure to check "Add Python to PATH" during installation
   - Verify installation by running:
     ```bash
     python --version
     ```
   - Note: Python 3.10+ is required due to dependency requirements

### Setting up the Development Environment

1. **Clone the Repository**
   ```bash
   git clone https://github.com/awjuliani/dream-jrpg.git
   cd dream-jrpg
   ```

2. **Create a Virtual Environment**
   ```bash
   # Create a new virtual environment
   python -m venv dream-jrpg-env

   # Activate the virtual environment
   # On Windows:
   dream-jrpg-env\Scripts\activate
   # On macOS/Linux:
   source dream-jrpg-env/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. **Set up API Keys**
   First, set up your LLM provider API keys as environment variables:
   ```bash
   export OPENAI_API_KEY='your-api-key-here'
   export ANTHROPIC_API_KEY='your-api-key-here'
   export REPLICATE_API_TOKEN='your-api-token-here'
   export GEMINI_API_KEY='your-api-key-here'
   ```
   You can add these to your shell configuration file (e.g., `.bashrc`, `.zshrc`) or set them before running the application.

2. **Configure the Game**
   Edit `config.yaml` to customize your game experience (see Configuration section below).

3. **Start the Game**
   ```bash
   uvicorn web_main:app --host 127.0.0.1 --port 8000
   ```
   Then open your browser and navigate to `http://127.0.0.1:8000`

## Configuration

The game can be customized through `config.yaml`. Here's an example configuration:

```yaml
provider: anthropic    # LLM provider (openai/anthropic/gemini)
model_size: large     # Model size (large/small)
image_style: Retro    # Visual style (Retro/Classic/Modern/Chibi/Dark)
image_model: black-forest-labs/flux-schnell # Image model
use_cache: false      # Enable LLM response caching
cheat_mode: false     # Enable debug mode with boosted stats
```

### Available Options

#### LLM Providers (`provider`)
- `openai`
- `anthropic`
- `gemini`

#### Model Sizes (`model_size`)
- `large`
- `small`

#### Image Styles (`image_style`)
- `Retro` - 16-bit era JRPG style
- `Classic` - Traditional 90s anime style
- `Modern` - Contemporary anime style
- `Chibi` - Cute super-deformed style
- `Dark` - Dark fantasy style

#### Image Models (`image_model`)
- `black-forest-labs/flux-schnell`
- `black-forest-labs/flux-dev`

## Development

### Contributing
1. Fork the repository
2. Create a new branch for your feature
3. Make your changes
4. Submit a pull request

For bug reports or feature requests, please open an issue on GitHub.
