const vid = document.getElementById('vid');
const replayBtn = document.getElementById('replay-btn');

replayBtn.addEventListener('click', () => {
    vid.pause();
    vid.currentTime = 0;
    vid.play();
});
