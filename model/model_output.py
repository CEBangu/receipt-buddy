import json
import re

from typing import List, Tuple, Any
from datetime import datetime
from google import genai
from google.genai import types
from pydantic import BaseModel


# This module contatins model wrapping code. It handles both the ingest in GeminiWrapper and output in ModelOutput

class Row(BaseModel):
    """
    This class handles the structure of row that will be written to the excel notebook.
    """
    item: str
    quantity: int
    price: float
    price_per_unit: float
    date: datetime


class ModelOutput(BaseModel):
    raw: str
    rows: List[Row]

    @staticmethod
    def _strip_fences(s: str) -> str:
        """
        The model likes to couch its json in markdown and also put json on the top.
        so this funciton deals with that.
        """
        return re.sub(r"^```(?:json)?|```$", "", s.strip(), flags=re.MULTILINE).strip()
    
    @staticmethod
    def _to_float(x: Any):
        """
        This function converts ints to floats for the prices in case the model messes it up.
        """
        if x is None: return None
        if isinstance(x, (int, float)): return float(x)
        # and in case it uses commas instead of periods:
        s = str(x).strip().replace(",", ".")
        return float(s)

    @classmethod
    def from_raw(cls, raw_model_text: str, date: datetime) -> "ModelOutput":
        clean = cls._strip_fences(raw_model_text)
        json_obj = json.loads(clean)
        
        rows = []
        for item, quant_price in json_obj.items():
            try:
                qty = int(quant_price['quantity'])
            except KeyError:
                return(f"Key 'quantity' not found for {item} in json object. Try again")
            try:
                price = cls._to_float(quant_price['price'])
            except KeyError:
                return(f"Key 'price' not found for {item} in json object. Try again")
        
            rows.append(Row(
                item=item,
                quantity= qty,
                price=price,
                price_per_unit=price/qty if qty else 0.0,
                date=date
            ))
        return cls(raw=raw_model_text, rows=rows)

#TODO: ModelOutputError