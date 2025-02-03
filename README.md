![Banner](banner.png)

# One Trillion and One Nights

One Trillion and One Nights is a browser-based JRPG that uses artificial intelligence to create unique, dynamic gaming experiences. The game procedurally generates:
- Engaging storylines and quests
- Character dialogues and personalities
- Beautiful anime-style artwork
- Turn-based combat encounters
- Dynamic world exploration

To learn more about the making of this project, you can read my [Medium article](https://medium.com/p/e215d82f53e2).

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

1. **Configure the Game**
   Create a copy of `config.yaml.example` as `.config.yaml` and customize your game experience (see Configuration section below).

2. **Start the Game**
   ```bash
   uvicorn web_main:app --host 127.0.0.1 --port 8000
   ```
   Then open your browser and navigate to `http://127.0.0.1:8000`

## Configuration

The game requires configuration through `.config.yaml`. Here's a detailed example:

```yaml
# LLM Config
llm_provider: openai
llm_model_id: gpt-4o
llm_endpoint: https://api.openai.com/v1
llm_api_key: "<your-api-key>"

# Image Model Config
image_model: black-forest-labs/flux-schnell
image_api_key: "<your-api-key>"
image_style: Modern

# Miscellaneous Config
use_cache: false
cheat_mode: false
```

### Configuration Details

#### LLM Configuration
Multiple LLM providers are supported. The default is OpenAI. To use a different provider, change the `llm_provider` to the desired provider. For each provider, you will need to set the `llm_model_id`, `llm_endpoint`, and `llm_api_key`.

- `llm_provider`: The LLM service provider.
  - `openai`: OpenAI
  - `anthropic`: Anthropic
  - `gemini`: Google Gemini
  - `universal`: Universal (Groq, OpenRouter, etc.)
- `llm_model_id`: The specific model to use
- `llm_endpoint`: API endpoint URL (when using Universal)
- `llm_api_key`: Your API key for the LLM service

#### Image Configuration
Image generation is currently handled by Replicate. In order to use this, you will need to create an account and get an API key. To do so, go to https://replicate.com/ and sign up.

- `image_model`: The model to use for image generation
- `image_api_key`: Your API key for the image service
- `image_style`: Visual style for generated images
  - `Modern` - Contemporary anime style
  - `Classic` - Traditional 90s anime style
  - `Retro` - 16-bit era JRPG style
  - `Chibi` - Cute super-deformed style
  - `Dark` - Dark fantasy style

#### Miscellaneous Options
- `use_cache`: Enable/disable LLM response caching (true/false)
- `cheat_mode`: Enable debug mode with boosted stats (true/false)

## Development

### Contributing
1. Fork the repository
2. Create a new branch for your feature
3. Make your changes
4. Submit a pull request

For bug reports or feature requests, please open an issue on GitHub.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
