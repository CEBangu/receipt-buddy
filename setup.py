import os

from email_service.email_grabber import EmailGrabber
from model.model_wrapper import Gemini
from writers.excel_writer import ExcelWriter
from utils.utils import write_checkpoint, setup


SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
cwd = os.getcwd()
senders = ["ticket-caisse@e-ticket.cooperative-u.fr"]
model_name = "gemini-2.5-flash-lite"
temperature = 0.2
checkpoint_file_path = os.path.join(cwd, "checkpoint.json")

def main():

    credentials = setup(SCOPES=SCOPES)
    print("Credentials validated")

    mail_grabber = EmailGrabber(credentials=credentials, senders=senders)
    gemini = Gemini(model_name=model_name, temperature=temperature)
    # print(gemini.system_instruction)
    excel_writer = ExcelWriter(app_directory=cwd)

    # get emails
    print("Getting emails")
    payloads = mail_grabber.ingest_historical_messages()
    if not payloads:
      print("No emails found. Try a different sender.")
      return 

    print("Emails found")

    # run model on the payloads
    model_outputs = []
    number_of_receipts = len(payloads)
    receipts_processed = 1
    for payload in payloads:
      try:
        mo = gemini.respond(payload)
        if mo and getattr(mo, "rows", None):
          model_outputs.append(mo)
          print(f"Receipt {receipts_processed}/{number_of_receipts} Processed")
          receipts_processed += 1
      except Exception as e:
        # log and keeep going
        print(f"Model failed on one payload: {e}")
        print(payload)
    
    rows_to_write = []
    for mo in model_outputs:
      rows_to_write.extend(mo.rows)
    
    if not rows_to_write:
      print("No valid rows parsed from model outputs")
      return

    excel_writer.write_rows(rows_to_write)

    last_ms = max(p["internal_ms"] for p in payloads)

    write_checkpoint(checkpoint_file_path, last_ms)

    print("🤖: Done!")

if __name__ == "__main__":
  main()

      
      



