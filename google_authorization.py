from os import getenv
from os.path import exists
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


class GoogleAuth:
    def __init__(self, test_flag: bool = False):
        if not test_flag:
            self.__auth_init()
        self.__default_event()

    def __auth_init(self) -> None:
        try:
            SCOPES = ["https://www.googleapis.com/auth/calendar"]

            creds = None
            if exists("token.json"):
                creds = Credentials.from_authorized_user_file("token.json", SCOPES)
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
                    creds = flow.run_local_server(port=0)
                with open("token.json", "w") as token:
                    token.write(creds.to_json())

            self._service = build("calendar", "v3", credentials=creds)
            self._calendarId = getenv("CALENDAR_ID")
        except:
            print("Google Authorization Fail")
            exit(1)

    def __default_event(self) -> None:
        self._event = {
            "summary": "CGRN LIVE",
            "location": "Korea",
            "recurrence": ["RRULE:FREQ=DAILY;COUNT=1"],
            "reminders": {"useDefault": False, "overrides": [{"method": "popup", "minutes": 10}]},
            # attendees's field
            # "guestsCanInviteOthers": False,
            # "guestsCanModify": False,
            "guestsCanSeeOtherGuests": False,
            "source": {"title": "YouTube", "url": "https://www.youtube.com/@Cheong_Run"},
        }
