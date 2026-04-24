import os
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "開啟可持久化的瀏覽器 Session，供蝦皮/淘寶登入與驗證後供後端備援使用。"

    def add_arguments(self, parser):
        parser.add_argument(
            "--provider",
            choices=["all", "shopee", "taobao"],
            default="all",
            help="要先登入哪個平台。",
        )
        parser.add_argument(
            "--channel",
            default=str(os.getenv("BROWSER_CHANNEL", "msedge")).strip() or "msedge",
            help="Playwright 瀏覽器通道（預設 msedge）。",
        )
        parser.add_argument(
            "--user-data-dir",
            default=str(os.getenv("BROWSER_USER_DATA_DIR", ".browser-profile")).strip() or ".browser-profile",
            help="持久化瀏覽器資料夾。建議固定同一路徑給後端備援使用。",
        )

    def handle(self, *args, **options):
        try:
            from playwright.sync_api import sync_playwright
        except Exception as exc:
            raise CommandError("尚未安裝 Playwright，請先安裝 requirements.txt。") from exc

        provider = options["provider"]
        channel = options["channel"]
        user_data_dir = Path(options["user_data_dir"]).resolve()
        user_data_dir.mkdir(parents=True, exist_ok=True)

        urls = []
        if provider in ("all", "shopee"):
            urls.append("https://shopee.tw/search?keyword=iphone")
        if provider in ("all", "taobao"):
            urls.append("https://s.taobao.com/search?q=iphone")

        self.stdout.write(self.style.NOTICE(f"使用瀏覽器資料夾：{user_data_dir}"))
        self.stdout.write(self.style.NOTICE("即將開啟瀏覽器，請完成登入/驗證後回到終端機按 Enter。"))

        try:
            with sync_playwright() as playwright:
                context = playwright.chromium.launch_persistent_context(
                    str(user_data_dir),
                    channel=channel,
                    headless=False,
                )

                for url in urls:
                    page = context.new_page()
                    page.goto(url, wait_until="domcontentloaded", timeout=120000)

                input("完成登入後按 Enter 關閉瀏覽器並儲存 Session... ")
                context.close()
        except Exception as exc:
            raise CommandError(f"開啟瀏覽器 Session 失敗：{exc}") from exc

        self.stdout.write(self.style.SUCCESS("Session 已儲存，可用於後端瀏覽器備援。"))
