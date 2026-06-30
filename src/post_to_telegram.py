import os
import requests

TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = "@psychedelics_for_real"


def _send(text: str, dry_run: bool = False):
    if dry_run:
        print(f"[DRY RUN] Would send to Telegram:\n{text}\n{'-'*40}")
        return
    if not BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")
    resp = requests.post(
        TELEGRAM_API.format(token=BOT_TOKEN),
        json={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML", "disable_web_page_preview": False},
        timeout=15,
    )
    if resp.status_code != 200:
        print(f"Telegram error {resp.status_code}: {resp.text}")


def post_article(item: dict, dry_run: bool = False):
    authors = ", ".join(item.get("authors", [])) if item.get("authors") else ""
    author_line = f"👤 {authors}\n" if authors else ""
    date_line = f"📅 {item['date']}\n" if item.get("date") else ""

    en_summary = item["summaries"].get("en", "")
    ru_summary = item["summaries"].get("ru", "")

    text = (
        f"<b>{item['title']}</b>\n"
        f"📰 {item['source']}  {date_line}"
        f"{author_line}"
        f"\n🇬🇧 {en_summary}\n"
        f"\n🇷🇺 {ru_summary}\n"
        f"\n🔗 <a href='{item['url']}'>Read original</a>"
    )
    _send(text, dry_run=dry_run)


def post_summary(total: int, relevant: int, skipped: int, dry_run: bool = False):
    text = (
        f"📊 <b>Daily scan complete</b>\n"
        f"Total fetched: {total}\n"
        f"Already seen (skipped): {skipped}\n"
        f"Relevant today: {relevant}"
    )
    _send(text, dry_run=dry_run)


def post_error(message: str, dry_run: bool = False):
    _send(f"⚠️ <b>Error during scan</b>\n{message[:200]}", dry_run=dry_run)
