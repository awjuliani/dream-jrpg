from abc import ABC, abstractmethod
import json
from typing import Dict, Any
import time


# Abstract Base Class for LLM Providers
class LLMProvider(ABC):
    def __init__(self, model_id: str = None, api_key: str = None):
        self.api_key = api_key
        if not self.api_key:
            raise ValueError(
                "API key must be provided either through constructor or environment variable"
            )
        self.use_model = model_id if model_id else self.get_default_model()
        self.client = self._initialize_client()

    @abstractmethod
    def get_default_model(self) -> str:
        """Return the default model name if none is specified."""
        pass

    @abstractmethod
    def _initialize_client(self):
        """Initialize and return the client for the LLM provider."""
        pass

    @abstractmethod
    def _create_response(self, prompt: str, system_message: str) -> str:
        """Create a response based on the prompt and system message."""
        pass

    def _extract_json(self, text: str) -> str:
        """Extract JSON from text that might contain additional content."""
        json_start = text.find("{")
        json_end = text.rfind("}") + 1
        if json_start == -1 or json_end == 0:
            return text  # Return original text if no JSON found
        return text[json_start:json_end]

    def _process_response(self, response: str) -> str:
        """Process and clean up the response text."""
        return self._extract_json(response)

    def generate(
        self, prompt: str, system_message: str, max_retries: int = 3
    ) -> Dict[str, Any]:
        last_error = None
        for attempt in range(max_retries):
            try:
                response = self._create_response(prompt, system_message)
                processed_response = self._process_response(response)
                return json.loads(processed_response)
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    time.sleep(1)
                continue

        raise Exception(
            f"Failed to generate response after {max_retries} attempts. Last error: {last_error}"
        )


# New abstract class for chat-based providers to reduce duplication
class ChatProvider(LLMProvider):
    def _build_messages(self, prompt: str, system_message: str) -> list:
        return [
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt},
        ]

    def _create_response(self, prompt: str, system_message: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.use_model,
                response_format={"type": "json_object"},
                messages=self._build_messages(prompt, system_message),
            )
            return response.choices[0].message.content
        except AttributeError:
            # Fallback for providers that do not support chat completions
            response = self.client.completions.create(
                model=self.use_model,
                prompt=f"{system_message}\n\nUser: {prompt}\n\nAssistant:",
                response_format={"type": "json_object"},
            )
            return response.choices[0].text


# OpenAI Provider Implementation using ChatProvider
class OpenAIProvider(ChatProvider):
    def __init__(self, api_key: str = None, model_id: str = None):
        super().__init__(model_id=model_id, api_key=api_key)

    def get_default_model(self) -> str:
        return "gpt-4o"

    def _initialize_client(self):
        from openai import OpenAI

        return OpenAI(api_key=self.api_key)


# Anthropic Provider Implementation
class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str = None, model_id: str = None):
        super().__init__(model_id=model_id, api_key=api_key)

    def get_default_model(self) -> str:
        return "claude-3-5-sonnet-latest"

    def _initialize_client(self):
        from anthropic import Anthropic

        return Anthropic(api_key=self.api_key)

    def _create_response(self, prompt: str, system_message: str) -> str:
        response = self.client.messages.create(
            model=self.use_model,
            max_tokens=8192,
            system=system_message,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text


# Gemini Provider Implementation
class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str = None, model_id: str = None):
        super().__init__(model_id=model_id, api_key=api_key)

    def get_default_model(self) -> str:
        return "gemini-1.5-flash"

    def _initialize_client(self):
        import google.generativeai as genai

        genai.configure(api_key=self.api_key)
        return genai.GenerativeModel(self.use_model)

    def _create_response(self, prompt: str, system_message: str) -> str:
        self.client.system_instruction = system_message
        response = self.client.generate_content(
            contents=prompt,
            generation_config={"response_mime_type": "application/json"},
        )
        return response.text


# Universal Provider Implementation using ChatProvider
class UniversalProvider(ChatProvider):
    def __init__(self, api_base: str = None, api_key: str = None, model_id: str = None):
        self.api_base = api_base
        super().__init__(model_id=model_id, api_key=api_key)

    def get_default_model(self) -> str:
        return "llama-3.3-70b-specdec"

    def _initialize_client(self):
        from openai import OpenAI

        client_kwargs = {"api_key": self.api_key}
        if self.api_base:
            client_kwargs["base_url"] = self.api_base
        return OpenAI(**client_kwargs)
