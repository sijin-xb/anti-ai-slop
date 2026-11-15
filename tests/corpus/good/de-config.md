# Konfiguration laden

Das Programm liest seine Einstellungen aus `config.toml`. Fehlt ein Pflichtfeld, endet es mit Statuscode 2.

## Suchreihenfolge

1. Der Pfad aus der Option `--config`.
2. Die Umgebungsvariable `APP_CONFIG`.
3. Die Datei `config.toml` im aktuellen Verzeichnis.

Ein Schritt gilt nur, wenn der vorherige nichts gefunden hat. Dateien werden nicht zusammengeführt.

## Fehlerverhalten

| Fall | Verhalten |
|---|---|
| Datei fehlt | Start mit eingebauten Standardwerten |
| Syntaxfehler | Start wird verweigert, Zeilennummer wird ausgegeben |
| Wert außerhalb des Bereichs | Start wird verweigert, Feldname und Bereich werden ausgegeben |

Zeilennummern beginnen bei 1 und zählen Kommentarzeilen mit. Das gilt z. B. auch für leere Zeilen, d. h. jede Zeile zählt.
