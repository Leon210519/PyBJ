async function post(action) {
    try {
        const resp = await fetch('/' + action, { method: 'POST' });
        if (resp.ok) {
            return await resp.json();
        }
    } catch (err) {
        console.error(err);
    }
    return { message: 'Network error', player: { cards: [] }, dealer: { cards: [] } };
}

function render(state) {
    document.getElementById('bankroll-value').textContent = state.bankroll;
    document.getElementById('bet-value').textContent = state.bet;
    const playerCards = document.getElementById('player-cards');
    const dealerCards = document.getElementById('dealer-cards');
    playerCards.innerHTML = '';
    dealerCards.innerHTML = '';
    state.player.cards.forEach(c => {
        const img = document.createElement('img');
        img.src = c.image;
        img.alt = c.code;
        playerCards.appendChild(img);
    });
    state.dealer.cards.forEach(c => {
        const img = document.createElement('img');
        img.src = c.image;
        img.alt = c.code;
        dealerCards.appendChild(img);
    });
    document.getElementById('player-value').textContent = state.player.value || '';
    document.getElementById('dealer-value').textContent = state.dealer.value ?? '';
    document.getElementById('message').textContent = state.message || '';

    const hitBtn = document.getElementById('hit-btn');
    const standBtn = document.getElementById('stand-btn');
    const dealBtn = document.getElementById('deal-btn');
    if (state.status === 'player_turn') {
        hitBtn.disabled = false;
        standBtn.disabled = false;
        dealBtn.disabled = true;
    } else {
        hitBtn.disabled = true;
        standBtn.disabled = true;
        dealBtn.disabled = false;
    }
}

document.getElementById('deal-btn').addEventListener('click', async () => {
    const state = await post('start');
    render(state);
});

document.getElementById('hit-btn').addEventListener('click', async () => {
    const state = await post('hit');
    render(state);
});

document.getElementById('stand-btn').addEventListener('click', async () => {
    const state = await post('stand');
    render(state);
});

(async () => {
    const resp = await fetch('/state');
    if (resp.ok) {
        const state = await resp.json();
        render(state);
    }
})();
