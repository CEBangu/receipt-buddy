import os
from typing import List, Tuple

from email_service.email_grabber import EmailGrabber

def write_checkpoint(cwd: str, final_payload):
    """
    This function writes a checkpoint file st. only emails after that timestamp are read in.  
    """
    


def read_checkpoint(cwd:str):
    """
    This funciton reads in the the checkpoint file to hand off the right query string to the EmailGrabber
    """
    pass

def get_ms_date(api_payload):
    pass

