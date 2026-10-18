"""세력 흔적 스캐너: 거래대금 상위 종목에서 양봉 거래량 급증을 찾는다.

사용: python3 whale_scan.py [기준일 YYYYMMDD] [상위N] [탐색일수] [최근일수]
의존: pip install pykrx
"""
import sys
from datetime import datetime, timedelta

# 거래량이 20일 평균의 몇 배인지로 등급을 나눈다
TIERS = [("purple", 5.0), ("orange", 3.0), ("yellow", 2.0)]


def classify(rows, avg_win=20):
    """rows: [(open, close, volume)] 오래된 순. 반환: [(index, tier)]"""
    out = []
    for i in range(avg_win, len(rows)):
        o, c, v = rows[i]
        avg = sum(r[2] for r in rows[i - avg_win:i]) / avg_win
        if c <= o or avg <= 0:
            continue
        ratio = v / avg
        for name, th in TIERS:
            if ratio >= th:
                out.append((i, name))
                break
    return out


def scan(date, top_n=500, lookback=60, recent=5):
    from pykrx import stock  # 지연 임포트로 테스트 시 설치 불필요

    day = stock.get_market_ohlcv(date, market="ALL")
    day = day.sort_values("거래대금", ascending=False).head(top_n)
    start = (datetime.strptime(date, "%Y%m%d") - timedelta(days=lookback * 2)).strftime("%Y%m%d")
    hits = []
    for tk in day.index:
        # shortcut: 종목별 순차 조회라 느리다. 느리면 캐시나 병렬화로 올린다
        df = stock.get_market_ohlcv(start, date, tk).tail(lookback + 20)
        if len(df) < 25:
            continue
        rows = list(zip(df["시가"], df["종가"], df["거래량"]))
        sig = classify(rows)
        counts = {n: 0 for n, _ in TIERS}
        for _, t in sig:
            counts[t] += 1
        last = [(i, t) for i, t in sig if i >= len(rows) - recent]
        if not last:
            continue
        hits.append({
            "ticker": tk,
            "name": stock.get_market_ticker_name(tk),
            "close": int(rows[-1][1]),
            "last_signal": df.index[last[-1][0]].strftime("%m/%d"),
            "counts": counts,
        })
    hits.sort(key=lambda h: (h["counts"]["purple"], h["counts"]["orange"]), reverse=True)
    return hits


def main():
    a = sys.argv[1:]
    date = a[0] if a else datetime.now().strftime("%Y%m%d")
    top_n, lookback, recent = (int(x) for x in (a[1:4] + ["500", "60", "5"][len(a[1:4]):]))
    hits = scan(date, top_n, lookback, recent)
    print(f"매집 각인 종목 {len(hits)} | 상위 {top_n} | 탐색 {lookback}일 | 최근 {recent}일 | {date}")
    for i, h in enumerate(hits, 1):
        c = h["counts"]
        print(f"{i:>2} {h['name']}({h['ticker']}) {h['close']:,}원 "
              f"신호 {h['last_signal']} 보라 {c['purple']} 주황 {c['orange']} 노랑 {c['yellow']}")


def _selfcheck():
    flat = [(100, 100, 1000)] * 20
    assert classify(flat) == []
    assert classify(flat + [(100, 110, 5000)]) == [(20, "purple")]
    assert classify(flat + [(100, 110, 3000)]) == [(20, "orange")]
    assert classify(flat + [(100, 110, 2000)]) == [(20, "yellow")]
    assert classify(flat + [(110, 100, 9000)]) == []  # 음봉은 제외
    print("ok")


if __name__ == "__main__":
    _selfcheck() if sys.argv[1:] == ["--test"] else main()
