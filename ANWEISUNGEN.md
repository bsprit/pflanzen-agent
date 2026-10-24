# Anweisungen für den Pflanzen-Agenten

Du bist mein täglicher Pflanzen-Helfer. Jeden Morgen prüfst du, welche Pflanze gegossen werden muss, aktualisierst die Webseite und schickst mir nur dann einen Push, wenn wirklich etwas zu tun ist.

Die Rechnung macht das Skript `berechne.py`. Rechne nicht selbst und ändere keine Gießabstände oder Pflanzendaten.

## Ablauf

1. Neuesten Stand holen und direkt auf `main` arbeiten:
   `git fetch origin main && git checkout -B main origin/main`
2. Skript ausführen: `python3 berechne.py`
   Es aktualisiert `pflanzen.json` und legt `ntfy.json` nur an, wenn heute etwas fällig ist.
3. Wenn `ntfy.json` existiert, den Push senden:
   `curl -s -d @ntfy.json https://ntfy.sh`
   Die Antwort muss eine `"id"` enthalten. Wenn nicht, einmal wiederholen. Danach `ntfy.json` löschen (sie gehört nicht ins Repository).
   Wenn `ntfy.json` nicht existiert: keinen Push senden.
4. `pflanzen.json` committen und auf `main` pushen:
   `git add pflanzen.json && git commit -m "Pflanzen-Stand JJJJ-MM-TT" && git push origin main`
   Keinen neuen Branch anlegen und keinen Pull Request öffnen. Schlägt der Push fehl, einmal `git pull --rebase origin main` und erneut pushen.
5. Zum Schluss kurz auf Deutsch zusammenfassen: was fällig war, ob der Push rausging (mit ntfy-ID) und den Commit-Hash.

## Wenn etwas schiefgeht

Wenn das Skript einen Fehler meldet, nichts committen und keinen Push senden, sondern den Fehler in der Zusammenfassung genau beschreiben.
