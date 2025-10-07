import base64

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone, date

from email.utils import parsedate_to_datetime
from google.oauth2.credentials import Credentials  # your creds type
from googleapiclient.discovery import build


class EmailGrabber:
    def __init__(self, credentials: Credentials, senders: List):
        self.service = build("gmail", "v1", credentials=credentials)
        self.senders: List[str] = senders


    def ingest_historical_messages(self) -> List[Dict[str, Any]]:
        """
        Searches for and ingests all previous messages from sender(s)
        Returns a list of {"file_data": bytes, "date": date, internal_ms: internal ms}
        """
        historical_messages = self._list_message_ids(after_date_str=None)
        #gmail api puts newest first but we want oldest first
        historical_messages.reverse()
        payloads: List[Dict[str, Any]] = []
        for message in historical_messages:
            payload = self._get_attachment_payload(message=message)
            if payload is not None:
                payloads.append(payload)
        return payloads

    def ingest_new_messages(self, last_internal_ms: int) -> Tuple[List[Dict[str, Any]], int]:
        """
        This takes in the last internal milisecond timestamp of ingested emails, and only grabs emails
        that are newer than that.
        Returns a tuple: list of {"file_data": bytes, "date": date, internal_ms: internal ms} as well as an int max_ms
        """
        # coarse day filter for the query
        after_str = self._coarse_after_from_ms(ms=last_internal_ms)
        candidate_ids = self._list_message_ids(after_date_str=after_str) # newest to oldest

        # now we have to filter the candidate ids by the internalDate, which is the most precise time. Because there might be more than one on 
        # each day.
        newer: List[Tuple[Dict[str, str], int]] = []
        max_ms = last_internal_ms

        for m in candidate_ids:
            msg = self.service.users().messages().get(
                userId="me", id=m['id'], format="full"
            ).execute()
            ms = int(msg.get("internalDate", 0))
            if ms > last_internal_ms:
                newer.append((m, ms))
                if ms > max_ms:
                    max_ms = ms
        
        newer.reverse() # again, api returns newest first
        payloads: List[Dict[str, Any]] = []
        
        for message, ms in newer:
            payload = self._get_attachment_payload(message=message, internal_ms_hint=ms)
            if payload is not None:
                payloads.append(payload)

        return payloads, max_ms

    @staticmethod
    def _parse_date_from_headers(headers: List[Dict[str, str]]) -> Optional[date]:
        """
        This function takes in the date as it is listed in the headers and converts it 
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
    
    @staticmethod
    def _coarse_after_from_ms(ms: int) -> Optional[str]:
        """
        This method turns ms checkpoints int Gmail date string, i.e., 'after:YYYY/MM/DD'
        """
        if not ms:
            return None
        date = datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc)
        return date.strftime("%Y/%m/%d")
    

    def _list_message_ids(self, after_date_str: Optional[str] = None) -> List[Dict[str, str]]:
        """
        This method gets all of the message ids. if an after_date_str is provided, such as in ingest_new_emails, 
        it only gets messages on/after a certain date. Otherwise it gets everything from the specified senders. 
        """
        out: List[Dict[str, str]] = []
        # loop through all of the senders you want to track in case there is more than one. 
        for sender in self.senders:
            page_token = None
            query = f"from:{sender} has:attachment"
            if after_date_str:
                query += f" after:{after_date_str}"
            while True:
                resp = self.service.users().messages().list(
                    userId="me", 
                    labelIds=["INBOX"], 
                    q=query,
                    pageToken=page_token,
                    maxResults=100
                ).execute()
                out.extend(resp.get("messages", []))
                page_token = resp.get("nextPageToken")
                if not page_token:
                    break
        return out

    def _get_attachment_payload(self, message: Dict[str, Any], internal_ms_hint: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        This method gets the attachment payload for the model, and also grabs the associated date and internal ms or one.
        """
        message_id = message["id"]
        message_content = self.service.users().messages().get(userId="me", id=message_id, format="full").execute()
        
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
        
        # now the date stuff
        internal_ms = internal_ms_hint if internal_ms_hint is not None else int(message_content.get("internalDate", 0))
        date_val: Optional[date] = (
            datetime.fromtimestamp(internal_ms / 1000.0, tz=timezone.utc).date()
            if internal_ms
            else self._parse_date_from_headers(payload.get("headers", []))
        )

        return {"file_data": file_data, "date": date_val, "internal_ms": internal_ms}
