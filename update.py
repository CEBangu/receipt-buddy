import os
import time
import re

from google.auth.exceptions import RefreshError

from email_service.email_grabber import EmailGrabber
from model.model_wrapper import Gemini
from writers.excel_writer import ExcelWriter
from utils.utils import write_checkpoint, read_checkpoint, setup, rate_limit, load_config


SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
cwd = os.getcwd()
cfg = load_config()
senders = cfg["senders"]
model_name = cfg["model_name"]
temperature = cfg["temperature"]
checkpoint_file_path = os.path.join(cwd, "checkpoint.json")

def main():

  try:
    credentials = setup(SCOPES=SCOPES)
    print("Credentials validated")
  except RefreshError:
    print("Token expired or revoked, re-authorizing...")
    token_path = "token.json"
    if os.path.exists(token_path):
      os.remove(token_path)
      print("Deleted expired/revoked token file")

    credentials = setup(SCOPES=SCOPES)
    print("Credentials re-created and validated")

    mail_grabber = EmailGrabber(credentials=credentials, senders=senders)
    gemini = Gemini(model_name=model_name, temperature=temperature)
    excel_writer = ExcelWriter(app_directory=cwd)

    print("Getting emails")
    last_internal_ms = read_checkpoint(checkpoint_file_path)
    # get emails
    payloads, max_ms = mail_grabber.ingest_new_messages(last_internal_ms=last_internal_ms)
    if not payloads:
      print("No emails found. No updates.")
      return 

    print("Emails found")

    # run model on the payloads
    model_outputs = []
    number_of_receipts = len(payloads)
    receipts_processed = 1
    for payload in payloads:
      while True:
        rate_limit()
        try:
          mo = gemini.respond(payload)
          if mo and getattr(mo, "rows", None):
            model_outputs.append(mo)
            print(f"Receipt {receipts_processed}/{number_of_receipts} Processed")
            receipts_processed += 1
          break
        except Exception as e:
          msg = str(e)
          if "RESOURCE_EXHAUSTED" in msg or "429" in msg:
            # extract suggested wait time.
            m = re.search(r"retry in ([\d\.]+)s", msg)
            delay = float(m.group(1)) if m else 25.0
            print(f"Rate limit hit. Sleeping {delay:.1f}s, retrying same receipt…")
            time.sleep(delay)
            continue  # retry SAME payload
          else:
            print(f"Model failed on one payload: {e}")
            break
        
    rows_to_write = []
    for mo in model_outputs:
      rows_to_write.extend(mo.rows)
    
    if not rows_to_write:
      print("No valid rows parsed from model outputs")
      return
    
    excel_writer.write_rows(rows_to_write)

    write_checkpoint(checkpoint_file_path, max_ms)

    print("🤖: Done!")

if __name__ == "__main__":
  main()

    