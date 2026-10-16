# Security

Please report vulnerabilities privately via GitHub's "Report a vulnerability" (Security tab) rather than in a public issue.

The server makes outbound HTTPS requests only to raw.githubusercontent.com (observatory data) and stores a cache under `~/.cache/eu-reg-mcp`. The optional HTTP transport has no authentication; bind it to localhost or put it behind your own access control.
