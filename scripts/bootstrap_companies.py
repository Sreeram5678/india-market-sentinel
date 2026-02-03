from __future__ import annotations

import argparse
from pathlib import Path

from ims.core.settings import get_settings
from ims.storage.db import connect, init_db
from ims.storage.repos import Repos


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=Path, default=Path("data/seed_companies.csv"))
    args = ap.parse_args()

    settings = get_settings()
    init_db(settings.db_path)

    if not args.seed.exists():
        raise SystemExit(f"Seed file not found: {args.seed}")

    with connect(settings.db_path) as conn:
        repos = Repos(conn)
        for line in args.seed.read_text(encoding="utf-8").splitlines():
            if not line.strip() or line.startswith("#"):
                continue
            parts = [p.strip() for p in line.split(",")]
            if len(parts) < 3:
                continue
            symbol, name, bse_scrip = parts[0], parts[1], parts[2]
            repos.upsert_company(symbol=symbol, name=name, exchange="BSE", bse_scrip_code=bse_scrip)
    print(f"Seeded companies into {settings.db_path}")


if __name__ == "__main__":
    main()

