const list = document.getElementById('book-list');
console.log('Book list element:', list);

list.addEventListener('click', function(e) {
  // Find the closest li element (walks up the DOM tree)
  const li = e.target.closest('li');
  
  if (li && list.contains(li)) {
    console.log('Clicked item:', li);
    location.href = "/book/"+li.textContent;
    // or whatever attribute you need
    // Your code here
  }
});