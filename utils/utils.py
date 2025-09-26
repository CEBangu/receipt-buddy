import os
import json
import time
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

####################
# dealing with free-tier gemini rate limits
#####################

RATE_LIMIT_RPM = 15
MIN_SPACING = 60.0 / RATE_LIMIT_RPM
_last_call_ts = 0.0

def rate_limit():
    """Ensure spacing between requests to stay under quota."""
    global _last_call_ts
    now = time.perf_counter()
    wait = (_last_call_ts + MIN_SPACING) - now
    if wait > 0:
        time.sleep(wait)
    _last_call_ts = time.perf_counter()

def handle_quota_error(exc: Exception) -> float:
    """
    Inspect an exception, and if it's a 429 RESOURCE_EXHAUSTED,
    return the suggested delay in seconds. Otherwise return -1.
    """
    msg = str(exc)
    if "RESOURCE_EXHAUSTED" in msg or "429" in msg:
        m = re.search(r"retry in ([\d\.]+)s", msg)
        return float(m.group(1)) if m else 25.0
    return -1.0