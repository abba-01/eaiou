const cardSlideItems = document.querySelectorAll(".my-card-item");

cardSlideItems.forEach((cardSlide) => {
  let startX = null;
  let currentTranslation = 0; // Tracks the current translation state

  function handleStart(e) {
    e.preventDefault();
    startX = e.type.includes("mouse") ? e.clientX : e.touches[0].clientX;
  }

  function handleMove(e) {
    if (startX === null) return; // Ensure a valid start position
    e.preventDefault();

    const x = e.type.includes("mouse") ? e.clientX : e.touches[0].clientX;
    const diff = x - startX;
    if (Math.abs(diff) > 50) {
      // Threshold for triggering sliding
      if (diff < 0 && currentTranslation > -2.1) {
        slideLeft();
      } else if (diff > 0 && currentTranslation < 0) {
        slideRight();
      }
      startX = null; // Reset to avoid repeated triggering
    }
  }

  function handleEnd() {
    startX = null; // Reset on touch end
  }

  function slideLeft() {
    currentTranslation -= 3; // Move left
    cardSlide.style.transform = `translateX(${currentTranslation}rem)`;
  }

  function slideRight() {
    currentTranslation += 3; // Move right
    cardSlide.style.transform = `translateX(${currentTranslation}rem)`;
  }

  cardSlide.addEventListener("mousedown", handleStart);
  cardSlide.addEventListener("mousemove", handleMove);
  cardSlide.addEventListener("mouseup", handleEnd);
  cardSlide.addEventListener("mouseleave", handleEnd);
  // Touch event listeners
  cardSlide.addEventListener("touchstart", handleStart, { passive: false });
  cardSlide.addEventListener("touchmove", handleMove, { passive: false });
  cardSlide.addEventListener("touchend", handleEnd);
  cardSlide.addEventListener("touchcancel", handleEnd);
});
