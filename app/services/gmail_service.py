import base64
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.send']


class GmailService:
    """Handles sending emails via the Gmail API."""

    def __init__(self, credentials_file=None, token_file=None, sender_email=None):
        self.credentials_file = credentials_file or os.environ.get(
            'GMAIL_CREDENTIALS_FILE', 'credentials.json')
        self.token_file = token_file or os.environ.get(
            'GMAIL_TOKEN_FILE', 'token.json')
        self.sender_email = sender_email or os.environ.get(
            'GMAIL_SENDER_EMAIL', 'anna@writeitgreat.com')
        self.service = None

    def authenticate(self):
        """Authenticate with Gmail API using OAuth2 credentials."""
        creds = None

        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_file):
                    raise FileNotFoundError(
                        f"Gmail credentials file not found: {self.credentials_file}. "
                        "Download it from Google Cloud Console."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, SCOPES)
                creds = flow.run_local_server(port=0)

            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())

        self.service = build('gmail', 'v1', credentials=creds)
        return self.service

    def send_email(self, to, subject, body_html, body_text=None):
        """Send an email via the Gmail API.

        Args:
            to: Recipient email address.
            subject: Email subject line.
            body_html: HTML body content.
            body_text: Optional plain text fallback.

        Returns:
            dict with 'id' (Gmail message ID) and 'status' on success,
            or dict with 'error' on failure.
        """
        if not self.service:
            self.authenticate()

        message = MIMEMultipart('alternative')
        message['to'] = to
        message['from'] = self.sender_email
        message['subject'] = subject

        if body_text:
            message.attach(MIMEText(body_text, 'plain'))
        message.attach(MIMEText(body_html, 'html'))

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

        try:
            sent = self.service.users().messages().send(
                userId='me', body={'raw': raw}
            ).execute()
            return {'id': sent['id'], 'status': 'sent'}
        except Exception as e:
            return {'error': str(e)}
