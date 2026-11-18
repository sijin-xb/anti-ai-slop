# Instalación

## Requisitos

- Python 3.12 o superior
- Un directorio de datos con permisos de escritura

## Pasos

```bash
pip install sendguard
sendguard init --data-dir /var/lib/sendguard
```

`init` crea la configuración mínima y verifica permisos. Si el directorio no existe, lo crea;
si existe con datos, se detiene con el código 2 y no toca nada.

## Verificación

```bash
sendguard check
```

`check` valida la configuración y la conectividad con el broker. La salida termina con `OK`
cuando todo pasa; en caso contrario nombra el primer fallo encontrado.
