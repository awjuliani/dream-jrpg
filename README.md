![Banner](banner.png)

# One Trillion and One Nights

An experiment in using LLMs to procedurally generate browser-based Japanese-style RPGs.

## Web launch command
`uvicorn web_main:app --host 127.0.0.1 --port 8000`

## Requirements
`pip install -r requirements.txt`

## Config

`config.yaml` is used to configure the game.

* `provider`: The LLM provider to use. Currently supported: 
    * `openai`
    * `anthropic`
    * `gemini`
* `model_size`: The size of the model to use. Currently supported: 
    * `large`
    * `small`
* `image_style`: The style of the image to generate. Currently supported: 
    * `Retro`
    * `Classic`
    * `Modern`
    * `Chibi`
    * `Dark`
* `image_model`: The model to use for image generation. Currently supported: 
    * `black-forest-labs/flux-schnell`
    * `black-forest-labs/flux-dev`
* `use_cache`: Whether to use caching for the LLM calls in the game. Useful for debugging.
* `cheat_mode`: Whether to enable cheat mode for the game. This increases the player's stats and gives them special abilities. Useful for debugging.

## Adding LLM provider API keys
To use different LLM providers, you'll need to set up the following environment variables:

```bash
export OPENAI_API_KEY='your-api-key-here'
export ANTHROPIC_API_KEY='your-api-key-here'
export REPLICATE_API_TOKEN='your-api-token-here'
export GEMINI_API_KEY='your-api-key-here'
```

You can add these to your shell configuration file (e.g., `.bashrc`, `.zshrc`) or set them before running the application.
