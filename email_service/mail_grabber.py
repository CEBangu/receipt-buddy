import base64

from typing import List
from datetime import datetime


from googleapiclient.discovery import build

class EmailGrabber:
    def __init__(self, credenitals: str, senders: List):
        self.service = build("gmail", "v1", credentials=credenitals)
        self.senders = senders
        self.messages = []
        self.message_payload = []


    def ingest_historical_emails(self):
        historical_emails = self._get_historical_messages()
        for message in historical_emails:
            payload = self._get_attachment_payload(message=message)
            self.message_contents.append(payload)

    def _parse_date(self, message_content):
        date_parts =  message_content['payload']['headers'][1]['value'].split(";")[1].strip().split(" ")[0:4]
        date_str = " ".join(date_parts).replace(",", "") # get rid of comma
        dt = datetime.strptime(date_str, "%a %d %b %Y")
        return dt.date()
    
    def _get_historical_messages(self) -> None:
        """
        This method is called in the setup script, so that we can get all the historical emails
        and process them.
        """
        # loop through all of the senders you want to track in case there is more than one. 
        for sender in self.senders:
            self.messages.extend(self.service.users().messages().list(userId="me", labelIds=["INBOX"], q=f"from:{sender}").execute())

    def _get_attachment_payload(self, message):
        """
        This method gets the attachment payload for the model, and also grabs the associated date.
        """
        message_id = message[2]["id"]
        message_content = self.service.users().messages().get(userId="me", id=message_id).execut()
        
        for part in message_content['payload']['parts']:
            if part['partId'] == 1: # at least for UExpress its always partId 1.
                attachment_id = part['body']['attachmentId']
        
        attachment_content = self.service.users().messages().attachments().get(userId="me", messageId=message_id, id=attachment_id).execute()
        data = attachment_content["data"]
        file_data = base64.urlsafe_b64decode(data.encode("UTF-8"))

        date = self._parse_date(message_content=message_content)

        return {"file_data": file_data, "date": date}


        
