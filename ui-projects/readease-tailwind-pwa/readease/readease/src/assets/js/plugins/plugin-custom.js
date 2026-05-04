"use strict";

const onboardingSlider = new Swiper(".onboarding-slider", {
  spaceBetween: 1,
  slidesPerView: 1,
  slidesToShow: 1,
  navigation: {
    nextEl: ".ara-next",
  },
  pagination: {
    el: ".onBoardingsliderPagingation",
    clickable: true,
  },
});

const nextButton = document.querySelector(".next-button");

onboardingSlider.on("reachEnd", function () {
  nextButton.addEventListener("click", () => {
    window.location.href = `./sign-up.html`;
  });
});

const featuredBooksSlider = new Swiper(".featured-books-slider", {
  spaceBetween: 16,
  slidesPerView: 2.6,
  slidesToShow: 1,
});

const popularAuthorSlider = new Swiper(".popular-author-slider", {
  spaceBetween: 20,
  slidesPerView: 5,
  slidesToShow: 1,
});

const categoriesSlider = new Swiper(".categories-slider", {
  spaceBetween: 20,
  slidesPerView: 2.2,
  slidesToShow: 1,
});

const featuredAudioBooksSlider = new Swiper(".featured-audio-books-slider", {
  spaceBetween: 16,
  slidesPerView: 2.6,
  slidesToShow: 1,
});

const continueReadingSlider = new Swiper(".continue-reading-slider", {
  spaceBetween: 16,
  slidesPerView: 1.1,
  slidesToShow: 1,
});

const audioBooksSlider = new Swiper(".audio-book-slider", {
  spaceBetween: 16,
  slidesPerView: 1.25,
  slidesToShow: 1,
  navigation: {
    nextEl: ".ara-next",
  },
});
