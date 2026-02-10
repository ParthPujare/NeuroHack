import os
import json
import google.generativeai as genai
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

try:
    from llama_cpp import Llama
except ImportError:
    Llama = None

class LLMProvider(ABC):
    @abstractmethod
    def generate_text(self, prompt: str) -> str:
        """Generates natural language text."""
        pass

    @abstractmethod
    def generate_json(self, prompt: str) -> Dict[str, Any]:
        """Generates a JSON object."""
        pass

class GeminiProvider(LLMProvider):
    def __init__(self, model_name: str = "gemini-flash-latest"):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables.")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
    
    def generate_text(self, prompt: str) -> str:
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"Gemini Text Generation Error: {e}")
            return "Thinking process interrupted."

    def generate_json(self, prompt: str) -> Dict[str, Any]:
        try:
            # Force JSON response via prompt engineering
            json_prompt = prompt + "\n\nRespond strictly with valid JSON. Do not include markdown formatting."
            response = self.model.generate_content(json_prompt)
            return self._parse_json(response.text)
        except Exception as e:
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
            # Fallback: find first { and last }
            start = text.find('{')
            end = text.rfind('}') + 1
            if start != -1 and end != -1:
                try:
                    return json.loads(text[start:end])
                except:
                    pass
            return {}

class LlamaLocalProvider(LLMProvider):
    def __init__(self, model_path: str):
        if Llama is None:
            raise ImportError("llama-cpp-python is not installed.")
        
        # Initialize Llama model
        # n_ctx=4096 to check context window requirements
        # n_gpu_layers=-1 to offload all to GPU (Metal on Mac)
        print(f"Loading local model from {model_path}...")
        self.llm = Llama(
            model_path=model_path,
            n_gpu_layers=-1, # Auto-detect GPU/Metal
            n_ctx=4096,
            verbose=False
        )
    
    def generate_text(self, prompt: str) -> str:
        # Llama 3 format
        formatted_prompt = f"<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n\n{prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"
        
        output = self.llm(
            formatted_prompt,
            max_tokens=512,
            stop=["<|eot_id|>"],
            echo=False
        )
        return output['choices'][0]['text'].strip()

    def generate_json(self, prompt: str) -> Dict[str, Any]:
        # Llama 3 format with JSON instruction
        json_prompt = prompt + "\n\nRespond strictly with valid JSON."
        formatted_prompt = f"<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n\n{json_prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"
        
        output = self.llm(
            formatted_prompt,
            max_tokens=512,
            stop=["<|eot_id|>"],
            echo=False
        )
        text = output['choices'][0]['text'].strip()
        return self._parse_json(text)

    def _parse_json(self, text: str) -> Dict[str, Any]:
        # Reuse simple parsing logic
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            start = text.find('{')
            end = text.rfind('}') + 1
            if start != -1 and end != -1:
                try:
                    return json.loads(text[start:end])
                except:
                    pass
            return {}

class LLMFactory:
    _instances = {}

    @staticmethod
    def get_provider(provider_type: str, **kwargs) -> LLMProvider:
        if provider_type == "gemini":
            if "gemini" not in LLMFactory._instances:
                LLMFactory._instances["gemini"] = GeminiProvider()
            return LLMFactory._instances["gemini"]
        
        elif provider_type == "llama_local":
            model_path = kwargs.get("model_path")
            if not model_path:
                # Default path
                model_path = os.path.join(os.getcwd(), "models/Llama-3.2-3B-Instruct-Q4_K_M.gguf")
            
            key = f"llama_{model_path}"
            if key not in LLMFactory._instances:
                LLMFactory._instances[key] = LlamaLocalProvider(model_path)
            return LLMFactory._instances[key]
        
        else:
            raise ValueError(f"Unknown provider type: {provider_type}")
