"""Passo 1: login no portal Domínio Web (Thomson Reuters) via Playwright.

Uso: DW_USER=... DW_PASS=... python login_portal.py
Mantém o navegador aberto por 25 min (o AppController depende da sessão).
"""
import os
import time
from playwright.sync_api import sync_playwright

PERFIL = r"C:\Users\atend\.dominio-pw-p1"

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        PERFIL, channel="chrome", headless=False, no_viewport=True,
        args=["--profile-directory=Profile 1"])
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.goto("https://www.dominioweb.com.br/")
    page.wait_for_load_state("domcontentloaded")
    try:
        page.get_by_role("button", name="Entrar").click(timeout=15000)
    except Exception:
        pass
    if "/success" not in page.url:
        try:
            page.wait_for_selector("input[name=username]", timeout=20000)
            page.fill("input[name=username]", os.environ["DW_USER"])
            page.locator("button[name=action]").click()
            page.locator("input[type=password]").first.wait_for(timeout=15000)
            page.locator("input[type=password]").first.fill(os.environ["DW_PASS"])
            page.locator("button[type=submit]:visible").first.click()
        except Exception as e:
            print("login:", e)
    page.wait_for_timeout(8000)
    print("URL final:", page.url, flush=True)
    time.sleep(1500)
