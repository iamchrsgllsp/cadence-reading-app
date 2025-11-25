const testPlaylistBtn = document.getElementById("testPlaylistBtn");
const testPlaylistMsg = document.getElementById("testPlaylistMsg");

if (testPlaylistBtn) {
  testPlaylistBtn.onclick = function () {
    const bookCard = document.getElementById("playlistcard{{loop.index}}");
    const author = bookCard.getAttribute("author");
    const title = bookCard.getAttribute("title");
    this.disabled = true;
    this.style.opacity = "0.6";
    testPlaylistMsg.innerHTML =
      '<div class="loading"><div class="spinner"></div> Creating your playlist...</div>';
    testPlaylistMsg.className = "alert";

    fetch("http://127.0.0.1:3000/testgen", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ author: author, title: title }),
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.playlist_id) {
          testPlaylistMsg.innerHTML =
            '✅ Playlist created! <a href="https://open.spotify.com/playlist/' +
            data.playlist_id +
            '" target="_blank" rel="noopener noreferrer" style="color: var(--primary-light); text-decoration: underline;">View on Spotify</a>';
        } else {
          testPlaylistMsg.textContent = "❌ Failed to create playlist.";
        }
        this.disabled = false;
        this.style.opacity = "1";
      })
      .catch(() => {
        testPlaylistMsg.textContent =
          "❌ Error occurred while creating playlist.";
        this.disabled = false;
        this.style.opacity = "1";
      });
  };
} // Properly closed DOMContentLoaded
