(function () {
  const lightbox = document.getElementById("art-lightbox");
  const stage = lightbox.querySelector(".art-lightbox-media");

  function openArt(media) {
    const { type, src, alt } = media.dataset;
    let el;

    if (type === "img") {
      el = document.createElement("img");
      el.alt = alt;
    } else {
      el = document.createElement("video");
      el.controls = true;
      el.autoplay = true;
      el.playsInline = true;
    }

    el.src = src;
    stage.replaceChildren(el);
    lightbox.showModal();
  }

  document.querySelectorAll(".art-media").forEach((media) => {
    media.addEventListener("click", () => openArt(media));
    media.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        openArt(media);
      }
    });
  });

  lightbox.addEventListener("click", (e) => {
    if (e.target === lightbox) lightbox.close();
  });

  lightbox.addEventListener("close", () => stage.replaceChildren());

  const SCROLL_KEY = "fanArtScrollY";

  document.querySelectorAll(".art-pagination a").forEach((link) => {
    link.addEventListener("click", () => {
      sessionStorage.setItem(SCROLL_KEY, String(window.scrollY));
    });
  });

  const saved = sessionStorage.getItem(SCROLL_KEY);
  if (saved !== null) {
    sessionStorage.removeItem(SCROLL_KEY);
    const y = parseInt(saved, 10);
    window.scrollTo(0, y);
    window.addEventListener("load", () => window.scrollTo(0, y));
  }
})();
