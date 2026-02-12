import os
import json
import time
from google import genai
from google.genai import types
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
import groq

# -------------------------------
# Base Provider Interface
# -------------------------------

class LLMProvider(ABC):
    @abstractmethod
    def generate_text(self, prompt: str, **kwargs) -> str:
        pass

    @abstractmethod
    def generate_json(self, prompt: str) -> Dict[str, Any]:
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
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
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables.")

        self.client = genai.Client(api_key=api_key)
        self._model_name = model_name

    @property
    def provider_name(self) -> str:
        return f"Gemini ({self._model_name})"

    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        retry=retry_if_exception(is_retryable_error)
    )
    def generate_text(self, prompt: str, **kwargs) -> str:
        try:
            time.sleep(0.3)  # throttle free-tier usage
            
            tool_config = None
            tools_arg = kwargs.get('tools')
            
            # Simple mapping: if user passed 'google_search', use the proper tool type
            # Or if they passed the dict {'google_search': {}} from previous step
            if tools_arg:
                # We interpret any truthy tool arg (that isn't empty) as a request for google search 
                # if it matches our known key, or we just enable it if requested.
                # Pipeline passes: {'google_search': {}} or similar.
                
                # Check for our specific flag or dict key
                use_search = False
                if isinstance(tools_arg, dict) and 'google_search' in tools_arg:
                    use_search = True
                elif tools_arg == 'google_search':
                    use_search = True
                
                if use_search:
                     tool_config = [types.Tool(google_search=types.GoogleSearch())]

            response = self.client.models.generate_content(
                model=self._model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=tool_config
                )
            )
            
            if kwargs.get('return_full_response'):
                metadata = None
                if response.candidates and response.candidates[0].grounding_metadata:
                    gm = response.candidates[0].grounding_metadata
                    chunks = []
                    if gm.grounding_chunks:
                        for chunk in gm.grounding_chunks:
                            if chunk.web:
                                chunks.append({
                                    "title": chunk.web.title,
                                    "url": chunk.web.uri
                                })
                    metadata = {"chunks": chunks}
                
                return {
                    "text": response.text,
                    "grounding_metadata": metadata
                }
                
            return response.text
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg:
                print(f"CRITICAL: Gemini quota exceeded (429): {error_msg}")
                return "System limited: Gemini API quota exceeded. Please wait a moment."
            else:
                print(f"Gemini Text Generation Error: {error_msg}")
                return f"Thinking process interrupted: {error_msg}"

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
            response = self.client.models.generate_content(
                model=self._model_name,
                contents=json_prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
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
# Groq Provider
# -------------------------------

class GroqProvider(LLMProvider):
    def __init__(self, model_name: str = "llama-3.3-70b-versatile"):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables.")

        self.client = groq.Groq(api_key=api_key)
        self.model = model_name

    @property
    def provider_name(self) -> str:
        return f"Groq ({self.model})"

    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        retry=retry_if_exception(is_retryable_error)
    )
    def generate_text(self, prompt: str, **kwargs) -> str:
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                model=self.model,
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            if "429" in str(e):
                print("Groq quota exceeded. Skipping retry.")
            else:
                print(f"Groq Text Generation Error: {e}")
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
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": json_prompt,
                    }
                ],
                model=self.model,
                response_format={"type": "json_object"},
            )
            return json.loads(chat_completion.choices[0].message.content)
        except Exception as e:
            if "429" in str(e):
                print("Groq quota exceeded. Skipping retry.")
            else:
                print(f"Groq JSON Generation Error: {e}")
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
        self._model_path = model_path

    @property
    def provider_name(self) -> str:
        return f"Local Llama ({os.path.basename(self._model_path)})"

    def generate_text(self, prompt: str, **kwargs) -> str:
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

        elif provider_type == "groq":
            if "groq" not in LLMFactory._instances:
                LLMFactory._instances["groq"] = GroqProvider()
            return LLMFactory._instances["groq"]



        else:
            raise ValueError(f"Unknown provider type: {provider_type}")
