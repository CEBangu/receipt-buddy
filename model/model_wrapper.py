import os
import base64

from datetime import datetime
from google import genai
from google.genai import types
from typing import List, Dict, Tuple

from model.model_output import ModelOutput


# this module wraps the llm api to make it easier to use

class Gemini(genai.Client):
    def __init__(self, model_name, temperature):
        
        self.model = genai.Client()
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

    #TODO: Not entirely sure this is how I want to handle this ... 
    # It might make more sense to have this be part of the MailGrabber class
    def _ingest_data(self, attachment_date: Dict) -> Tuple[str, datetime]:
        """
        This function takes in dictionary with the attachment to decode, and its date, and 
        feeds it to the model
        """
        attachment = attachment_date['data']
        date = attachment_date['date']
        file_data = base64.urlsafe_b64decode(attachment.encode("UTF-8"))

        return file_data, date

    def _get_system_prompt(self,) -> None:
        system_prompt_path = self._get_system_prompt_path()

        with open(system_prompt_path, "r", encoding="utf-8") as f:
            self.system_instruction = f.read()
    
    def _get_system_prompt_path(self):
        cwd = os.getcwd()
        system_prompt_path = os.path.join(cwd, "system_prompt.txt")
        return system_prompt_path
