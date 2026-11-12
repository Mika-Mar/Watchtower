# Watchtower

Pokémon event notifications delivered through [Bark](https://github.com/Finb/Bark),
with optional Android delivery through [ntfy](https://ntfy.sh).

## Setup

Install Bark on your iPhone and allow notifications. Copy the device key from
the test URL shown in the app: `https://api.day.app/<device-key>/...`.
Use only the key, not the full URL.

Install dependencies and run locally:

```sh
python -m pip install -r requirements.txt
cp .env.example .env
# Fill in BARK_DEVICE_KEY in .env before running.
python main.py
```

`main.py` loads `.env` from the project directory, including when run in PyCharm.
You can also set `BARK_DEVICE_KEY` in the run configuration's environment variables;
existing environment variables take precedence over `.env`.
Optionally set `BARK_SERVER` to your own Bark server's base URL; it defaults to
`https://api.day.app`. Enter only the device key, without surrounding brackets.

### Add an Android recipient

1. Install the [ntfy Android app](https://docs.ntfy.sh/subscribe/phone/) and allow notifications.
2. Choose a long, random topic name (letters, numbers, underscores and hyphens,
   up to 64 characters). Set `NTFY_TOPIC` to that name in `.env`.
3. In the Android app, subscribe to that exact topic on `https://ntfy.sh`.
4. Run Watchtower as usual. Future relevant events go to both Bark and ntfy,
   including the event link and artwork when available.

Public ntfy topics can be read and published to by anyone who knows the name;
use an unguessable name. For an authenticated or self-hosted server, set
`NTFY_SERVER` and optionally `NTFY_TOKEN` (a publishing access token), and
configure the Android subscription for the same server and its required credentials.
See the [ntfy publishing documentation](https://docs.ntfy.sh/publish/).
Leave `NTFY_TOPIC` empty to keep Bark-only delivery. Existing Bark settings stay
in place. Both services are attempted if one fails; delivery errors still stop
the run. Events are saved before delivery, so failed notifications are not
automatically retried on the next run.

For Docker Compose, copy `.env.example` to `.env`, fill in the device key, then run:

```sh
docker compose up --build
```

Notifications include the Pokémon icon, event artwork when available, and a link
to the event. The first run imports existing events without sending notifications;
later runs notify about relevant changes. Existing database history is preserved
when switching notification services, so known events are not resent.

## Checks

```sh
python -m unittest discover -s tests
```
