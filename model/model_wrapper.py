import os
import base64

from dotenv import load_dotenv
from google import genai
from google.genai import types

from model.model_output import ModelOutput


# this module wraps the llm api to make it easier to use

class Gemini(genai.Client):
    def __init__(self, model_name, temperature):

        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "Missing Gemini Api key. Please set it in .env (GEMINI_API_KEY=...)"
            )

        super().__init__(api_key=api_key)

        self.model_name = model_name
        self.temperature = temperature
        self.system_instruction = self._get_system_prompt()

        if not self.system_instruction.strip():
            print("[Gemini] WARNING: system_prompt.txt empty or not found")


    def respond(self, file_payload):
        
        response = self.models.generate_content(
            model=self.model_name,
            config=types.GenerateContentConfig(
                system_instruction=self.system_instruction,
                temperature=self.temperature,
            ),
            contents=[
                types.Part.from_bytes(
                    data=file_payload['file_data'], mime_type="application/pdf"
                )
            ],
        )
        # print(response.text)
        text_out = getattr(response, "text", None) or ""
        date_out = file_payload['date']

        return ModelOutput.from_raw(raw_model_text=text_out, date=date_out)

    def _get_system_prompt(self) -> str:
        here = os.path.dirname(os.path.abspath(__file__)) # this file's dir
        path = os.path.join(here, "system_prompt.txt")
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return ""
