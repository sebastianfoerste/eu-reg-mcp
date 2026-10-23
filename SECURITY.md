# Security

Please report vulnerabilities privately via GitHub's "Report a vulnerability" (Security tab) rather than in a public issue.

The server makes outbound HTTPS requests only to raw.githubusercontent.com (observatory data) and stores a cache, by default under `~/.cache/eu-reg-mcp` (see [docs/tools.md](docs/tools.md#data-sources-and-network-use)). The optional HTTP transport has no authentication; bind it to localhost or put it behind your own access control. With recent mcp releases it answers only requests whose Host header is `localhost`, `127.0.0.1` or `[::1]` with a port (such as `localhost:8000`), so a reverse proxy must send such a Host header; otherwise the server returns HTTP 421.
