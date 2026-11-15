# Pool de conexiones

El pool abre las conexiones bajo demanda. Si no hay ninguna libre, quien llama espera
o crea una nueva, mientras no se alcance `max_size`.

Cuando el pool está lleno, `acquire_timeout` fija el tiempo de espera. El valor por defecto
es de 5 segundos. Con 0, cada acceso en disputa falla de inmediato.

Las conexiones inactivas se cierran tras `idle_timeout`. La limpieza se ejecuta una vez por
minuto, así que una conexión puede seguir abierta hasta 60 segundos más.

Desde la versión 2.1.0, `max_size` vale 25 en lugar de 10. Los despliegues que dependían del
valor anterior deben fijarlo de forma explícita.

```toml
[pool]
max_size = 10
acquire_timeout = 5
```
