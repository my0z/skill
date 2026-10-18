"""세력 흔적 스캐너: 3년치 수급 패널에서 기관+외국인 순매수 급증 양봉을 찾는다.

사용: python3 whale_scan.py [패널폴더] [탐색일수] [최근일수] [상위N]
      python3 whale_scan.py --bt [패널폴더]   3년 백테스트 (신호 다음날 시가 수익률)
      python3 whale_scan.py --test
의존: pandas pyarrow
패널: day.stock 저장소의 surge_data/history/krx_*.parquet (open close inst foreign)
"""
import glob
import os
import sys

import pandas as pd

DIR = os.environ.get("PANEL_DIR", "/home/user/my0z/day.stock/surge_data/history")
# 순매수가 20일 평균 절댓값의 몇 배인지로 등급을 나눈다
TIERS = [("purple", 5.0), ("orange", 3.0), ("yellow", 2.0)]


def load(path=DIR):
    pn = pd.concat(pd.read_parquet(p) for p in sorted(glob.glob(f"{path}/krx_*.parquet")))
    return pn[~pn.index.duplicated(keep="last")].sort_index()


def signals(pn, win=20):
    """date x ticker 등급 표. 값은 purple orange yellow 또는 빈칸."""
    flow = (pn["inst"] + pn["foreign"]).unstack("ticker")
    o = pn["open"].unstack("ticker")
    c = pn["close"].unstack("ticker")
    ratio = flow / flow.abs().rolling(win).mean().shift(1)
    ok = (c > o) & (flow > 0)
    tier = pd.DataFrame("", index=flow.index, columns=flow.columns)
    for name, th in reversed(TIERS):  # 낮은 등급부터 덮어쓴다
        tier = tier.mask(ok & (ratio >= th), name)
    return tier, o


def scan(pn, lookback=60, recent=5, top_n=500):
    tier, _ = signals(pn)
    close = pn["close"].unstack("ticker")
    liq = (pn["inst"].abs() + pn["foreign"].abs()).unstack("ticker").tail(20).mean()
    pool = set(liq.nlargest(top_n).index)  # shortcut: 거래대금 대신 수급 규모로 대체. 거래량 데이터 받으면 교체
    win = tier.tail(lookback)
    out = []
    for tk in win.columns:
        col = win[tk]
        if tk not in pool or not (col.tail(recent) != "").any():
            continue
        last = col.tail(recent)[lambda s: s != ""].index[-1]
        out.append((tk, int(close[tk].iloc[-1]), last.strftime("%m/%d"),
                    (col == "purple").sum(), (col == "orange").sum(), (col == "yellow").sum()))
    return sorted(out, key=lambda r: (r[3], r[4]), reverse=True)


def backtest(pn):
    tier, o = signals(pn)
    nxt = o.shift(-1) / pn["close"].unstack("ticker") - 1  # 종가 매수 다음날 시가 매도
    for name, _ in TIERS:
        r = nxt.where(tier == name).stack().dropna()
        print(f"{name:<7} n={len(r):>6} 평균 {r.mean()*100:+.2f}% 승률 {(r > 0).mean()*100:.1f}%")
    r = nxt.stack().dropna()
    print(f"{'전체':<7} n={len(r):>6} 평균 {r.mean()*100:+.2f}% 승률 {(r > 0).mean()*100:.1f}%")


def main():
    a = [x for x in sys.argv[1:] if x != "--bt"]
    pn = load(a[0] if a else DIR)
    if "--bt" in sys.argv:
        return backtest(pn)
    lookback, recent, top_n = (int(x) for x in (a[1:4] + ["60", "5", "500"][len(a[1:4]):]))
    hits = scan(pn, lookback, recent, top_n)
    d = pn.index.get_level_values("date").max()
    print(f"매집 각인 종목 {len(hits)} | 상위 {top_n} | 탐색 {lookback}일 | 최근 {recent}일 | {d:%Y-%m-%d}")
    for i, (tk, cl, ls, p, og, y) in enumerate(hits, 1):
        print(f"{i:>2} {tk} {cl:,}원 신호 {ls} 보라 {p} 주황 {og} 노랑 {y}")


def _selfcheck():
    d = pd.bdate_range("2026-01-01", periods=22)
    idx = pd.MultiIndex.from_product([d, ["A"]], names=["date", "ticker"])
    pn = pd.DataFrame({"open": 100.0, "close": 100.0, "inst": 1000.0, "foreign": 0.0}, index=idx)
    pn.iloc[-1] = [100, 110, 5000, 0]
    t, _ = signals(pn)
    assert t["A"].iloc[-1] == "purple" and (t["A"].iloc[:-1] == "").all()
    pn.iloc[-1] = [110, 100, 5000, 0]  # 음봉 제외
    assert signals(pn)[0]["A"].iloc[-1] == ""
    print("ok")


if __name__ == "__main__":
    _selfcheck() if "--test" in sys.argv else main()
