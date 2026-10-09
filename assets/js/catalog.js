(() => {
  const cards = [...document.querySelectorAll('.catalog-card')];
  const search = document.querySelector('#catalog-search');
  const series = document.querySelector('#series-filter');
  const buttons = [...document.querySelectorAll('[data-filter]')];
  let format = 'all';
  function filter() {
    const query = search.value.trim().toLocaleLowerCase();
    let count = 0;
    cards.forEach(card => {
      const visible = (format === 'all' || card.dataset.type === format)
        && (!series.value || card.dataset.series === series.value)
        && (!query || card.textContent.toLocaleLowerCase().includes(query));
      card.hidden = !visible;
      if (visible) count++;
    });
    document.querySelector('#catalog-count').textContent = `${count} ${count === 1 ? 'piece' : 'pieces'} in the collection`;
    document.querySelector('#catalog-empty').hidden = count !== 0;
  }
  search.addEventListener('input', filter);
  series.addEventListener('change', filter);
  buttons.forEach(button => button.addEventListener('click', () => {
    format = button.dataset.filter;
    buttons.forEach(item => item.setAttribute('aria-pressed', String(item === button)));
    filter();
  }));
})();
