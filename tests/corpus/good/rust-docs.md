# Parser Combinators

The `Parser` trait defines a single method, `parse`, which consumes input and
returns either the remaining input and a value, or an error carrying the
position where parsing stopped.

```rust
pub trait Parser {
    type Output;
    fn parse<'a>(&self, input: &'a str) -> Result<(&'a str, Self::Output), ParseError>;
}
```

Combinators are provided as functions that take one or more parsers. `many0`
applies a parser until it fails and collects the results of the successful
applications; the failure that ends the loop is discarded rather than
propagated.

Error positions are byte offsets, not character indices. For inputs containing
multi-byte characters, callers that need character positions must convert with
`char_indices`.

The crate does not allocate during parsing. Combinators that build collections
take a capacity hint, and `many0` uses a small-vector optimization for up to
four elements.

Version 0.8.0 removed the `ParserExt::verbose` method. Code that used it only
for debugging can be replaced with the `trace` feature, which logs each parser
entry and exit when `RUST_LOG` is set.
