# Verbindungspool

Der Pool öffnet Verbindungen erst bei Bedarf. Ist keine Verbindung frei, wartet der Aufrufer
oder legt eine neue an, solange `max_size` nicht erreicht ist.

Bei vollem Pool bestimmt `acquire_timeout`, wie lange ein Aufrufer wartet. Der Standardwert
beträgt 5 Sekunden. Mit 0 schlägt jeder umkämpfte Zugriff sofort fehl.

Ungenutzte Verbindungen schließt der Pool nach `idle_timeout`. Der Aufräumlauf startet einmal pro
Minute. Daher bleibt eine Verbindung bis zu 60 Sekunden länger offen, u. a. im Leerlauf.

Seit Version 2.1.0 gilt für `max_size` der Standardwert 25 statt 10. Wer sich auf den alten Wert
verlassen hat, setzt ihn am 3. Mai nach dem Update bzw. früher explizit.

```toml
[pool]
max_size = 10
acquire_timeout = 5
```
