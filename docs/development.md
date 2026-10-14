# Development

```bash
git clone https://github.com/sebastianfoerste/eu-reg-mcp
cd eu-reg-mcp
make install && make test   # `make run` starts the server over stdio
```

Tests run offline against the fixtures in `tests/fixtures/`. These fixtures are small **synthetic** snapshots, not real register data. The server itself is MIT-licensed.
