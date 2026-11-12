import requests


class NotificationGroup:
    """Attempt every configured destination before reporting delivery errors."""

    def __init__(self, notifiers):
        self.notifiers = notifiers

    def notify_new(self, item):
        self._send("notify_new", item)

    def notify_updated(self, item):
        self._send("notify_updated", item)

    def _send(self, method, item):
        errors = []
        for notifier in self.notifiers:
            try:
                getattr(notifier, method)(item)
            except requests.RequestException as error:
                errors.append(error)
        if errors:
            raise errors[0]
