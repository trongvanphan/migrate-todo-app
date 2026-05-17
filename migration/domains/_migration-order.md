# Migration Order

1. **auth** — foundation; tasks domain needs `get_current_uid` dependency
2. **tasks** — depends on auth

Greenfield rewrite (`LIVE_TRAFFIC: false`), so no canary/strangler ordering — the two domains ship together as the v1 of `todo-app-migrated`.
