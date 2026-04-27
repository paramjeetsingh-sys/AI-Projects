import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List

# One folder at the repo root, next to ai-news-aggregator/
DIGESTS_DIR = Path(__file__).parent.parent / "digests"


def save_daily_digest(digest: Dict) -> Path:
    DIGESTS_DIR.mkdir(exist_ok=True)
    date = digest.get("date", datetime.now().strftime("%Y-%m-%d"))
    path = DIGESTS_DIR / f"{date}.json"
    with open(path, "w") as f:
        json.dump(digest, f, indent=2, ensure_ascii=False)
    print(f"Daily digest written → {path.name}")
    return path


def cleanup_old_digests(keep_days: int = 7) -> List[str]:
    if not DIGESTS_DIR.exists():
        return []
    cutoff = (datetime.now() - timedelta(days=keep_days)).date()
    removed = []
    for f in DIGESTS_DIR.glob("????-??-??.json"):
        try:
            if datetime.strptime(f.stem, "%Y-%m-%d").date() < cutoff:
                f.unlink()
                removed.append(f.name)
                print(f"Removed old digest: {f.name}")
        except ValueError:
            pass
    return removed
