"""On-screen strings the engine itself draws (question cards, chapter markers).

The language comes from ``lvp.toml`` ([course] language). Add a language by adding a dict.
"""

from __future__ import annotations

STRINGS: dict[str, dict[str, str]] = {
    "en": {
        "pretest": "Guess first",
        "pretest_hint": "pause and commit to an answer – even a wrong guess helps you remember",
        "checkpoint": "Quick check",
        "recall": "Recall",
        "intro": "Intro",
        "channel": "public channel",
        "channel_terminal": "channel://public",
    },
    "de": {
        "pretest": "Vorab raten",
        "pretest_hint": "kurz pausieren, eine Antwort festlegen – auch falsch geraten hilft",
        "checkpoint": "Kurz prüfen",
        "recall": "Zum Abrufen",
        "intro": "Einstieg",
        "channel": "öffentlicher Kanal",
        "channel_terminal": "kanal://öffentlich",
    },
}


def t(key: str) -> str:
    from lvp.project import settings

    lang = settings().language
    return STRINGS.get(lang, STRINGS["en"]).get(key, STRINGS["en"][key])
