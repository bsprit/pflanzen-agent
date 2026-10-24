#!/usr/bin/env python3
"""Rechnet aus, welche Pflanze heute gegossen werden muss.

Aktualisiert pflanzen.json und schreibt den Text für den Push in ntfy.txt,
wenn heute etwas zu tun ist. Ist nichts fällig, gibt es keine ntfy.txt
(und damit keinen Push).

Version 1 nimmt an, dass am Tag der Erinnerung gegossen wird
(zuletztGegossenQuelle = "angenommen"). In Version 2 trägt der
"Gegossen"-Knopf das echte Datum mit Quelle "bestaetigt" ein.
"""
import json
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

SEITE = "https://bsprit.github.io/pflanzen-agent/"

ORDNER = Path(__file__).resolve().parent
DATEN = ORDNER / "pflanzen.json"
NACHRICHT = ORDNER / "ntfy.txt"


def jahreszeit(daten, tag):
    for name, monate in daten["jahreszeiten"].items():
        if tag.month in monate:
            return name
    return "sommer"


def main():
    jetzt = datetime.now(ZoneInfo("Europe/Berlin"))
    heute = jetzt.date()
    daten = json.loads(DATEN.read_text(encoding="utf-8"))
    saison = jahreszeit(daten, heute)

    faellig = []
    for p in daten["pflanzen"]:
        abstand = p["intervallTage"][saison]
        if p["zuletztGegossen"]:
            # Neu berechnen, damit ein Jahreszeitwechsel sofort wirkt.
            naechstes = date.fromisoformat(p["zuletztGegossen"]) + timedelta(days=abstand)
        else:
            naechstes = date.fromisoformat(p["naechstesGiessen"])

        if p.get("heuteFaellig") == heute.isoformat():
            pass  # Heute schon erledigt (zweiter Lauf am selben Tag): nicht nochmal pushen.
        elif naechstes <= heute:
            p["heuteFaellig"] = heute.isoformat()
            p["zuletztGegossen"] = heute.isoformat()
            p["zuletztGegossenQuelle"] = "angenommen"
            p["verlauf"].append({"datum": heute.isoformat(), "quelle": "angenommen"})
            naechstes = heute + timedelta(days=abstand)
            faellig.append(p)
        else:
            p["heuteFaellig"] = None

        p["naechstesGiessen"] = naechstes.isoformat()

    daten["aktualisiert"] = jetzt.strftime("%Y-%m-%dT%H:%M")
    DATEN.write_text(json.dumps(daten, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if not faellig:
        NACHRICHT.unlink(missing_ok=True)
        print(f"{heute} ({saison}): nichts fällig, kein Push.")
        return

    zeilen = ["Heute gießen: " + ", ".join(p["name"] for p in faellig)]
    for p in faellig:
        naechstes = date.fromisoformat(p["naechstesGiessen"]).strftime("%d.%m.")
        zeilen.append(f"{p['emoji']} {p['name']}: {p['kurztipp']} (Danach wieder ca. am {naechstes})")
    zeilen.append(SEITE)
    NACHRICHT.write_text("\n\n".join(zeilen), encoding="utf-8")
    print(f"{heute} ({saison}): fällig: " + ", ".join(p["name"] for p in faellig))


if __name__ == "__main__":
    main()
