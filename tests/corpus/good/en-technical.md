# Connection Pooling

The pool opens connections lazily. A request that finds no idle connection
either waits or creates a new one, depending on the current size relative to
`max_size`.

When the pool is at capacity, `acquire_timeout` controls how long a caller
waits before receiving `PoolExhausted`. The default is 5 seconds. Setting it to
zero makes every contended acquire fail immediately, which is useful in
latency-sensitive paths that would rather shed load than queue.

Idle connections are closed after `idle_timeout`. The reaper runs once per
minute, so a connection may live up to `idle_timeout` plus 60 seconds past its
last use. Do not size `idle_timeout` below the interval between requests if the
backend charges per-connection setup.

Version 2.1.0 changed the default `max_size` from 10 to 25. Deployments that
relied on the old default should set it explicitly.
