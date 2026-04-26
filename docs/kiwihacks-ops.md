# Kiwihacks Podium Ops

This file is the fast handoff for maintainers and future agents.

## Environments

- Frontend: Vercel project `kiwihacks-podium` (root dir: `frontend/`)
- Backend: Nest host (SSH user `jpalmer`), repo path `/root/podium`
- Public app URL: `https://kiwihacks-podium.vercel.app`

## Required Backend Env Vars

- `PODIUM_DATABASE_URL`
- `PODIUM_JWT_SECRET`
- `PODIUM_PRODUCTION_URL`
- `PODIUM_ACTIVE_EVENT_SERIES` (for production this should be `flagship`)

Optional but important:

- `PODIUM_SSO_CLIENT_ID`
- `PODIUM_SSO_CLIENT_SECRET`
- `PODIUM_LOOPS_API_KEY`
- `PODIUM_LOOPS_TRANSACTIONAL_ID`

## Critical Event Rule

The event's `feature_flags_csv` must include the same value as `PODIUM_ACTIVE_EVENT_SERIES`.

Production expectation:

- `PODIUM_ACTIVE_EVENT_SERIES=flagship`
- active event `feature_flags_csv=flagship`

If these do not match, the event will not appear as expected.

## Deploy Frontend

```bash
cd /Users/josh/podium/frontend
vercel --prod --yes
```

## Deploy Backend (Nest)

```bash
ssh -o StrictHostKeyChecking=accept-new jpalmer@<nest-host>
cd /root/podium
docker compose up -d --build podium-backend
```

## Check Backend Health

```bash
curl -I https://<backend-domain>/openapi.json
```

Expected: HTTP `200`.

## Make User Superadmin

```bash
ssh -o StrictHostKeyChecking=accept-new jpalmer@<nest-host>
cd /root/podium
docker compose exec -T podium-backend python - <<'PY'
import asyncio
from sqlmodel import select
from podium.db.postgres.base import async_session_factory
from podium.db.postgres import User

EMAIL = "replace@domain.com"

async def main():
    async with async_session_factory() as s:
        user = (await s.execute(select(User).where(User.email == EMAIL))).scalars().first()
        if user is None:
            print("NOT_FOUND")
            return
        user.is_superadmin = True
        s.add(user)
        await s.commit()
        print("OK", user.email, user.is_superadmin)

asyncio.run(main())
PY
```

## Common Failures

- `502` from backend domain: backend container down or reverse-proxy route issue.
- Magic link says sent but no email arrives: missing `PODIUM_LOOPS_API_KEY` or wrong `PODIUM_LOOPS_TRANSACTIONAL_ID`.
- OAuth button present but fails: missing `PODIUM_SSO_CLIENT_ID/SECRET` or callback URL mismatch.

## Git Remote

Preferred fork remote for this project:

- `https://github.com/heycastawhat/kiwihacks-podium.git`
