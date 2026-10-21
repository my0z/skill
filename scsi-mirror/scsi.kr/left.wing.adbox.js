  const box = document.querySelector('.rounded-box');
  const triggerScroll = 100;   // 스크롤 200px 이상에서 위치 변경
  const fixedTop     = 200;    // 스크롤 시 고정될 top
  const initialTop   = 230;    // 초기 top

  window.addEventListener('scroll', () => {
    if (window.scrollY >= triggerScroll) {
      box.style.top = fixedTop + 'px';
    } else {
      box.style.top = initialTop + 'px';
    }
  });
