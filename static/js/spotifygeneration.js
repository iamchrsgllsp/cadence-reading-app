// spotifygeneration.js
document.addEventListener("DOMContentLoaded", function () {
  // Select all buttons with the new class
  const playlistButtons = document.querySelectorAll(".generate-playlist-btn");

  playlistButtons.forEach((button) => {
    button.addEventListener("click", function (event) {
      const btn = event.currentTarget; // The button that was clicked

      // 1. Get data directly from the button attributes
      const author = btn.getAttribute("data-author");
      const title = btn.getAttribute("data-title");

      // 2. Find the corresponding message element (assuming it's right after the button)
      // We use 'nextElementSibling' to reliably find the message box right after the button.
      const testPlaylistMsg = btn.nextElementSibling;

      // --- Existing Logic Starts Here ---

      btn.disabled = true;
      btn.style.opacity = "0.6";

      if (testPlaylistMsg) {
        testPlaylistMsg.innerHTML =
          '<div class="loading"><div class="spinner"></div> Creating your playlist...</div>';
        testPlaylistMsg.className = "alert";
      } else {
        console.error("Playlist message element not found.");
      }
      console.log(JSON.stringify({ author: author, title: title }));
      fetch("https://cadence-reading-app.onrender.com/testgen", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ author: author, title: title }),
      })
        .then((response) => response.json())
        .then((data) => {
          if (testPlaylistMsg) {
            if (data.playlist_id) {
              testPlaylistMsg.innerHTML =
                '✅ Playlist created! <a href="https://open.spotify.com/playlist/' +
                data.playlist_id +
                '" target="_blank" rel="noopener noreferrer" style="color: var(--primary-light); text-decoration: underline;">View on Spotify</a>';
            } else {
              testPlaylistMsg.textContent = "❌ Failed to create playlist.";
            }
          }
          btn.disabled = false;
          btn.style.opacity = "1";
        })
        .catch(() => {
          if (testPlaylistMsg) {
            testPlaylistMsg.textContent =
              "❌ Error occurred while creating playlist.";
          }
          btn.disabled = false;
          btn.style.opacity = "1";
        });
    });
  });
});
