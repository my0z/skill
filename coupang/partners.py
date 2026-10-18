"""쿠팡 파트너스 공식 API: 키워드 검색 후 제휴링크(productUrl이 이미 제휴링크)를 CSV로 저장.
사용: COUPANG_ACCESS_KEY=.. COUPANG_SECRET_KEY=.. python3 partners.py 키워드 [개수]
"""
import csv, hashlib, hmac, json, os, sys, time, urllib.parse, urllib.request

HOST = "https://api-gateway.coupang.com"
BASE = "/v2/providers/affiliate_open_api/apis/openapi/v1"
DISCLOSURE = "이 포스팅은 쿠팡 파트너스 활동의 일환으로 이에 따른 일정액의 수수료를 제공받습니다"


def sign(method, path, query, access, secret, now=None):
    # 서명 시각이 서버와 어긋나면 거부되므로 실행 전에 시간 동기화 필수
    stamp = time.strftime("%y%m%dT%H%M%SZ", time.gmtime(now))
    msg = stamp + method + path + query
    sig = hmac.new(secret.encode(), msg.encode(), hashlib.sha256).hexdigest()
    return f"CEA algorithm=HmacSHA256, access-key={access}, signed-date={stamp}, signature={sig}"


def call(method, path, query="", body=None):
    access, secret = os.environ["COUPANG_ACCESS_KEY"], os.environ["COUPANG_SECRET_KEY"]
    req = urllib.request.Request(
        HOST + path + ("?" + query if query else ""),
        data=json.dumps(body).encode() if body else None,
        method=method,
        headers={"Authorization": sign(method, path, query, access, secret), "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def main(keyword, limit=10):
    q = urllib.parse.urlencode({"keyword": keyword, "limit": limit})
    products = call("GET", BASE + "/products/search", q)["data"]["productData"]
    with open(f"{keyword}.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["상품명", "가격", "로켓", "제휴링크", "이미지", "원본URL"])
        for p in products:
            w.writerow([p["productName"], p["productPrice"], p.get("isRocket"), p["productUrl"], p["productImage"], f"https://www.coupang.com/vp/products/{p['productId']}"])
    print(f"{len(products)}개 저장: {keyword}.csv\n문구 필수: {DISCLOSURE}")


if __name__ == "__main__":
    # 자체 검사: 같은 입력이면 같은 서명 / 시각이 다르면 다른 서명
    a = sign("GET", "/p", "k=1", "A", "S", now=0)
    assert a == sign("GET", "/p", "k=1", "A", "S", now=0) and a != sign("GET", "/p", "k=1", "A", "S", now=1)
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 10)
