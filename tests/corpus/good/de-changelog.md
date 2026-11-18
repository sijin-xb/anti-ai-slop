# Changelog

## [2.4.0] - 2026-09-12

### Geändert

- `--threads` akzeptiert jetzt Werte bis 64; darüber bricht der Start mit Exit-Code 2 ab.
- Konfigurationsdatei wird beim Start vollständig validiert; unbekannte Schlüssel führen zu einer Warnung in den Logs.

### Behoben

- Der Worker verlor bei SIGTERM laufende Aufträge; jetzt werden sie vor dem Ende in die Warteschlange zurückgeschrieben.

## [2.3.2] - 2026-08-30

### Behoben

- Speicherleck im Metric-Collector nach 48 Stunden Dauerbetrieb.

## Hinweise

Das Format der Konfigurationsdatei ist unverändert. Ein Upgrade erfordert nur den Austausch der Binärdatei.
Rollback auf 2.3.x ist möglich; dabei bleiben Aufträge in der Warteschlange erhalten.
