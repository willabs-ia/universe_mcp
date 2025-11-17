// ===========================
// Global State
// ===========================
const state = {
    servers: [],
    clients: [],
    usecases: [],
    statistics: {},
    currentTab: 'servers',
    searchQuery: '',
    filters: {
        classification: null,
        provider: null
    },
    pagination: {
        servers: { page: 1, perPage: 24 },
        clients: { page: 1, perPage: 24 },
        usecases: { page: 1, perPage: 24 }
    }
};

// ===========================
// Data Loading
// ===========================
async function loadData() {
    try {
        showLoading();

        // Load all data in parallel
        const [serversData, clientsData, usecasesData, statsData] = await Promise.all([
            fetch('../indexes/all-servers.json').then(r => r.json()),
            fetch('../indexes/all-clients.json').then(r => r.json()),
            fetch('../indexes/all-usecases.json').then(r => r.json()),
            fetch('../indexes/statistics.json').then(r => r.json())
        ]);

        state.servers = serversData.servers || [];
        state.clients = clientsData.clients || [];
        state.usecases = usecasesData.use_cases || [];
        state.statistics = statsData;

        updateStatsBanner();
        initFilters();
        renderCurrentTab();
        renderStatistics();

        hideLoading();
    } catch (error) {
        console.error('Error loading data:', error);
        hideLoading();
        alert('Error loading data. Please check the console for details.');
    }
}

// ===========================
// Loading Overlay
// ===========================
function showLoading() {
    document.getElementById('loading-overlay').classList.remove('hidden');
}

function hideLoading() {
    document.getElementById('loading-overlay').classList.add('hidden');
}

// ===========================
// Stats Banner
// ===========================
function updateStatsBanner() {
    const stats = state.statistics;

    document.getElementById('total-servers').textContent =
        (stats.totals?.servers || 0).toLocaleString();

    document.getElementById('total-clients').textContent =
        (stats.totals?.clients || 0).toLocaleString();

    document.getElementById('official-servers').textContent =
        (stats.servers?.by_classification?.official || 0).toLocaleString();

    document.getElementById('community-servers').textContent =
        (stats.servers?.by_classification?.community || 0).toLocaleString();
}

// ===========================
// Filters
// ===========================
function initFilters() {
    const filtersContainer = document.getElementById('filters-container');

    const filtersHTML = `
        <div class="filter-group">
            <button class="filter-btn ${!state.filters.classification ? 'active' : ''}"
                    data-filter="classification" data-value="">
                All
            </button>
            <button class="filter-btn official ${state.filters.classification === 'official' ? 'active' : ''}"
                    data-filter="classification" data-value="official">
                Official
            </button>
            <button class="filter-btn community ${state.filters.classification === 'community' ? 'active' : ''}"
                    data-filter="classification" data-value="community">
                Community
            </button>
            <button class="filter-btn reference ${state.filters.classification === 'reference' ? 'active' : ''}"
                    data-filter="classification" data-value="reference">
                Reference
            </button>
        </div>
    `;

    filtersContainer.innerHTML = filtersHTML;

    // Add event listeners to filter buttons
    filtersContainer.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const filter = btn.dataset.filter;
            const value = btn.dataset.value;

            state.filters[filter] = value || null;
            state.pagination[state.currentTab].page = 1;

            // Update active states
            filtersContainer.querySelectorAll(`[data-filter="${filter}"]`).forEach(b => {
                b.classList.remove('active');
            });
            btn.classList.add('active');

            renderCurrentTab();
        });
    });
}

// ===========================
// Search
// ===========================
function setupSearch() {
    const searchInput = document.getElementById('search-input');
    const searchBtn = document.getElementById('search-btn');

    const performSearch = () => {
        state.searchQuery = searchInput.value.toLowerCase().trim();
        state.pagination[state.currentTab].page = 1;
        renderCurrentTab();
    };

    searchBtn.addEventListener('click', performSearch);
    searchInput.addEventListener('keyup', (e) => {
        if (e.key === 'Enter') {
            performSearch();
        }
    });

    // Live search (debounced)
    let searchTimeout;
    searchInput.addEventListener('input', () => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(performSearch, 300);
    });
}

// ===========================
// Tab Navigation
// ===========================
function setupTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tab = btn.dataset.tab;

            // Update active states
            tabBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            document.querySelectorAll('.tab-panel').forEach(panel => {
                panel.classList.remove('active');
            });
            document.getElementById(`${tab}-panel`).classList.add('active');

            state.currentTab = tab;
            renderCurrentTab();
        });
    });
}

// ===========================
// Rendering
// ===========================
function renderCurrentTab() {
    switch (state.currentTab) {
        case 'servers':
            renderServers();
            break;
        case 'clients':
            renderClients();
            break;
        case 'usecases':
            renderUseCases();
            break;
        case 'stats':
            renderStatistics();
            break;
    }
}

function filterData(data) {
    let filtered = [...data];

    // Apply search
    if (state.searchQuery) {
        filtered = filtered.filter(item => {
            const searchText = [
                item.name,
                item.title,
                item.provider,
                item.description
            ].filter(Boolean).join(' ').toLowerCase();

            return searchText.includes(state.searchQuery);
        });
    }

    // Apply classification filter (servers only)
    if (state.filters.classification && filtered[0]?.classification !== undefined) {
        filtered = filtered.filter(item =>
            item.classification === state.filters.classification
        );
    }

    return filtered;
}

// ===========================
// Render Servers
// ===========================
function renderServers() {
    const filtered = filterData(state.servers);
    const { page, perPage } = state.pagination.servers;
    const start = 0;
    const end = page * perPage;
    const paginatedData = filtered.slice(start, end);

    document.getElementById('servers-count').textContent =
        `${filtered.length.toLocaleString()} servers`;

    const grid = document.getElementById('servers-grid');
    grid.innerHTML = paginatedData.map(server => `
        <div class="card" onclick="window.open('${server.url}', '_blank')">
            <div class="card-header">
                <div>
                    <div class="card-title">${escapeHtml(server.name)}</div>
                    <div class="card-provider">${escapeHtml(server.provider || 'Unknown')}</div>
                </div>
                ${server.classification ? `<span class="badge ${server.classification}">${server.classification}</span>` : ''}
            </div>
            <div class="card-description">
                ${escapeHtml(server.description || 'No description available')}
            </div>
            <div class="card-footer">
                ${server.weekly_metric ? `
                    <div class="card-metric">
                        ${server.weekly_metric.type === 'downloads' ? '📥' : '👁️'}
                        <strong>${formatNumber(server.weekly_metric.value)}</strong>
                        ${server.weekly_metric.type}
                    </div>
                ` : '<div></div>'}
                ${server.release_date ? `
                    <div class="card-date">📅 ${escapeHtml(server.release_date)}</div>
                ` : ''}
            </div>
        </div>
    `).join('');

    // Show/hide load more button
    const loadMoreBtn = document.getElementById('load-more-servers');
    if (end >= filtered.length) {
        loadMoreBtn.classList.add('hidden');
    } else {
        loadMoreBtn.classList.remove('hidden');
    }
}

// ===========================
// Render Clients
// ===========================
function renderClients() {
    const filtered = filterData(state.clients);
    const { page, perPage } = state.pagination.clients;
    const start = 0;
    const end = page * perPage;
    const paginatedData = filtered.slice(start, end);

    document.getElementById('clients-count').textContent =
        `${filtered.length.toLocaleString()} clients`;

    const grid = document.getElementById('clients-grid');
    grid.innerHTML = paginatedData.map(client => `
        <div class="card" onclick="window.open('${client.url}', '_blank')">
            <div class="card-header">
                <div>
                    <div class="card-title">${escapeHtml(client.name)}</div>
                    <div class="card-provider">${escapeHtml(client.provider || 'Unknown')}</div>
                </div>
            </div>
            <div class="card-description">
                ${escapeHtml(client.description || 'No description available')}
            </div>
            ${client.platforms && client.platforms.length > 0 ? `
                <div class="card-footer">
                    <div class="card-metric">
                        🖥️ ${client.platforms.join(', ')}
                    </div>
                </div>
            ` : ''}
        </div>
    `).join('');

    // Show/hide load more button
    const loadMoreBtn = document.getElementById('load-more-clients');
    if (end >= filtered.length) {
        loadMoreBtn.classList.add('hidden');
    } else {
        loadMoreBtn.classList.remove('hidden');
    }
}

// ===========================
// Render Use Cases
// ===========================
function renderUseCases() {
    const filtered = filterData(state.usecases);

    document.getElementById('usecases-count').textContent =
        `${filtered.length} use cases`;

    const grid = document.getElementById('usecases-grid');
    grid.innerHTML = filtered.map(usecase => `
        <div class="card" onclick="window.open('${usecase.url}', '_blank')">
            <div class="card-header">
                <div>
                    <div class="card-title">${escapeHtml(usecase.title)}</div>
                </div>
            </div>
            <div class="card-description">
                ${escapeHtml(usecase.description || 'No description available')}
            </div>
            ${usecase.servers_used && usecase.servers_used.length > 0 ? `
                <div class="card-footer">
                    <div class="card-metric">
                        🔧 ${usecase.servers_used.length} servers used
                    </div>
                </div>
            ` : ''}
        </div>
    `).join('');
}

// ===========================
// Render Statistics
// ===========================
function renderStatistics() {
    const stats = state.statistics;

    // Top Providers
    if (stats.servers?.top_providers) {
        const topProviders = Object.entries(stats.servers.top_providers)
            .slice(0, 15);

        document.getElementById('top-providers').innerHTML = topProviders.map(([provider, count]) => `
            <div class="stats-item">
                <div class="stats-item-name">${escapeHtml(provider)}</div>
                <div class="stats-item-count">${count.toLocaleString()}</div>
            </div>
        `).join('');
    }

    // Classification Chart
    if (stats.servers?.by_classification) {
        const classifications = stats.servers.by_classification;
        const total = Object.values(classifications).reduce((a, b) => a + b, 0);

        document.getElementById('classification-chart').innerHTML = Object.entries(classifications)
            .filter(([key]) => key && key !== '')
            .map(([classification, count]) => {
                const percentage = (count / total * 100).toFixed(1);
                return `
                    <div class="chart-bar">
                        <div class="chart-label">${classification}</div>
                        <div class="chart-bar-container">
                            <div class="chart-bar-fill" style="width: ${percentage}%">
                                ${count.toLocaleString()} (${percentage}%)
                            </div>
                        </div>
                    </div>
                `;
            }).join('');
    }

    // Quality Metrics
    const qualityMetrics = [
        { label: 'Servers', value: stats.totals?.servers || 0 },
        { label: 'With Descriptions', value: stats.servers?.with_description || 0 },
        { label: 'With Metrics', value: stats.servers?.with_metrics || 0 },
        { label: 'Clients', value: stats.totals?.clients || 0 }
    ];

    document.getElementById('quality-metrics').innerHTML = qualityMetrics.map(metric => `
        <div class="quality-metric">
            <div class="quality-metric-value">${metric.value.toLocaleString()}</div>
            <div class="quality-metric-label">${metric.label}</div>
        </div>
    `).join('');
}

// ===========================
// Load More
// ===========================
function setupLoadMore() {
    document.getElementById('load-more-servers').addEventListener('click', () => {
        state.pagination.servers.page++;
        renderServers();
    });

    document.getElementById('load-more-clients').addEventListener('click', () => {
        state.pagination.clients.page++;
        renderClients();
    });
}

// ===========================
// Utility Functions
// ===========================
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return String(text).replace(/[&<>"']/g, m => map[m]);
}

function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    }
    if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
}

// ===========================
// Initialization
// ===========================
document.addEventListener('DOMContentLoaded', () => {
    setupTabs();
    setupSearch();
    setupLoadMore();
    loadData();
});
