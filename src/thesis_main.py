import os
import sys

from fetch_theses import fetch_all_theses
from filter_theses import process_theses
from post_to_telegram import post_error, post_summary
from seen_articles import theses_store

DRY_RUN = os.environ.get("DRY_RUN", "false").lower() == "true"


def post_thesis(item: dict, dry_run: bool = False):
    from post_to_telegram import _send
    authors = ", ".join(item.get("authors", [])) if item.get("authors") else ""
    text = (
        f"🎓 <b>{item['title']}</b>\n"
        f"📰 {item['source']}  📅 {item.get('date', '')}\n"
        + (f"👤 {authors}\n" if authors else "")
        + (f"🏛 {item.get('institution', '')}\n" if item.get("institution") else "")
        + (f"📋 Level: {item.get('level', '')}\n" if item.get("level") else "")
        + f"\n🔗 <a href='{item['url']}'>View thesis</a>"
    )
    _send(text, dry_run=dry_run)


def main():
    print(f"Starting weekly thesis scan (dry_run={DRY_RUN})")
    try:
        all_theses = fetch_all_theses()
        print(f"Fetched {len(all_theses)} theses total")

        new_theses = [t for t in all_theses if not theses_store.is_seen(t.url)]
        skipped = len(all_theses) - len(new_theses)
        print(f"New: {len(new_theses)}, skipped: {skipped}")

        results = process_theses(new_theses)
        print(f"Relevant: {len(results)}")

        for item in results:
            post_thesis(item, dry_run=DRY_RUN)

        post_summary(
            total=len(all_theses),
            relevant=len(results),
            skipped=skipped,
            dry_run=DRY_RUN,
        )

        if not DRY_RUN:
            for t in new_theses:
                theses_store.mark_seen(t.url)
            print("Done. seen_theses.json updated.")
        else:
            print("Dry run complete.")

    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        post_error(str(e), dry_run=DRY_RUN)
        sys.exit(1)


if __name__ == "__main__":
    main()
