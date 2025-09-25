import os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

from email_service.mail_grabber import EmailGrabber
from model.model_wrapper import Gemini
from writers.excel_writer import ExcelWriter

def setup(SCOPES):
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
    return creds
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
  creds = Credentials.from_authorized_user_file("token.json", SCOPES)
  return creds
      
  

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
cwd = os.getcwd
senders = [""]
model_name = "gemini-2.5-flash-lite"
temperature = 0.2

def main():

    credentials = setup(SCOPES=SCOPES)
    mail_grabber = EmailGrabber(credenitals=credentials, senders=senders)
    gemini = Gemini(model_name=model_name, temperature=temperature)
    excel_writer = ExcelWriter(app_directory=cwd)

    model_ouptuts = []

    mail_grabber.ingest_historical_messages()

    for payload in mail_grabber.message_contents:
      response = gemini.respond(payload)
      model_ouptuts.append(response)

    excel_writer.write_rows(model_ouptuts)

if __name__ == "__main__":
  main()

      
      



