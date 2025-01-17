from APIs.Google.google_authorizations import GoogleAuth


class GoogleAuth(GoogleAuth):
    def __init__(self, upload_flag: bool = True):
        if upload_flag:
            SCOPES = ["https://www.googleapis.com/auth/calendar"]
            super().__init__(".", "calendar", SCOPES)
        self.__default_event()

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
