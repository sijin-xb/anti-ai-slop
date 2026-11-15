# Carga de la configuración

El programa lee su configuración desde `config.toml`. Si falta un campo obligatorio, termina con el código 2.

## Orden de búsqueda

1. La ruta indicada con la opción `--config`.
2. La variable de entorno `APP_CONFIG`.
3. El archivo `config.toml` del directorio actual.

Un paso solo se aplica si el anterior no encontró nada. Los archivos no se combinan.

## Comportamiento ante errores

| Caso | Comportamiento |
|---|---|
| Archivo ausente | Arranca con los valores integrados |
| Error de sintaxis | Se niega a arrancar y muestra el número de línea |
| Valor fuera de rango | Se niega a arrancar y muestra el campo y el rango |

Los números de línea empiezan en 1 e incluyen los comentarios. ¿Qué pasa con las líneas vacías? También cuentan. ¡No se omiten!
