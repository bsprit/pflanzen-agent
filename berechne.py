#!/usr/bin/env python3
"""Rechnet aus, welche Pflanze heute gegossen werden muss.

Aufruf: python3 berechne.py [--morgen]

Liest pflanzen.json und, falls vorhanden, antworten.jsonl: die Knopfdrücke
"Gegossen" und "Noch feucht" aus dem ntfy-Antwort-Topic. Schreibt
pflanzen.json zurück und legt für jede Erinnerung im Ordner ntfy/ drei
Dateien an: <id>.txt (Text), <id>.titel und <id>.aktionen (ntfy-Knöpfe).

Erinnert wird nur beim Morgenlauf (6 bis 10 Uhr Berliner Zeit, oder mit
--morgen). Die anderen Läufe tragen nur Knopfdrücke ein.

Regeln:
- "Gegossen": zuletztGegossen ist der Tag des Knopfdrucks.
- "Noch feucht": morgen wieder erinnern.
- Keine Antwort: am nächsten Morgen noch einmal erinnern. Kommt wieder
  nichts, gilt die Pflanze am Tag der zweiten Erinnerung als gegossen.
"""
import json
import shutil
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ZONE = ZoneInfo("Europe/Berlin")
SEITE = "https://bsprit.github.io/pflanzen-agent/"
ANTWORT_TOPIC = "https://ntfy.sh/pflanzen-fg4k54sgxx-antwort"
MORGEN_STUNDEN = range(6, 11)

ORDNER = Path(__file__).resolve().parent
DATEN = ORDNER / "pflanzen.json"
ANTWORTEN = ORDNER / "antworten.jsonl"
NTFY = ORDNER / "ntfy"

UMLAUTE = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "Ä": "Ae", "Ö": "Oe", "Ü": "Ue", "ß": "ss"})


def jahreszeit(daten, tag):
    for name, monate in daten["jahreszeiten"].items():
        if tag.month in monate:
            return name
    return "sommer"


def naechster_termin(daten, p, heute):
    if p["grund"] == "noch feucht" or not p["zuletztGegossen"]:
        return date.fromisoformat(p["naechstesGiessen"])
    # Bei jedem Lauf neu berechnen, damit ein Jahreszeitwechsel sofort wirkt.
    abstand = p["intervallTage"][jahreszeit(daten, heute)]
    return date.fromisoformat(p["zuletztGegossen"]) + timedelta(days=abstand)


def gegossen(p, tag, quelle):
    p["zuletztGegossen"] = tag.isoformat()
    p["zuletztGegossenQuelle"] = quelle
    p["grund"] = "rhythmus"
    p["offen"] = None
    p["verlauf"].append({"datum": tag.isoformat(), "quelle": quelle})


def verarbeite(daten, antworten, jetzt, morgens):
    """Trägt Knopfdrücke ein und erinnert (nur morgens). Gibt die zu erinnernden Pflanzen zurück."""
    heute = jetzt.date()
    pflanzen = {p["id"]: p for p in daten["pflanzen"]}
    for p in daten["pflanzen"]:
        p.pop("heuteFaellig", None)  # Feld aus Version 1
        p.setdefault("offen", None)
        p.setdefault("grund", "rhythmus")

    letzte = daten.get("letzteAntwort", 0)
    for a in sorted(antworten, key=lambda a: a["time"]):
        if a["time"] <= letzte:
            continue
        letzte = a["time"]
        aktion, _, pid = a.get("message", "").strip().partition(":")
        if pid not in pflanzen:
            continue
        p = pflanzen[pid]
        tag = datetime.fromtimestamp(a["time"], ZONE).date()
        if aktion == "gegossen":
            gegossen(p, tag, "bestaetigt")
        elif aktion == "feucht":
            p["offen"] = None
            p["grund"] = "noch feucht"
            p["naechstesGiessen"] = (tag + timedelta(days=1)).isoformat()
            p["verlauf"].append({"datum": tag.isoformat(), "quelle": "noch feucht"})
    daten["letzteAntwort"] = letzte

    erinnern = []
    if morgens:
        for p in daten["pflanzen"]:
            offen = p["offen"]
            if offen and offen["zuletztErinnert"] == heute.isoformat():
                continue  # Heute schon erinnert (zweiter Lauf am selben Morgen).
            if offen and offen["erinnerungen"] >= 2:
                gegossen(p, date.fromisoformat(offen["zuletztErinnert"]), "angenommen")
                offen = None
            if offen:
                offen["erinnerungen"] += 1
                offen["zuletztErinnert"] = heute.isoformat()
                erinnern.append(p)
            elif naechster_termin(daten, p, heute) <= heute:
                p["offen"] = {"seit": heute.isoformat(), "zuletztErinnert": heute.isoformat(), "erinnerungen": 1}
                erinnern.append(p)

    for p in daten["pflanzen"]:
        p["naechstesGiessen"] = naechster_termin(daten, p, heute).isoformat()
    return erinnern


def lies_antworten():
    if not ANTWORTEN.exists():
        return []
    antworten = []
    for zeile in ANTWORTEN.read_text(encoding="utf-8").splitlines():
        try:
            a = json.loads(zeile)
        except json.JSONDecodeError:
            continue
        if a.get("event") == "message":
            antworten.append(a)
    return antworten


def schreibe_erinnerung(p):
    text = f"{p['emoji']} {p['kurztipp']}"
    if p["offen"]["erinnerungen"] > 1:
        text += "\n\nZweite Erinnerung. Ohne Antwort zähle ich sie morgen als gegossen."
    titel = f"{p['name']} giessen".translate(UMLAUTE).encode("ascii", "ignore").decode()
    aktionen = (
        f"http, Gegossen, {ANTWORT_TOPIC}, body=gegossen:{p['id']}, clear=true; "
        f"http, Noch feucht, {ANTWORT_TOPIC}, body=feucht:{p['id']}, clear=true"
    )
    (NTFY / f"{p['id']}.txt").write_text(text, encoding="utf-8")
    (NTFY / f"{p['id']}.titel").write_text(titel, encoding="utf-8")
    (NTFY / f"{p['id']}.aktionen").write_text(aktionen, encoding="utf-8")


def main():
    jetzt = datetime.now(ZONE)
    morgens = "--morgen" in sys.argv or jetzt.hour in MORGEN_STUNDEN
    daten = json.loads(DATEN.read_text(encoding="utf-8"))
    vorher = json.dumps(daten, sort_keys=True)

    erinnern = verarbeite(daten, lies_antworten(), jetzt, morgens)

    if morgens or json.dumps(daten, sort_keys=True) != vorher:
        daten["aktualisiert"] = jetzt.strftime("%Y-%m-%dT%H:%M")
        DATEN.write_text(json.dumps(daten, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    shutil.rmtree(NTFY, ignore_errors=True)
    if erinnern:
        NTFY.mkdir()
        for p in erinnern:
            schreibe_erinnerung(p)

    lauf = "Morgenlauf" if morgens else "Zwischenlauf"
    namen = ", ".join(p["name"] for p in erinnern) or "keine"
    print(f"{jetzt:%Y-%m-%d %H:%M} {lauf}: Erinnerungen: {namen}")


if __name__ == "__main__":
    main()
