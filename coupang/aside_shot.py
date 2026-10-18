"""Aside 브라우저에 CDP로 붙어 CSV의 상품 페이지를 캡처 (영상 소재용).
Aside를 --remote-debugging-port=9222 로 띄운 뒤 같은 PC에서 실행.
사용: python3 aside_shot.py 키워드.csv
"""
import csv, os, sys
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(os.environ.get("CDP_URL", "http://127.0.0.1:9222"))
    ctx = browser.contexts[0]  # 이미 로그인된 Aside 세션 재사용
    page = ctx.new_page()
    os.makedirs("shots", exist_ok=True)
    for i, row in enumerate(csv.DictReader(open(sys.argv[1], encoding="utf-8-sig"))):
        page.goto(row["원본URL"], wait_until="domcontentloaded")  # 제휴링크는 열지 않음: 본인 클릭은 약관 위반 소지
        page.screenshot(path=f"shots/{i:02d}.png")
        page.wait_for_timeout(3000)  # 사람처럼 간격 두기: 과도한 호출은 차단 위험
    page.close()
