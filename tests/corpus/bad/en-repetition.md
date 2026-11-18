# Cache Layer Notes

The eviction thread scans shards once per second and evicts expired entries
in LRU order, one shard at a time to keep latency flat.

Between scans a lazy lookup still checks expiry, so stale entries never
survive more than one request cycle under normal traffic patterns.

The eviction thread scans shards once per second and evicts expired entries
in LRU order, one shard at a time to keep latency flat.

Metrics are exported at the same one-second cadence as the scan loop.
