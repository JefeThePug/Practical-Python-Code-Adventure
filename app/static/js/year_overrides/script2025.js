// Section border wipes: two 30px strips of the 2025B border sweep up each
// section, half a cycle apart (::before and ::after).
// The masks live in style2025.css; this only moves them, via --wipe-a / --wipe-b.
(function () {
  const DURATION = 6000; // one full sweep, ms
  const FPS = 20; // a slow sweep looks the same at 20fps, for a third of the repaints

  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

  const sections = document.querySelectorAll(".section:not(header)");
  if (!sections.length) return;

  // only sections on screen get repainted
  const visible = new Set();
  if ("IntersectionObserver" in window) {
    const observer = new IntersectionObserver((entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting) visible.add(entry.target);
        else visible.delete(entry.target);
      }
    });
    sections.forEach((section) => observer.observe(section));
  } else {
    sections.forEach((section) => visible.add(section));
  }

  // bottom (100%) to top (0%) over 60% of the cycle, then off the top (-100%)
  function wipePosition(t) {
    return t < 0.6 ? 100 - (t / 0.6) * 100 : -((t - 0.6) / 0.4) * 100;
  }

  let last = 0;
  function frame(now) {
    requestAnimationFrame(frame);
    if (now - last < 1000 / FPS) return;
    last = now;

    const t = (now % DURATION) / DURATION;
    const a = `${wipePosition(t)}%`;
    const b = `${wipePosition((t + 0.5) % 1)}%`;
    visible.forEach((section) => {
      section.style.setProperty("--wipe-a", a);
      section.style.setProperty("--wipe-b", b);
    });
  }

  requestAnimationFrame(frame);
})();
