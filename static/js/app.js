/* ========================================
   NexusShop — JavaScript Application
   ======================================== */

const API_BASE = '/api';

// ==================== STATE ====================
let state = {
    token: localStorage.getItem('token') || null,
    user: JSON.parse(localStorage.getItem('user') || 'null'),
    products: [],
    categories: [],
    cart: [],
    currentCategory: 'all',
    searchQuery: '',
};

// Category icons (emoji map)
const categoryIcons = {
    'Electronics': '&#128187;',
    'Clothing': '&#128085;',
    'Books': '&#128218;',
    'default': '&#128230;',
};

function getCategoryIcon(name) {
    return categoryIcons[name] || categoryIcons['default'];
}

// ==================== API HELPERS ====================
async function apiRequest(path, method = 'GET', body = null) {
    const headers = { 'Content-Type': 'application/json' };
    if (state.token) {
        headers['Authorization'] = 'Bearer ' + state.token;
    }
    const opts = { method, headers };
    if (body) opts.body = JSON.stringify(body);

    const res = await fetch(API_BASE + path, opts);
    const data = res.status === 204 ? null : await res.json();
    return { status: res.status, data };
}

// ==================== AUTH ====================
function fillLogin(user, pass) {
    document.getElementById('login-username').value = user;
    document.getElementById('login-password').value = pass;
}

async function handleLogin(e) {
    e.preventDefault();
    const errEl = document.getElementById('login-error');
    errEl.textContent = '';

    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;

    const { status, data } = await apiRequest('/auth/login/', 'POST', { username, password });
    if (status === 200) {
        state.token = data.access;
        state.user = data.user;
        localStorage.setItem('token', data.access);
        localStorage.setItem('user', JSON.stringify(data.user));
        hideModal('loginModal');
        updateUI();
        loadCart();
        showToast('Benvenuto, ' + state.user.username + '!', 'success');
    } else {
        errEl.textContent = 'Credenziali non valide. Riprova.';
    }
}

async function handleRegister(e) {
    e.preventDefault();
    const errEl = document.getElementById('register-error');
    errEl.textContent = '';

    const username = document.getElementById('reg-username').value;
    const email = document.getElementById('reg-email').value;
    const password = document.getElementById('reg-password').value;

    const { status, data } = await apiRequest('/auth/register/', 'POST', { username, email, password, role: 'customer' });
    if (status === 201) {
        hideModal('registerModal');
        showToast('Account creato! Effettua il login.', 'success');
        showModal('loginModal');
        document.getElementById('login-username').value = username;
    } else {
        const msg = typeof data === 'object' ? Object.values(data).flat().join(' ') : 'Errore nella registrazione.';
        errEl.textContent = msg;
    }
}

function logout() {
    state.token = null;
    state.user = null;
    state.cart = [];
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    showPage('catalog');
    updateUI();
    showToast('Logout effettuato.', 'info');
}

// ==================== UI UPDATES ====================
function updateUI() {
    const isLoggedIn = !!state.user;
    const isManager = isLoggedIn && (state.user.role === 'manager' || state.user.role === 'admin');
    const isCustomer = isLoggedIn && (state.user.role === 'customer' || state.user.role === 'admin');

    document.getElementById('btn-login').style.display = isLoggedIn ? 'none' : '';
    document.getElementById('user-menu').style.display = isLoggedIn ? 'flex' : 'none';
    document.getElementById('btn-cart').style.display = isCustomer ? '' : 'none';
    document.getElementById('nav-orders').style.display = isCustomer ? '' : 'none';
    document.getElementById('nav-manager').style.display = isManager ? '' : 'none';

    if (isLoggedIn) {
        const roleTrans = { customer: 'Cliente', manager: 'Manager', admin: 'Admin' };
        document.getElementById('user-name').textContent = state.user.username + ' (' + (roleTrans[state.user.role] || state.user.role) + ')';
    }

    updateCartBadge();
    renderProducts();
}

// ==================== MODALS ====================
function showModal(id) {
    document.getElementById(id).classList.add('show');
}
function hideModal(id) {
    document.getElementById(id).classList.remove('show');
}

// ==================== TOAST ====================
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = 'toast ' + type;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(10px)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ==================== PAGES ====================
function showPage(page) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));

    const target = document.getElementById('page-' + page);
    if (target) target.classList.add('active');

    const link = document.querySelector('.nav-link[data-page="' + page + '"]');
    if (link) link.classList.add('active');

    if (page === 'orders') loadOrders();
    if (page === 'manager') loadManagerData();
}

// ==================== PRODUCTS ====================
async function loadProducts() {
    const { status, data } = await apiRequest('/products/');
    if (status === 200) {
        state.products = data;
        renderProducts();
    }
}

async function loadCategories() {
    const { status, data } = await apiRequest('/categories/');
    if (status === 200) {
        state.categories = data;
        renderCategoryFilters();
    }
}

function renderCategoryFilters() {
    const container = document.getElementById('category-filters');
    let html = '<button class="filter-btn active" data-category="all" onclick="filterByCategory(\'all\', this)">Tutti</button>';
    state.categories.forEach(c => {
        html += '<button class="filter-btn" data-category="' + c.id + '" onclick="filterByCategory(' + c.id + ', this)">' + c.name + '</button>';
    });
    container.innerHTML = html;
}

function filterByCategory(catId, btn) {
    state.currentCategory = catId;
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    if (btn) btn.classList.add('active');
    renderProducts();
}

function filterProducts() {
    state.searchQuery = document.getElementById('search-input').value.toLowerCase();
    renderProducts();
}

function renderProducts() {
    const grid = document.getElementById('products-grid');
    let filtered = state.products;

    if (state.currentCategory !== 'all') {
        filtered = filtered.filter(p => p.category === state.currentCategory);
    }
    if (state.searchQuery) {
        filtered = filtered.filter(p =>
            p.name.toLowerCase().includes(state.searchQuery) ||
            (p.description && p.description.toLowerCase().includes(state.searchQuery))
        );
    }

    if (filtered.length === 0) {
        grid.innerHTML = '<div class="orders-empty"><p>Nessun prodotto trovato</p></div>';
        return;
    }

    const isCustomer = state.user && (state.user.role === 'customer' || state.user.role === 'admin');

    grid.innerHTML = filtered.map(p => {
        const icon = getCategoryIcon(p.category_name);
        const available = p.stock > 0 && p.is_active;
        const stockText = available ? p.stock + ' disponibili' : 'Esaurito';
        const stockClass = available ? '' : 'out-of-stock';

        let addBtn = '';
        if (isCustomer) {
            addBtn = '<button class="product-add-btn" onclick="addToCart(' + p.id + ')" ' + (!available ? 'disabled' : '') + '>' +
                (available ? 'Aggiungi al Carrello' : 'Non Disponibile') + '</button>';
        } else if (!state.user) {
            addBtn = '<button class="product-add-btn" onclick="showModal(\'loginModal\')" ' + (!available ? 'disabled' : '') + '>' +
                'Accedi per acquistare</button>';
        }

        return '<div class="product-card">' +
            '<div class="product-image">' +
                '<span class="product-category-tag">' + (p.category_name || '') + '</span>' +
                icon +
            '</div>' +
            '<div class="product-body">' +
                '<div class="product-name">' + p.name + '</div>' +
                '<div class="product-desc">' + (p.description || '') + '</div>' +
                '<div class="product-footer">' +
                    '<div class="product-price"><span class="currency">EUR </span>' + parseFloat(p.price).toFixed(2) + '</div>' +
                    '<div class="product-stock ' + stockClass + '">' + stockText + '</div>' +
                '</div>' +
                addBtn +
            '</div>' +
        '</div>';
    }).join('');
}

// ==================== CART ====================
async function loadCart() {
    if (!state.user) return;
    const { status, data } = await apiRequest('/cart/');
    if (status === 200) {
        state.cart = data;
        updateCartBadge();
        renderCart();
    }
}

function updateCartBadge() {
    const badge = document.getElementById('cart-badge');
    const total = state.cart.reduce((sum, item) => sum + item.quantity, 0);
    badge.textContent = total;
    badge.style.display = total > 0 ? 'flex' : 'none';
}

function toggleCart() {
    document.getElementById('cartSidebar').classList.toggle('open');
    document.getElementById('cartOverlay').classList.toggle('show');
    renderCart();
}

function renderCart() {
    const itemsContainer = document.getElementById('cart-items');
    const emptyEl = document.getElementById('cart-empty');
    const footerEl = document.getElementById('cart-footer');

    if (state.cart.length === 0) {
        itemsContainer.innerHTML = '<div class="cart-empty"><span class="empty-icon">&#128722;</span><p>Il carrello e\' vuoto</p></div>';
        footerEl.style.display = 'none';
        return;
    }

    footerEl.style.display = '';
    let total = 0;

    itemsContainer.innerHTML = state.cart.map(item => {
        const prod = item.product_detail || {};
        const itemTotal = parseFloat(item.total_price || 0);
        total += itemTotal;

        return '<div class="cart-item">' +
            '<div class="cart-item-info">' +
                '<div class="cart-item-name">' + (prod.name || 'Prodotto #' + item.product) + '</div>' +
                '<div class="cart-item-price">EUR ' + itemTotal.toFixed(2) + '</div>' +
            '</div>' +
            '<div class="cart-item-qty">' +
                '<button class="qty-btn" onclick="updateCartQty(' + item.id + ', ' + (item.quantity - 1) + ')">-</button>' +
                '<span class="qty-value">' + item.quantity + '</span>' +
                '<button class="qty-btn" onclick="updateCartQty(' + item.id + ', ' + (item.quantity + 1) + ')">+</button>' +
            '</div>' +
            '<button class="cart-item-remove" onclick="removeCartItem(' + item.id + ')">&times;</button>' +
        '</div>';
    }).join('');

    document.getElementById('cart-total-price').textContent = 'EUR ' + total.toFixed(2);
}

async function addToCart(productId) {
    if (!state.user) {
        showModal('loginModal');
        return;
    }
    const { status, data } = await apiRequest('/cart/', 'POST', { product: productId, quantity: 1 });
    if (status === 201) {
        showToast('Prodotto aggiunto al carrello!', 'success');
        loadCart();
    } else {
        const msg = typeof data === 'object' ? Object.values(data).flat().join(' ') : 'Errore';
        showToast(msg, 'error');
    }
}

async function updateCartQty(itemId, newQty) {
    if (newQty < 1) {
        removeCartItem(itemId);
        return;
    }
    const { status, data } = await apiRequest('/cart/' + itemId + '/', 'PATCH', { quantity: newQty });
    if (status === 200) {
        loadCart();
    } else {
        const msg = typeof data === 'object' ? Object.values(data).flat().join(' ') : 'Errore nella modifica';
        showToast(msg, 'error');
    }
}

async function removeCartItem(itemId) {
    const { status } = await apiRequest('/cart/' + itemId + '/', 'DELETE');
    if (status === 204) {
        showToast('Prodotto rimosso dal carrello.', 'info');
        loadCart();
    }
}

async function checkout() {
    if (state.cart.length === 0) {
        showToast('Il carrello e\' vuoto!', 'error');
        return;
    }
    const { status, data } = await apiRequest('/orders/', 'POST', {});
    if (status === 201) {
        showToast('Ordine #' + data.id + ' creato con successo!', 'success');
        state.cart = [];
        updateCartBadge();
        renderCart();
        toggleCart();
        loadProducts(); // Refresh stock
    } else {
        const msg = typeof data === 'string' ? data : (Array.isArray(data) ? data.join(' ') : JSON.stringify(data));
        showToast('Errore: ' + msg, 'error');
    }
}

// ==================== ORDERS ====================
async function loadOrders() {
    const container = document.getElementById('orders-list');
    container.innerHTML = '<div class="orders-empty"><p>Caricamento...</p></div>';

    const { status, data } = await apiRequest('/orders/');
    if (status !== 200) {
        container.innerHTML = '<div class="orders-empty"><p>Errore nel caricamento degli ordini.</p></div>';
        return;
    }

    if (data.length === 0) {
        container.innerHTML = '<div class="orders-empty"><p>Non hai ancora effettuato ordini.</p></div>';
        return;
    }

    container.innerHTML = data.map(order => {
        const statusClass = 'status-' + order.status;
        const statusText = { pending: 'In Attesa', shipped: 'Spedito', delivered: 'Consegnato', canceled: 'Annullato' };
        const date = new Date(order.created_at).toLocaleDateString('it-IT', { day: '2-digit', month: 'long', year: 'numeric' });

        const itemsHtml = (order.items || []).map(item =>
            '<div class="order-item-row">' +
                '<span class="order-item-name">' + (item.product_name || 'Prodotto') + ' x' + item.quantity + '</span>' +
                '<span>EUR ' + parseFloat(item.price_at_order).toFixed(2) + '</span>' +
            '</div>'
        ).join('');

        return '<div class="order-card">' +
            '<div class="order-header">' +
                '<span class="order-id">Ordine #' + order.id + '</span>' +
                '<span class="status-badge ' + statusClass + '">' + (statusText[order.status] || order.status) + '</span>' +
            '</div>' +
            '<div class="order-items">' + itemsHtml + '</div>' +
            '<div class="order-footer">' +
                '<span class="order-date">' + date + '</span>' +
                '<span class="order-total">EUR ' + parseFloat(order.total_price).toFixed(2) + '</span>' +
            '</div>' +
        '</div>';
    }).join('');
}

// ==================== MANAGER ====================
function showManagerTab(tab, btn) {
    document.querySelectorAll('.manager-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.getElementById('tab-' + tab).classList.add('active');
    if (btn) btn.classList.add('active');
}

async function loadManagerData() {
    await Promise.all([loadManagerProducts(), loadManagerCategories(), loadManagerOrders()]);
}

async function loadManagerProducts() {
    const { status, data } = await apiRequest('/products/');
    if (status === 200) {
        const tbody = document.getElementById('manager-products-body');
        tbody.innerHTML = data.map(p =>
            '<tr>' +
                '<td>' + p.id + '</td>' +
                '<td style="color:var(--text-primary);font-weight:600;">' + p.name + '</td>' +
                '<td>' + (p.category_name || p.category) + '</td>' +
                '<td>EUR ' + parseFloat(p.price).toFixed(2) + '</td>' +
                '<td>' + p.stock + '</td>' +
                '<td>' + (p.is_active ? '<span style="color:var(--success);">Si</span>' : '<span style="color:var(--danger);">No</span>') + '</td>' +
                '<td><button class="btn-danger" onclick="deleteProduct(' + p.id + ')">Elimina</button></td>' +
            '</tr>'
        ).join('');
    }
}

async function loadManagerCategories() {
    const { status, data } = await apiRequest('/categories/');
    if (status === 200) {
        state.categories = data;
        const tbody = document.getElementById('manager-categories-body');
        tbody.innerHTML = data.map(c =>
            '<tr>' +
                '<td>' + c.id + '</td>' +
                '<td style="color:var(--text-primary);font-weight:600;">' + c.name + '</td>' +
                '<td>' + c.slug + '</td>' +
                '<td>' + (c.description || '-') + '</td>' +
                '<td><button class="btn-danger" onclick="deleteCategory(' + c.id + ')">Elimina</button></td>' +
            '</tr>'
        ).join('');

        // Update product form dropdown
        const select = document.getElementById('prod-category');
        select.innerHTML = data.map(c => '<option value="' + c.id + '">' + c.name + '</option>').join('');
    }
}

async function loadManagerOrders() {
    const { status, data } = await apiRequest('/orders/');
    if (status === 200) {
        const tbody = document.getElementById('manager-orders-body');
        const statusOptions = ['pending', 'shipped', 'delivered', 'canceled'];
        const statusText = { pending: 'In Attesa', shipped: 'Spedito', delivered: 'Consegnato', canceled: 'Annullato' };

        tbody.innerHTML = data.map(order => {
            const date = new Date(order.created_at).toLocaleDateString('it-IT');
            const selectHtml = '<select onchange="updateOrderStatus(' + order.id + ', this.value)">' +
                statusOptions.map(s =>
                    '<option value="' + s + '" ' + (s === order.status ? 'selected' : '') + '>' + statusText[s] + '</option>'
                ).join('') +
            '</select>';

            return '<tr>' +
                '<td>#' + order.id + '</td>' +
                '<td style="color:var(--text-primary);">' + (order.user_username || 'Utente #' + order.user) + '</td>' +
                '<td>' + selectHtml + '</td>' +
                '<td>EUR ' + parseFloat(order.total_price).toFixed(2) + '</td>' +
                '<td>' + date + '</td>' +
                '<td><span class="status-badge status-' + order.status + '">' + statusText[order.status] + '</span></td>' +
            '</tr>';
        }).join('');
    }
}

async function updateOrderStatus(orderId, newStatus) {
    const { status, data } = await apiRequest('/orders/' + orderId + '/', 'PATCH', { status: newStatus });
    if (status === 200) {
        showToast('Stato ordine #' + orderId + ' aggiornato a: ' + newStatus, 'success');
        loadManagerOrders();
        loadProducts(); // Stock may have changed
    } else {
        const msg = typeof data === 'object' ? (data.detail || JSON.stringify(data)) : data;
        showToast('Errore: ' + msg, 'error');
        loadManagerOrders();
    }
}

// Manager forms
function showAddProductForm() {
    document.getElementById('add-product-form').style.display = '';
}
function hideAddProductForm() {
    document.getElementById('add-product-form').style.display = 'none';
}
function showAddCategoryForm() {
    document.getElementById('add-category-form').style.display = '';
}
function hideAddCategoryForm() {
    document.getElementById('add-category-form').style.display = 'none';
}

async function handleAddProduct(e) {
    e.preventDefault();
    const payload = {
        name: document.getElementById('prod-name').value,
        category: parseInt(document.getElementById('prod-category').value),
        price: document.getElementById('prod-price').value,
        stock: parseInt(document.getElementById('prod-stock').value),
        description: document.getElementById('prod-desc').value,
    };
    const { status, data } = await apiRequest('/products/', 'POST', payload);
    if (status === 201) {
        showToast('Prodotto creato: ' + data.name, 'success');
        hideAddProductForm();
        e.target.reset();
        loadManagerProducts();
        loadProducts();
    } else {
        const msg = typeof data === 'object' ? Object.values(data).flat().join(' ') : 'Errore';
        showToast(msg, 'error');
    }
}

async function handleAddCategory(e) {
    e.preventDefault();
    const payload = {
        name: document.getElementById('cat-name').value,
        description: document.getElementById('cat-desc').value,
    };
    const { status, data } = await apiRequest('/categories/', 'POST', payload);
    if (status === 201) {
        showToast('Categoria creata: ' + data.name, 'success');
        hideAddCategoryForm();
        e.target.reset();
        loadManagerCategories();
        loadCategories();
    } else {
        const msg = typeof data === 'object' ? Object.values(data).flat().join(' ') : 'Errore';
        showToast(msg, 'error');
    }
}

async function deleteProduct(id) {
    if (!confirm('Sei sicuro di voler eliminare questo prodotto?')) return;
    const { status } = await apiRequest('/products/' + id + '/', 'DELETE');
    if (status === 204) {
        showToast('Prodotto eliminato.', 'info');
        loadManagerProducts();
        loadProducts();
    } else {
        showToast('Errore nell\'eliminazione.', 'error');
    }
}

async function deleteCategory(id) {
    if (!confirm('Sei sicuro di voler eliminare questa categoria? I prodotti associati verranno eliminati.')) return;
    const { status } = await apiRequest('/categories/' + id + '/', 'DELETE');
    if (status === 204) {
        showToast('Categoria eliminata.', 'info');
        loadManagerCategories();
        loadCategories();
        loadProducts();
    } else {
        showToast('Errore nell\'eliminazione.', 'error');
    }
}

// ==================== INITIALIZATION ====================
document.addEventListener('DOMContentLoaded', async () => {
    await Promise.all([loadProducts(), loadCategories()]);
    if (state.user) {
        loadCart();
    }
    updateUI();
});
