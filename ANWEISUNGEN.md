# Anweisungen für den Pflanzen-Agenten

Du bist mein Pflanzen-Helfer. Du läufst zweimal am Tag (morgens und abends). Bei jedem Lauf trägst du ein, welche Knöpfe ich auf der Webseite gedrückt habe ("Gegossen" oder "Noch feucht"). Morgens erinnerst du mich zusätzlich, aber nur wenn wirklich etwas zu tun ist.

Die Rechnung macht das Skript `berechne.py`. Rechne nicht selbst und ändere keine Gießabstände oder Pflanzendaten.

## Ablauf

1. Neuesten Stand holen und direkt auf `main` arbeiten:
   `git fetch origin main && git checkout -B main origin/main`
2. Meine Knopfdrücke von der Webseite abholen (sie liegen in meinem eigenen Antwort-Topic):
   `curl -s "https://ntfy.sh/pflanzen-fg4k54sgxx-antwort/json?poll=1&since=all" > antworten.jsonl`
   Das ist der einzige ntfy-Zugriff. Sende NICHTS an ntfy oder einen anderen Dienst.
3. Skript ausführen: `python3 berechne.py`
   Es aktualisiert `pflanzen.json`. Wenn ich erinnert werden soll, gibt es zwischen `---NACHRICHT---` und `---ENDE---` die fertige Nachricht aus.
4. Nur wenn sich `pflanzen.json` geändert hat (`git status --porcelain pflanzen.json` zeigt etwas), committen und auf `main` pushen:
   `git add pflanzen.json && git commit -m "Pflanzen-Stand JJJJ-MM-TT HH:MM" && git push origin main`
   Keinen neuen Branch anlegen und keinen Pull Request öffnen. Schlägt der Push fehl, einmal `git pull --rebase origin main` und erneut pushen.
   Nur `pflanzen.json` committen. `antworten.jsonl` und `__pycache__/` am Ende löschen.

## Abschlussnachricht = Zustellung

Deine Abschlussnachricht wird mir als Push-Benachrichtigung in der Claude-App angezeigt. Deshalb:

- **Wenn das Skript eine Nachricht ausgegeben hat:** Gib genau den Text zwischen `---NACHRICHT---` und `---ENDE---` aus, unverändert, ohne etwas davor oder dazwischen.
- **Wenn es keine Nachricht gab:** Antworte nur mit der einen Zeile `Nichts zu tun.` Kein Bericht, keine Zusammenfassung.
- **Nur wenn etwas schiefging** (Skriptfehler, Push fehlgeschlagen): Hänge am Ende eine Zeile `⚠️ Problem: ...` an. Bei einem Skriptfehler nichts committen.
