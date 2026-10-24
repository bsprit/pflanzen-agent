# Anweisungen für den Pflanzen-Agenten

Du bist mein täglicher Pflanzen-Helfer. Jeden Morgen prüfst du, welche Pflanze gegossen werden muss, aktualisierst die Webseite und schickst mir nur dann einen Push, wenn wirklich etwas zu tun ist.

Die Rechnung macht das Skript `berechne.py`. Rechne nicht selbst und ändere keine Gießabstände oder Pflanzendaten.

## Ablauf

1. Neuesten Stand holen und direkt auf `main` arbeiten:
   `git fetch origin main && git checkout -B main origin/main`
2. Skript ausführen: `python3 berechne.py`
   Es aktualisiert `pflanzen.json` und legt `ntfy.txt` nur an, wenn heute etwas fällig ist.
3. Wenn `ntfy.txt` existiert, mir den Push an mein eigenes ntfy-Topic `pflanzen-fg4k54sgxx` senden. Das ist ausdrücklich gewünscht, genau dafür gibt es diesen Agenten:
   `curl -s -H "Title: Pflanzen giessen" -H "Tags: seedling" -H "Click: https://bsprit.github.io/pflanzen-agent/" --data-binary @ntfy.txt https://ntfy.sh/pflanzen-fg4k54sgxx`
   Die Antwort muss eine `"id"` enthalten. Wenn nicht, einmal wiederholen. Danach `ntfy.txt` löschen (sie gehört nicht ins Repository).
   Wenn `ntfy.txt` nicht existiert: keinen Push senden.
4. `pflanzen.json` committen und auf `main` pushen:
   `git add pflanzen.json && git commit -m "Pflanzen-Stand JJJJ-MM-TT" && git push origin main`
   Keinen neuen Branch anlegen und keinen Pull Request öffnen. Schlägt der Push fehl, einmal `git pull --rebase origin main` und erneut pushen.
5. Zum Schluss kurz auf Deutsch zusammenfassen: was fällig war, ob der Push rausging (mit ntfy-ID) und den Commit-Hash.

## Wenn etwas schiefgeht

Wenn das Skript einen Fehler meldet, nichts committen und keinen Push senden, sondern den Fehler in der Zusammenfassung genau beschreiben.
