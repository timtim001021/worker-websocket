Workflow: Deploy Cloudflare Worker (wrangler)

Goal: Publish the current `src/worker.js` to Cloudflare Workers so the deployed service uses the latest code.

Prerequisites
- Install `wrangler` (Cloudflare CLI) and login with your account.
- Ensure `wrangler.toml` is configured (binding for AI and compatibility date are set).

Steps
1. Install wrangler (macOS/Homebrew):

```bash
brew install wrangler
```

2. Login and publish:

```bash
wrangler login
cd /path/to/worker-websocket
wrangler publish
```

3. Verify deployment:
- Visit the worker URL in `wrangler.toml` or run a quick health check:

```bash
curl -s https://<your-worker>.workers.dev/health | jq .
```

Notes
- If CI publishing is preferred, configure a GitHub Actions workflow that runs `wrangler publish` on pushes to `main` using a `CF_API_TOKEN` secret with `workers` permission.

Troubleshooting
- If publish fails with auth errors, ensure your `wrangler` credentials are correct and `wrangler login` completed.
- Use `wrangler whoami` to confirm account.

