// Import our custom CSS
import "../css/main.scss";

if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("assets/js/service-worker.js");
  });
}
