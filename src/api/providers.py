from abc import ABC, abstractmethod
import json
import os
from typing import Dict, Any
import time


# Abstract Base Class for LLM Providers
class LLMProvider(ABC):
    def __init__(self, model_size: str = "small"):
        self.model_size = model_size
        self.use_model = self.get_model_name()
        self.client = self._initialize_client()

    @abstractmethod
    def set_model_names(self) -> Dict[str, str]:
        """Return a dictionary mapping model sizes to model names."""
        pass

    @abstractmethod
    def _initialize_client(self):
        """Initialize and return the client for the LLM provider."""
        pass

    @abstractmethod
    def _create_response(self, prompt: str, system_message: str) -> str:
        """Create a response based on the prompt and system message."""
        pass

    def get_model_name(self) -> str:
        """Retrieve the model name based on the selected model size."""
        models = self.set_model_names()
        return models.get(self.model_size, models["small"])

    def generate(
        self, prompt: str, system_message: str, max_retries: int = 3
    ) -> Dict[str, Any]:
        last_error = None
        for attempt in range(max_retries):
            try:
                response = self._create_response(prompt, system_message)
                return json.loads(response)
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:  # Don't sleep on the last attempt
                    time.sleep(1)
                continue

        raise Exception(
            f"Failed to generate response after {max_retries} attempts. Last error: {last_error}"
        )


# OpenAI Provider Implementation
class OpenAIProvider(LLMProvider):
    def set_model_names(self) -> Dict[str, str]:
        return {"small": "gpt-4o-mini", "large": "gpt-4o-2024-11-20"}

    def _initialize_client(self):
        from openai import OpenAI

        return OpenAI()

    def _create_response(self, prompt: str, system_message: str) -> str:
        response = self.client.chat.completions.create(
            model=self.use_model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content


# Anthropic Provider Implementation
class AnthropicProvider(LLMProvider):
    def set_model_names(self) -> Dict[str, str]:
        return {
            "small": "claude-3-5-haiku-latest",
            "large": "claude-3-5-sonnet-latest",
        }

    def _initialize_client(self):
        from anthropic import Anthropic

        return Anthropic()

    def _create_response(self, prompt: str, system_message: str) -> str:
        response = self.client.messages.create(
            model=self.use_model,
            max_tokens=8192,
            system=system_message,
            messages=[{"role": "user", "content": prompt}],
        )
        json_start = response.content[0].text.find("{")
        json_end = response.content[0].text.rfind("}") + 1
        return response.content[0].text[json_start:json_end]


# Gemini Provider Implementation
class GeminiProvider(LLMProvider):
    def set_model_names(self) -> Dict[str, str]:
        return {"small": "gemini-1.5-flash-002", "large": "gemini-2.0-flash-exp"}

    def _initialize_client(self):
        import google.generativeai as genai

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise EnvironmentError("GEMINI_API_KEY environment variable not set.")
        genai.configure(api_key=api_key)
        return genai.GenerativeModel(self.use_model)

    def _create_response(self, prompt: str, system_message: str) -> str:
        self.client.system_instruction = system_message
        response = self.client.generate_content(
            contents=prompt,
            generation_config={"response_mime_type": "application/json"},
        )
        return response.text
