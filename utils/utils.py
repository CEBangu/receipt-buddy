import os
import json
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow


def write_checkpoint(path: str, ms: int):
    """
    This function writes a checkpoint file st. only emails after that timestamp are read in. 
    """
    state = {"last_internal_ms": ms}
    with open(path, "w") as f:
        json.dump(state, f)

    
def read_checkpoint(path: str):
    """
    This funciton reads in the the checkpoint file to hand off the right query string to the EmailGrabber
    """
    try:
        with open(path) as f:
            state = json.load(f)
            return int(state.get("last_internal_ms", 0))
    except FileNotFoundError:
        return 0
    except (json.JSONDecodeError, ValueError):
        return 0


def setup(SCOPES: str):
  """
  This funciton is copied from Google quickstart.py file to make sure that the API 
  works for the user.
  """
  creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          "credentials.json", SCOPES
      )
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
      token.write(creds.to_json())
      
  return creds