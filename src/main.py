import os
import sys

from fetch_sources import fetch_all
from filter_and_summarize import process_articles
from post_to_telegram import post_article, post_summary, post_error
from seen_articles import articles_store

DRY_RUN = os.environ.get("DRY_RUN", "false").lower() == "true"


def main():
    print(f"Starting daily scan (dry_run={DRY_RUN})")
    try:
        all_articles = fetch_all()
        print(f"Fetched {len(all_articles)} articles total")

        new_articles = [a for a in all_articles if not articles_store.is_seen(a.url)]
        skipped = len(all_articles) - len(new_articles)
        print(f"New (not yet seen): {len(new_articles)}, skipped: {skipped}")

        results = process_articles(new_articles)
        print(f"Relevant after filtering: {len(results)}")

        for item in results:
            post_article(item, dry_run=DRY_RUN)
            if not DRY_RUN:
                articles_store.mark_seen(item["url"])

        post_summary(
            total=len(all_articles),
            relevant=len(results),
            skipped=skipped,
            dry_run=DRY_RUN,
        )

        if DRY_RUN:
            print("Dry run complete — nothing was posted or saved.")
        else:
            # Mark all fetched articles as seen (not just relevant ones)
            for a in new_articles:
                articles_store.mark_seen(a.url)
            print("Done. seen.json updated.")

    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        post_error(str(e), dry_run=DRY_RUN)
        sys.exit(1)


if __name__ == "__main__":
    main()
