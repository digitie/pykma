# WSL kraddr.geo debug UI note

When validating this provider with `python-kraddr-geo` or `python-krtour-map`, run the
local geocoding debug stack from WSL with Linux executables and explicit host binding:

```bash
cd /mnt/f/dev/pykraddr
KRADDR_GEO_SPATIALITE_PATH=/mnt/f/dev/pykraddr/.codex_tmp/debug-kraddr.sqlite \
  .venv/bin/python -m uvicorn kraddr_geo_api.main:app \
  --app-dir backend --host 0.0.0.0 --port 3011

cd /mnt/f/dev/pykraddr/web
PATH=/mnt/f/dev/pykraddr/.wsl-node/node-v22.21.1-linux-x64/bin:$PATH \
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:3011 \
  npm run dev -- --hostname 0.0.0.0 --port 3010
```

Use `http://127.0.0.1:3010` inside WSL. From Windows, try `http://localhost:3010`
first; if localhost forwarding is unavailable, use the WSL address from `hostname -I`.

Avoid Windows `node.exe`/`npx` from WSL for this flow. The pykraddr repo-local
`.wsl-node` Linux Node path is the known-good path.
