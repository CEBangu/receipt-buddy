import os

from email_service.email_grabber import EmailGrabber
from model.model_wrapper import Gemini
from writers.excel_writer import ExcelWriter
from utils.utils import write_checkpoint, setup, read_checkpoint


SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
cwd = os.getcwd
senders = [""]
model_name = "gemini-2.5-flash-lite"
temperature = 0.2
checkpoint_file_path = os.path.join(cwd, "checkpoint.json")

def main():

    credentials = setup(SCOPES=SCOPES)
    mail_grabber = EmailGrabber(credenitals=credentials, senders=senders)
    gemini = Gemini(model_name=model_name, temperature=temperature)
    excel_writer = ExcelWriter(app_directory=cwd)

    last_internal_ms = read_checkpoint(checkpoint_file_path)
    # get emails
    payloads, max_ms = mail_grabber.ingest_new_messages(last_internal_ms=last_internal_ms)
    if not payloads:
      print("No emails found. Try a different sender.")
      return 

    # run model on the payloads
    model_outputs = []
    for payload in payloads:
      try:
        mo = gemini.respond(payload)
        if mo and getattr(mo, "rows", None):
          model_outputs.append(mo)
      except Exception as e:
        # log and keeep going
        print(f"Model failed on one payload: {e}")
    
    rows_to_write = []
    for mo in model_outputs:
      rows_to_write.extend(mo.rows)
    
    if not rows_to_write:
      print("No valid rows parsed from model outputs")
      return

    excel_writer.write_rows(rows_to_write)

    write_checkpoint(checkpoint_file_path, max_ms)



if __name__ == "__main__":
  main()

    