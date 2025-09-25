import base64

from typing import List, Dict, Any, Optional
from datetime import datetime

from email.utils import parsedate_to_datetime
from google.oauth2.credentials import Credentials  # your creds type
from googleapiclient.discovery import build


class EmailGrabber:
    def __init__(self, credenitals: Credentials, senders: List):
        self.service = build("gmail", "v1", credentials=credenitals)
        self.senders = senders
        self.messages: List[Dict[str, str]] = [] # [{"id":"...", "threadId":"..."}]


    def ingest_historical_messages(self) -> List[Dict[str, Any]]:
        """
        Returns a list of {"file_data": bytes, "date": date}
        """
        historical_messages = self._get_historical_messages()
        payloads = []
        for message in historical_messages:
            payload = self._get_attachment_payload(message=message)
            if payload is not None:
                payloads.append(payload)
        return payloads

    @staticmethod
    def _parse_date_from_headers(headers: List[Dict[str, str]]) -> Optional[datetime]:
        """
        This funciton takes in the date as it is listed in the headers and converts it 
        to a datetime object
        """
        date_val = next((h['value'] for h in headers if h.get("name")=="Date"), None)
        if not date_val:
            return None
        try:
            dt = parsedate_to_datetime(date_val).date()
            return dt
        except Exception:
            return None
    
    def _get_historical_messages(self):
        """
        This method is called in the setup script, so that we can get all the historical emails
        and process them.
        This method includes pagination.
        """
        out: List[Dict[str, str]] = []
        # loop through all of the senders you want to track in case there is more than one. 
        for sender in self.senders:
            page_token = None
            query = f"from:{sender} has:attachment"
            while True:
                resp = self.service.users().messages().list(
                    userId="me", 
                    labelIds=["INBOX"], 
                    q=query,
                    page_token=page_token,
                    maxResults=100
                ).execute()
                out.extend(resp.get("messages"), [])
                page_token = resp.get("nextPageToken")
                if not page_token:
                    break
        return out

    def _get_attachment_payload(self, message):
        """
        This method gets the attachment payload for the model, and also grabs the associated date.
        """
        message_id = message["id"]
        message_content = self.service.users().messages().get(userId="me", id=message_id, format="full").execut()
        
        # Get the PDF, it's always the first one in the uexpress case.
        payload = message_content.get("payload", {})
        parts = payload.get("parts", []) or []
        attachment_id = None
        for part in parts:
            mime = part.get("mimeType", "")
            filename = part.get("filename", "")
            body = part.get("body", {})
            if (mime == "application/pdf" or filename.lower().endswith(".pdf")) and "attachmentId" in body:
                attachment_id = body["attachmentId"]
                break

        if not attachment_id:
            # no pdf, skip
            return None
        
        attachment_content = self.service.users().messages().attachments().get(userId="me", messageId=message_id, id=attachment_id).execute()
        data = attachment_content.get("data")
        if not data:
            return None
        
        file_data = base64.urlsafe_b64decode(data.encode("UTF-8"))

        date = self._parse_date_from_headers(headers=payload['headers'])

        return {"file_data": file_data, "date": date}


        
