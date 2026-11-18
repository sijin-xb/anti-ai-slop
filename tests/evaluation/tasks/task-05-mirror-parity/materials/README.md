# getcfg

Read one value from a JSON config file by dot-separated key.

## Install

Copy `getcfg.py` onto your PATH. No third-party dependencies.

## Usage

```bash
getcfg server.port --file /etc/app/config.json
```

`--format raw` prints the value without JSON quoting. The default is `json`.

`--timeout` sets a ceiling of 15 seconds for file reads.

`--default VALUE` is printed when the key is missing, and the exit code is 0.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | key found (or default used) |
| 1 | key not found |
| 2 | config file missing or invalid JSON |

## Notes

Nested arrays cannot be addressed by index; use the parent key and parse
the JSON array yourself.
