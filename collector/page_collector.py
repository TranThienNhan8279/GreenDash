"""Đo trang web THUỘC QUYỀN CỦA BẠN bằng Playwright rồi gửi /api/v1/ingest/page.
Danh sách URL lấy từ API (chỉ URL đã đăng ký bằng tools/khoi_tao.py --url ...). Tôn trọng robots.txt.
  pip install playwright httpx && playwright install chromium
  python collector/page_collector.py            # đo một lần
  python collector/page_collector.py --lap-phut 60
"""
import argparse, os, time, urllib.robotparser
from datetime import datetime, timezone
from urllib.parse import urlparse

import httpx
from playwright.sync_api import sync_playwright

UA = "GreenDashBot/1.0 (do website cua chinh chu)"


def duoc_phep(url: str) -> bool:
    p = urlparse(url)
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url("%s://%s/robots.txt" % (p.scheme, p.netloc))
    try:
        rp.read()
    except Exception:
        return True          # không đọc được robots.txt (không tồn tại) thì coi như cho phép
    return rp.can_fetch("GreenDashBot", url)


def do_mot_trang(browser, url: str) -> dict:
    ctx = browser.new_context(user_agent=UA)
    page = ctx.new_page()
    reqs, hong = [], []
    page.on("requestfinished", lambda r: reqs.append(r))
    page.on("requestfailed", lambda r: hong.append(r))
    page.goto(url, wait_until="load", timeout=45000)
    try:
        page.wait_for_load_state("networkidle", timeout=10000)
    except Exception:
        pass
    tong = anh = js = css = 0.0
    loi = len(hong)
    for r in reqs:
        s = r.sizes()
        b = (s.get("responseBodySize", 0) + s.get("responseHeadersSize", 0)) / 1024.0
        tong += b
        rt = r.resource_type
        anh += b if rt == "image" else 0
        js += b if rt == "script" else 0
        css += b if rt == "stylesheet" else 0
        resp = r.response()
        if resp is not None and resp.status >= 400:
            loi += 1
    nav = page.evaluate("() => { const n = performance.getEntriesByType('navigation')[0]; "
                        "return n ? {ttfb: n.responseStart, tai: n.loadEventEnd} : {ttfb: 0, tai: 0}; }")
    so = len(reqs) + len(hong)
    ctx.close()
    return {"url": url, "thoiDiem": datetime.now(timezone.utc).isoformat(), "tongKB": round(tong, 2), "soRequest": so,
            "anhKB": round(anh, 2), "jsKB": round(js, 2), "cssKB": round(css, 2),
            "ttfbMs": round(max(nav["ttfb"], 0), 2), "taiMs": round(max(nav["tai"], 0), 2),
            "tyLeLoi": round(loi / so * 100, 2) if so else 0.0}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url-api", default=os.environ.get("GREENDASH_URL", "http://localhost:8000"))
    ap.add_argument("--lap-phut", type=int, default=0)
    ap.add_argument("--loc", default="", help="chỉ đo URL có chứa chuỗi này, ví dụ localhost hoặc infinityfreeapp")
    a = ap.parse_args()
    khoa = os.environ.get("GREENDASH_API_KEY", "")
    if not khoa:
        raise SystemExit("Thiếu biến môi trường GREENDASH_API_KEY")
    h = {"X-API-Key": khoa}
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        while True:
            urls = httpx.get(a.url_api + "/api/v1/ingest/page/urls", headers=h, timeout=15).json()["urls"]
            if a.loc:
                urls = [u for u in urls if a.loc in u]
            for u in urls:
                if not duoc_phep(u):
                    print("Bỏ qua (robots.txt không cho phép):", u)
                    continue
                try:
                    d = do_mot_trang(browser, u)
                    r = httpx.post(a.url_api + "/api/v1/ingest/page", headers=h, json=d, timeout=15)
                    print(u, d["tongKB"], "KB", r.status_code)
                except Exception as e:
                    print("Lỗi đo", u, e)
                time.sleep(3)            # tần suất thấp
            if a.lap_phut <= 0:
                break
            time.sleep(a.lap_phut * 60)
        browser.close()


if __name__ == "__main__":
    main()
