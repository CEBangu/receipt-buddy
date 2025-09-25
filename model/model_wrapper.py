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
    
        self.model = genai.Client(api_key=api_key)
        self.model_name = model_name
        self.temperature = temperature
        self.system_instruction = self._get_system_prompt()


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
            ]
        )

        text_out = response.text
        date_out = file_payload['date']

        return ModelOutput.from_raw(raw_model_text=text_out, date=date_out)

    def _get_system_prompt(self,) -> None:
        system_prompt_path = self._get_system_prompt_path()

        with open(system_prompt_path, "r", encoding="utf-8") as f:
            self.system_instruction = f.read()
    
    def _get_system_prompt_path(self):
        cwd = os.getcwd()
        system_prompt_path = os.path.join(cwd, "system_prompt.txt")
        return system_prompt_path
