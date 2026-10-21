window.addEventListener('scroll', function() {
    const logo = document.getElementById('logo');
    const currentScrollY = window.scrollY;

    if (currentScrollY > 160) {
        logo.style.position = 'fixed';
        logo.style.top = ''; // top 제거
        logo.style.top = '0px'; // 하단에서 200px 위에 고정
        logo.style.transform = 'translateX(-50%) scale(0.8)';
        logo.style.opacity = '1';
    } else {
        logo.style.position = 'absolute';
        logo.style.bottom = ''; // bottom 제거
        logo.style.top = '40px'; // 상단으로 복귀
        const scale = 1 - (currentScrollY / 160) * (1 - 0.8);
        const opacity = 1 - (currentScrollY / 160) * (1 - 0.5);
        logo.style.transform = `translateX(-50%) scale(${scale})`;
        logo.style.opacity = `${opacity}`;
    }
});