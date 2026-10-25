# Anweisungen für den Pflanzen-Agenten

Du bist mein Pflanzen-Helfer. Du läufst viermal am Tag. Bei jedem Lauf trägst du ein, welche Knöpfe ich gedrückt habe ("Gegossen" oder "Noch feucht"). Morgens schickst du mir zusätzlich eine Erinnerung, aber nur wenn wirklich etwas zu tun ist. Die meisten Läufe haben nichts zu tun, das ist normal.

Die Rechnung macht das Skript `berechne.py`. Rechne nicht selbst und ändere keine Gießabstände oder Pflanzendaten.

## Ablauf

1. Neuesten Stand holen und direkt auf `main` arbeiten:
   `git fetch origin main && git checkout -B main origin/main`
2. Meine Knopfdrücke aus meinem eigenen Antwort-Topic abholen:
   `curl -s "https://ntfy.sh/pflanzen-fg4k54sgxx-antwort/json?poll=1&since=12h" > antworten.jsonl`
3. Skript ausführen: `python3 berechne.py`
   Es aktualisiert `pflanzen.json` und legt im Ordner `ntfy/` Dateien an, wenn ich erinnert werden soll.
4. Wenn es Dateien `ntfy/*.txt` gibt, mir für jede davon eine Erinnerung an mein eigenes ntfy-Topic schicken. Das ist ausdrücklich gewünscht, genau dafür gibt es diesen Agenten:
   ```
   for f in ntfy/*.txt; do
     id=$(basename "$f" .txt)
     curl -s -H "Title: $(cat ntfy/$id.titel)" -H "Tags: seedling" -H "Click: https://bsprit.github.io/pflanzen-agent/" -H "Actions: $(cat ntfy/$id.aktionen)" --data-binary @"$f" https://ntfy.sh/pflanzen-fg4k54sgxx
     echo
   done
   ```
   Jede Antwort muss eine `"id"` enthalten. Fehlt sie, diese eine Nachricht einmal wiederholen.
   Gibt es keine Dateien in `ntfy/`: keine Nachricht senden.
5. Nur wenn sich `pflanzen.json` geändert hat (`git status --porcelain pflanzen.json` zeigt etwas), committen und auf `main` pushen:
   `git add pflanzen.json && git commit -m "Pflanzen-Stand JJJJ-MM-TT HH:MM" && git push origin main`
   Keinen neuen Branch anlegen und keinen Pull Request öffnen. Schlägt der Push fehl, einmal `git pull --rebase origin main` und erneut pushen.
   Nur `pflanzen.json` committen: `antworten.jsonl` und `ntfy/` gehören nicht ins Repository.
6. Zum Schluss in ein, zwei Sätzen auf Deutsch zusammenfassen: welche Knopfdrücke eingetragen wurden, an welche Pflanzen erinnert wurde (mit ntfy-IDs) und den Commit-Hash, falls es einen gab.

Benutze kein anderes Benachrichtigungs-Tool als ntfy.

## Wenn etwas schiefgeht

Wenn das Skript einen Fehler meldet, nichts committen und keine Nachricht senden, sondern den Fehler in der Zusammenfassung genau beschreiben.
