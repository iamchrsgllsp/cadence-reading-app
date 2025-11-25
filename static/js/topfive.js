// This array will be the live JavaScript store for the Top Five list
let currentRecsList = window.INITIAL_RECS || [];

/**
 * Renders the book list items into the #top-five-list element.
 */
function renderBookList(data) {
  const listElement = document.getElementById('top-five-list');
  if (!listElement) {
    console.error("Target list element 'top-five-list' not found.");
    return;
  }

  listElement.innerHTML = ''; // Clear existing list

  if (data.length === 0) {
    listElement.innerHTML = '<li class="empty-state">Drag books here to start your Top Five!</li>';
    return;
  }

  data.forEach((book, index) => {
    const listItem = document.createElement('li');
    listItem.textContent = `${index + 1}. ${book[1]}`;
    listItem.dataset.bookId = book[0];
    listItem.dataset.position = index;
    listItem.classList.add('ranked-item');
    listElement.appendChild(listItem);
  });
}

/**
 * Get the position where the item should be inserted based on mouse Y coordinate
 */
function getInsertPosition(list, clientY) {
  const items = [...list.querySelectorAll('li:not(.empty-state)')];
  
  if (items.length === 0) return 0;
  
  for (let i = 0; i < items.length; i++) {
    const rect = items[i].getBoundingClientRect();
    const midpoint = rect.top + rect.height / 2;
    
    if (clientY < midpoint) {
      return i;
    }
  }
  
  return items.length;
}

// --- Initialization and Event Listeners ---
document.addEventListener('DOMContentLoaded', () => {
  // 1. Initial Render
  renderBookList(currentRecsList);
  console.log("Top Five List Initialized. Data:", currentRecsList);

  // 2. DRAG AND DROP LOGIC
  const topFiveList = document.getElementById('top-five-list');

  if (!topFiveList) return;

  let draggedItem = null;
  let dropIndicator = null;

  // Create drop indicator element
  function createDropIndicator() {
    if (!dropIndicator) {
      dropIndicator = document.createElement('div');
      dropIndicator.className = 'drop-indicator';
      dropIndicator.style.cssText = 'height: 2px; background: var(--primary-light, #4A90E2); margin: 4px 0; transition: all 0.2s;';
    }
    return dropIndicator;
  }

  // --- Universal Drag Start (Capture the item being dragged) ---
  document.addEventListener('dragstart', (e) => {
    if (e.target.classList.contains('drag-item')) {
      draggedItem = e.target;
      setTimeout(() => e.target.classList.add('dragging'), 0);

      // Pass the book ID and title data
      e.dataTransfer.setData('text/plain', e.target.dataset.bookId);
      e.dataTransfer.setData('text/html', e.target.textContent);
      e.dataTransfer.effectAllowed = 'copy';
    }
  });

  // --- Universal Drag End (Clean up styles) ---
  document.addEventListener('dragend', (e) => {
    if (e.target.classList.contains('drag-item')) {
      e.target.classList.remove('dragging');
    }
    topFiveList.classList.remove('drag-over-list');
    if (dropIndicator && dropIndicator.parentNode) {
      dropIndicator.remove();
    }
    draggedItem = null;
  });

  // --- Drag Over (Allows Drop on the Top Five List and shows position) ---
  topFiveList.addEventListener('dragover', (e) => {
    e.preventDefault(); // ESSENTIAL: Allows the drop event to fire
    topFiveList.classList.add('drag-over-list');
    e.dataTransfer.dropEffect = 'copy';

    // Show drop indicator at insertion point
    const insertPos = getInsertPosition(topFiveList, e.clientY);
    const items = [...topFiveList.querySelectorAll('li:not(.empty-state)')];
    const indicator = createDropIndicator();
    
    if (items.length === 0) {
      topFiveList.appendChild(indicator);
    } else if (insertPos >= items.length) {
      items[items.length - 1].after(indicator);
    } else {
      items[insertPos].before(indicator);
    }
  });

  // --- Drag Leave ---
  topFiveList.addEventListener('dragleave', (e) => {
    // Only remove if actually leaving the list
    if (!topFiveList.contains(e.relatedTarget)) {
      topFiveList.classList.remove('drag-over-list');
      if (dropIndicator && dropIndicator.parentNode) {
        dropIndicator.remove();
      }
    }
  });

  // --- Drop Logic on the Top Five List ---
  topFiveList.addEventListener('drop', (e) => {
    e.preventDefault();
    topFiveList.classList.remove('drag-over-list');
    
    if (dropIndicator && dropIndicator.parentNode) {
      dropIndicator.remove();
    }

    // Only proceed if a drag-item was successfully started
    if (draggedItem) {
      const newBookId = e.dataTransfer.getData('text/plain');
      const newBookTitle = e.dataTransfer.getData('text/html');
      
      // Get the insertion position based on drop location
      const insertPos = getInsertPosition(topFiveList, e.clientY);

      // Check if the book is already in currentRecsList (by ID)
      const existingIndex = currentRecsList.findIndex(book => book[0] == newBookId);
      
      if (existingIndex !== -1) {
        alert("That book is already in your Top Five!");
        return;
      }

      // Create new book entry
      const newBook = [parseInt(newBookId), newBookTitle.trim()];
      
      // Insert at the specified position
      currentRecsList.splice(insertPos, 0, newBook);
      
      // If we now have more than 5 books, remove the last one
      if (currentRecsList.length > 5) {
        const removed = currentRecsList.pop();
        console.log(`Removed book: ${removed[1]} (list was full)`);
      }

      // Re-render the list to update the UI
      renderBookList(currentRecsList);

      console.log(`Added Book ID ${newBookId} at position ${insertPos + 1}. New data:`, currentRecsList);
    }
  });
});
