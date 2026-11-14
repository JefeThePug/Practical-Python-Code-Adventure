(function () {
  const BUFFER = 20;
  const FALL_DURATION = 600;
  const BOUNCE_HEIGHT = 16;
  const BOUNCE_DURATION = 240;
  const HANG_TIME = 600;

  const impactSound = new Audio("/static/audio/2027/stomp.mp3");
  impactSound.preload = "auto";

  const foot = document.createElement("img");
  foot.src = "/static/images/2027/index/foot.webp";
  foot.alt = "";
  Object.assign(foot.style, {
    position: "fixed",
    left: "50%",
    translate: "-50% 0",
    bottom: `${BUFFER}px`,
    height: "100vh",
    width: "auto",
    maxHeight: "none",
    maxWidth: "none",
    margin: "0",
    zIndex: "9999",
    pointerEvents: "none",
    display: "none",
    willChange: "transform",
  });
  document.body.appendChild(foot);

  function stomp(callback) {
    foot.style.display = "block";

    // fall: from fully above the window to bottom - BUFFER, accelerating
    const fall = foot.animate(
      [{ transform: "translateY(-100%)" }, { transform: "translateY(0)" }],
      {
        duration: FALL_DURATION,
        easing: "cubic-bezier(0.32, 0, 0.67, 0)",
        fill: "forwards",
      },
    );

    fall.finished
      .then(() => {
        // landed: sound, then bounce
        impactSound.currentTime = 0;
        impactSound.play().catch(() => {});

        const bounce = foot.animate(
          [
            { transform: "translateY(0)", easing: "ease-out" },
            { transform: `translateY(-${BOUNCE_HEIGHT}px)`, easing: "ease-in" },
            { transform: "translateY(0)" },
          ],
          { duration: BOUNCE_DURATION * 2, fill: "forwards" },
        );

        return bounce.finished;
      })
      .then(() => setTimeout(callback, HANG_TIME));
  }

  window.addEventListener("pageshow", (e) => {
    if (!e.persisted) return;
    foot.getAnimations().forEach((a) => a.cancel());
    foot.style.display = "none";
  });

  document.addEventListener("click", function (e) {
    const link = e.target.closest("a");
    if (!link || !link.href) return;
    if (link.origin !== location.origin) return;
    if (!link.pathname.startsWith("/challenge")) return;
    if (e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey)
      return;
    e.preventDefault();
    const url = link.href;
    stomp(() => {
      window.location.href = url;
    });
  });

  document.addEventListener("submit", function (e) {
    const form = e.target;
    // "OK"/"Close" buttons in popups just close them; no stomp
    if (form.method === "dialog") return;
    e.preventDefault();
    stomp(() => {
      form.submit();
    });
  });
})();
