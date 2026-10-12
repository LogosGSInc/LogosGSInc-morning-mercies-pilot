document.querySelectorAll('[data-catalog-search]').forEach(input => {
  const cards = [...document.querySelectorAll('[data-search]')];
  const status = document.querySelector('[data-search-status]');
  input.addEventListener('input', () => {
    const query = input.value.trim().toLowerCase();
    cards.forEach(card => { card.hidden = !card.dataset.search.includes(query); });
    const count = cards.filter(card => !card.hidden).length;
    status.textContent = query ? `${count} ${count === 1 ? 'release' : 'releases'} found.` : '';
  });
});
document.addEventListener('keydown', event => {
  if (event.key === 'Escape') document.querySelectorAll('.nav-menu[open]').forEach(menu => {
    menu.open = false;
    menu.querySelector('summary').focus();
  });
});
