import os
import json
import time
import google.generativeai as genai
from abc import ABC, abstractmethod
from typing import Any, Dict

try:
    from llama_cpp import Llama
except ImportError:
    Llama = None

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception
)

# -------------------------------
# Base Provider Interface
# -------------------------------

class LLMProvider(ABC):
    @abstractmethod
    def generate_text(self, prompt: str) -> str:
        pass

    @abstractmethod
    def generate_json(self, prompt: str) -> Dict[str, Any]:
        pass


# -------------------------------
# Retry Filter (DO NOT retry 429)
# -------------------------------

def is_retryable_error(e: Exception) -> bool:
    return "429" not in str(e)


# -------------------------------
# Gemini Provider
# -------------------------------

class GeminiProvider(LLMProvider):
    def __init__(self, model_name: str = "gemini-1.5-flash"):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables.")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        retry=retry_if_exception(is_retryable_error)
    )
    def generate_text(self, prompt: str) -> str:
        try:
            time.sleep(0.3)  # throttle free-tier usage
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            if "429" in str(e):
                print("Gemini quota exceeded. Skipping retry.")
            else:
                print(f"Gemini Text Generation Error: {e}")
            return "Thinking process interrupted."

    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        retry=retry_if_exception(is_retryable_error)
    )
    def generate_json(self, prompt: str) -> Dict[str, Any]:
        try:
            json_prompt = (
                "You are a JSON generator.\n"
                "Return ONLY valid JSON.\n"
                "No explanation. No markdown.\n\n"
                + prompt
            )
            time.sleep(0.3)  # throttle free-tier usage
            response = self.model.generate_content(json_prompt)
            return self._parse_json(response.text)
        except Exception as e:
            if "429" in str(e):
                print("Gemini quota exceeded. Skipping retry.")
            else:
                print(f"Gemini JSON Generation Error: {e}")
            return {}

    def _parse_json(self, text: str) -> Dict[str, Any]:
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}") + 1
            if start != -1 and end != -1:
                try:
                    return json.loads(text[start:end])
                except Exception:
                    pass
            return {}


# -------------------------------
# Local LLaMA Provider
# -------------------------------

class LlamaLocalProvider(LLMProvider):
    def __init__(self, model_path: str):
        if Llama is None:
            raise ImportError("llama-cpp-python is not installed.")

        print(f"Loading local model from {model_path}...")
        self.llm = Llama(
            model_path=model_path,
            n_gpu_layers=-1,
            n_ctx=4096,
            verbose=False
        )

    def generate_text(self, prompt: str) -> str:
        formatted_prompt = (
            "<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n\n"
            f"{prompt}"
            "<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"
        )

        output = self.llm(
            formatted_prompt,
            max_tokens=512,
            stop=["<|eot_id|>"],
            echo=False
        )
        return output["choices"][0]["text"].strip()

    def generate_json(self, prompt: str) -> Dict[str, Any]:
        json_prompt = prompt + "\n\nRespond strictly with valid JSON."
        formatted_prompt = (
            "<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n\n"
            f"{json_prompt}"
            "<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"
        )

        output = self.llm(
            formatted_prompt,
            max_tokens=512,
            stop=["<|eot_id|>"],
            echo=False
        )

        return self._parse_json(output["choices"][0]["text"].strip())

    def _parse_json(self, text: str) -> Dict[str, Any]:
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}") + 1
            if start != -1 and end != -1:
                try:
                    return json.loads(text[start:end])
                except Exception:
                    pass
            return {}


# -------------------------------
# Factory
# -------------------------------

class LLMFactory:
    _instances = {}

    @staticmethod
    def get_provider(provider_type: str, **kwargs) -> LLMProvider:
        if provider_type == "gemini":
            if "gemini" not in LLMFactory._instances:
                LLMFactory._instances["gemini"] = GeminiProvider()
            return LLMFactory._instances["gemini"]

        elif provider_type == "llama_local":
            model_path = kwargs.get(
                "model_path",
                os.path.join(
                    os.getcwd(),
                    "models/Llama-3.2-3B-Instruct-Q4_K_M.gguf"
                )
            )

            key = f"llama_{model_path}"
            if key not in LLMFactory._instances:
                LLMFactory._instances[key] = LlamaLocalProvider(model_path)
            return LLMFactory._instances[key]

        else:
            raise ValueError(f"Unknown provider type: {provider_type}")
