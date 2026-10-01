#!/usr/bin/env bash
# 사진 2~3장 + 영상 1개 -> 시네마틱 예고편 mp4 (ffmpeg만 사용)
# 사용: trailer.sh -t "제목" [-g "태그라인"] [-c "COMING SOON"] [-m music.mp3] [-o out.mp4] 사진1 사진2 [사진3] 영상
set -euo pipefail
TITLE="UNTITLED"; TAG="어느 날 모든 것이 바뀌었다"; END="COMING SOON"; MUSIC=""; OUT="trailer.mp4"
while getopts t:g:c:m:o: o; do case $o in t) TITLE=$OPTARG;; g) TAG=$OPTARG;; c) END=$OPTARG;; m) MUSIC=$OPTARG;; o) OUT=$OPTARG;; *) exit 1;; esac; done
shift $((OPTIND-1))
[ $# -ge 3 ] && [ $# -le 4 ] || { echo "사진 2~3장 + 영상 1개 필요" >&2; exit 1; }
VIDEO=${!#}; PHOTOS=("${@:1:$#-1}")
FONT=$(fc-match -f '%{file}' ':lang=ko:weight=bold')
W=1920 H=1080 FPS=25 SEG=3 BAR=140
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
ENC=(-an -c:v libx264 -preset veryfast -crf 18 -pix_fmt yuv420p -r $FPS)
# 틸오렌지 그레이딩 + 비네팅 + 2.39:1 레터박스 + 페이드
GRADE="eq=contrast=1.15:saturation=0.85,colorbalance=rs=-0.05:bs=0.08:rh=0.08:bh=-0.06,vignette=PI/5,drawbox=y=0:w=iw:h=$BAR:color=black:t=fill,drawbox=y=ih-$BAR:w=iw:h=$BAR:color=black:t=fill,fade=in:st=0:d=0.4,fade=out:st=$(echo "$SEG-0.4"|bc):d=0.4"
COVER="scale=$W:$H:force_original_aspect_ratio=increase,crop=$W:$H,setsar=1"
esc() { printf '%s' "$1" | sed "s/[\\:']/\\\\&/g"; }
card() { # $1 파일 $2 글자 $3 크기
  ffmpeg -nostdin -loglevel error -y -f lavfi -i "color=black:s=${W}x$H:d=$SEG:r=$FPS" \
    -vf "drawtext=fontfile=$FONT:text='$(esc "$2")':fontsize=$3:fontcolor=white:x=(w-tw)/2:y=(h-th)/2:alpha='min(1,t/0.8)*min(1,($SEG-t)/0.6)'" "${ENC[@]}" "$1"; }
photo() { ffmpeg -nostdin -loglevel error -y -i "$1" -vf "$COVER,scale=$((W*2)):$((H*2)),zoompan=z='1+0.12*on/($SEG*$FPS)':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d=$((SEG*FPS)):s=${W}x$H:fps=$FPS,$GRADE" -t $SEG "${ENC[@]}" "$2"; }
clip() { ffmpeg -nostdin -loglevel error -y -ss "$1" -i "$VIDEO" -t $SEG -vf "$COVER,fps=$FPS,$GRADE" "${ENC[@]}" "$2"; }

DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$VIDEO")
at() { echo "d=$DUR-$SEG; if (d<0) d=0; d*$1" | bc -l; }  # 영상 길이 비율 지점

card "$TMP/00.mp4" "$TAG" 64
photo "${PHOTOS[0]}" "$TMP/01.mp4"
clip "$(at 0.2)" "$TMP/02.mp4"
photo "${PHOTOS[1]}" "$TMP/03.mp4"
clip "$(at 0.7)" "$TMP/04.mp4"
[ ${#PHOTOS[@]} -eq 3 ] && photo "${PHOTOS[2]}" "$TMP/05.mp4"
card "$TMP/06.mp4" "$TITLE" 140
card "$TMP/07.mp4" "$END" 56

ls "$TMP"/*.mp4 | sed "s/.*/file '&'/" > "$TMP/list.txt"
N=$(wc -l < "$TMP/list.txt"); TOTAL=$((N*SEG))
# 컷마다 저음 붐 + 드론 (음악 없을 때 기본 사운드)
BOOM=$(for i in $(seq 1 $((N-1))); do printf '+0.9*gte(t,%d)*exp(-4*(t-%d))*sin(2*PI*40*(t-%d))' $((i*SEG)) $((i*SEG)) $((i*SEG)); done)
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
