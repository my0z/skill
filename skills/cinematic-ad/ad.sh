#!/usr/bin/env bash
# 상품 사진 2~3장 + 영상 1개 -> 영화 같은 상품광고 mp4 (ffmpeg만 사용)
# 사용: ad.sh -n "상품명" [-g "훅 카피"] [-s "슬로건"] [-c "CTA 예: brand.com"] [-m music.mp3] [-o out.mp4] 사진1 사진2 [사진3] 영상
# 마지막 사진 = 히어로 샷 (상품명이 그 위에 뜸)
set -euo pipefail
NAME="PRODUCT"; HOOK=""; SLOGAN=""; CTA=""; MUSIC=""; OUT="ad.mp4"
while getopts n:g:s:c:m:o: o; do case $o in n) NAME=$OPTARG;; g) HOOK=$OPTARG;; s) SLOGAN=$OPTARG;; c) CTA=$OPTARG;; m) MUSIC=$OPTARG;; o) OUT=$OPTARG;; *) exit 1;; esac; done
shift $((OPTIND-1))
[ $# -ge 3 ] && [ $# -le 4 ] || { echo "사진 2~3장 + 영상 1개 필요" >&2; exit 1; }
VIDEO=${!#}; PHOTOS=("${@:1:$#-1}"); HERO=${PHOTOS[-1]}
FONT=$(fc-match -f '%{file}' ':lang=ko:weight=bold')
W=1920 H=1080 FPS=25 BAR=140
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
ENC=(-an -c:v libx264 -preset veryfast -crf 18 -pix_fmt yuv420p -r $FPS)
COVER="scale=$W:$H:force_original_aspect_ratio=increase,crop=$W:$H,setsar=1"
# 상품 색은 살리고 대비와 따뜻한 톤만 살짝 + 약한 비네팅 + 2.39:1 레터박스 + 페이드
look() { echo "eq=contrast=1.08:saturation=1.05,colorbalance=rh=0.04:bh=-0.03,vignette=PI/7,drawbox=y=0:w=iw:h=$BAR:color=black:t=fill,drawbox=y=ih-$BAR:w=iw:h=$BAR:color=black:t=fill,fade=in:st=0:d=0.4,fade=out:st=$(echo "$1-0.4"|bc):d=0.4"; }
esc() { printf '%s' "$1" | sed "s/[\\:']/\\\\&/g"; }
txt() { # $1 글자 $2 크기 $3 y식 $4 등장초 $5 길이
  echo "drawtext=fontfile=$FONT:text='$(esc "$1")':fontsize=$2:fontcolor=white:shadowcolor=black@0.6:shadowx=3:shadowy=3:x=(w-tw)/2:y=$3:alpha='min(1,max(0,(t-$4)/0.8))*min(1,($5-t)/0.5)'"; }
DURS=()
seg() { DURS+=("$1"); }
photo() { # $1 사진 $2 출력 $3 길이 $4 줌식 $5 추가필터
  local f=$(( $3*FPS ))
  ffmpeg -nostdin -loglevel error -y -i "$1" -vf "$COVER,scale=$((W*2)):$((H*2)),zoompan=z='$4':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d=$f:s=${W}x$H:fps=$FPS,$(look "$3")${5:+,$5}" -t "$3" "${ENC[@]}" "$2"; seg "$3"; }
clip() { ffmpeg -nostdin -loglevel error -y -ss "$1" -i "$VIDEO" -t 3 -vf "$COVER,fps=$FPS,$(look 3)" "${ENC[@]}" "$2"; seg 3; }
card() { # $1 출력 $2 길이 $3 필터
  ffmpeg -nostdin -loglevel error -y -f lavfi -i "color=black:s=${W}x$H:d=$2:r=$FPS" -vf "$3" "${ENC[@]}" "$1"; seg "$2"; }
PUSH="1+0.10*on/75"   # 천천히 다가감
PULL="1.15-0.15*on/100" # 히어로 샷은 물러나며 전체 공개

DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$VIDEO")
at() { echo "d=$DUR-3; if (d<0) d=0; d*$1" | bc -l; }

[ -n "$HOOK" ] && card "$TMP/00.mp4" 3 "$(txt "$HOOK" 64 '(h-th)/2' 0.2 3)"
photo "${PHOTOS[0]}" "$TMP/01.mp4" 3 "$PUSH"
clip "$(at 0.2)" "$TMP/02.mp4"
[ ${#PHOTOS[@]} -eq 3 ] && photo "${PHOTOS[1]}" "$TMP/03.mp4" 3 "$PUSH"
clip "$(at 0.7)" "$TMP/04.mp4"
photo "$HERO" "$TMP/05.mp4" 4 "$PULL" "$(txt "$NAME" 120 "h-$BAR-th-60" 1.2 4)"
END="$(txt "$NAME" 96 '(h-th)/2-60' 0.2 4)"
[ -n "$SLOGAN" ] && END+=",$(txt "$SLOGAN" 48 '(h-th)/2+60' 0.8 4)"
[ -n "$CTA" ] && END+=",$(txt "$CTA" 36 "h-$BAR-th-40" 1.4 4)"
card "$TMP/06.mp4" 4 "$END"

ls "$TMP"/*.mp4 | sed "s/.*/file '&'/" > "$TMP/list.txt"
# 컷마다 저음 히트 + 드론 (음악 없을 때 기본 사운드)
T=0; BOOM=""
for d in "${DURS[@]::${#DURS[@]}-1}"; do T=$((T+d)); BOOM+="+0.9*gte(t,$T)*exp(-4*(t-$T))*sin(2*PI*40*(t-$T))"; done
TOTAL=$((T+${DURS[-1]}))
SFX="aevalsrc='0.25*sin(2*PI*55*t)*(0.6+0.4*sin(2*PI*0.25*t))$BOOM':s=48000:d=$TOTAL,lowpass=f=300"
if [ -n "$MUSIC" ]; then
  AUD=(-f lavfi -i "$SFX" -i "$MUSIC"); MIX="[1:a][2:a]amix=inputs=2:duration=first:weights=1 1.5"
else
  AUD=(-f lavfi -i "$SFX"); MIX="[1:a]anull"
fi
ffmpeg -nostdin -loglevel error -y -f concat -safe 0 -i "$TMP/list.txt" "${AUD[@]}" \
  -filter_complex "$MIX,afade=in:d=1,afade=out:st=$((TOTAL-2)):d=2,loudnorm=I=-14[a]" \
  -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k -t $TOTAL -movflags +faststart "$OUT"
echo "$OUT (${TOTAL}s)"
