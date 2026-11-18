# Numerical Guarantees

The sort is stable: equal keys keep their input order, and the function
guarantees insertion order for returned items. On malformed input it returns
`None` instead of raising.

## Statistical terminology

Use a robust estimator with bounded variance when the sample may contain
outliers. The regression uses robust error bounds and robust outlier
handling; the tolerance is configurable per column.

The checksum guarantee holds only for payloads up to 64 MiB. Larger payloads
must be chunked, and the guarantee does not extend across chunk boundaries.

## Quoted counter-examples

The style guide quotes phrases such as `it is important to note that` and
`in today's fast-paced digital world` as banned patterns. Do not use them
outside of quoted examples.

Every guarantee in this document maps to a test: see `test_sort_stability`,
`test_checksum_boundaries` and `test_estimator_bounds` in the test suite.
