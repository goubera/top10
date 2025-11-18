// Configuration
const API_BASE_URL = window.location.hostname === 'localhost'
    ? 'http://localhost:8000/api'
    : '/api';

// Chart instances
let volumeChart = null;
let newTokensChart = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Solana Token Tracker initialized');
    initializeCharts();
    loadAllData();
    setupEventListeners();

    // Auto-refresh every 5 minutes
    setInterval(loadAllData, 5 * 60 * 1000);
});

// Event Listeners
function setupEventListeners() {
    document.getElementById('refreshBtn').addEventListener('click', () => {
        loadAllData();
        showToast('Data refreshed', 'success');
    });

    document.getElementById('collectBtn').addEventListener('click', async () => {
        if (confirm('Trigger token collection now? This may take a minute.')) {
            await triggerCollection();
        }
    });

    document.getElementById('exportBtn').addEventListener('click', () => {
        exportCSV();
    });
}

// API Calls
async function fetchAPI(endpoint) {
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error(`API Error (${endpoint}):`, error);
        showToast(`Error loading data: ${error.message}`, 'error');
        return null;
    }
}

// Load all dashboard data
async function loadAllData() {
    showLoading(true);

    try {
        const [stats, topGainers, newTokens, trends] = await Promise.all([
            fetchAPI('/stats'),
            fetchAPI('/tokens/top-gainers'),
            fetchAPI('/tokens/new'),
            fetchAPI('/trends?days=7')
        ]);

        if (stats) updateStats(stats);
        if (topGainers) updateTopGainersTable(topGainers.top_gainers);
        if (newTokens) updateNewTokensTable(newTokens.new_tokens);
        if (trends) updateTrendingTable(trends.trending_tokens);
        if (stats) updateCharts(stats);

        updateLastUpdate();
    } finally {
        showLoading(false);
    }
}

// Update stats cards
function updateStats(data) {
    const today = data.today_stats;

    document.getElementById('tokensTracked').textContent = today.tokens_tracked || 0;
    document.getElementById('totalVolume').textContent = formatCurrency(today.total_volume || 0);
    document.getElementById('newTokens').textContent = today.new_tokens || 0;

    const avgChange = today.avg_price_change || 0;
    const changeEl = document.getElementById('avgChange');
    changeEl.textContent = formatPercent(avgChange);
    changeEl.className = 'stat-value ' + (avgChange >= 0 ? 'positive' : 'negative');
}

// Update Top Gainers Table
function updateTopGainersTable(tokens) {
    const tbody = document.querySelector('#topGainersTable tbody');

    if (!tokens || tokens.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="loading">No data available</td></tr>';
        return;
    }

    tbody.innerHTML = tokens.map((token, index) => `
        <tr>
            <td>${index + 1}</td>
            <td class="token-symbol">${escapeHtml(token.token_symbol)}</td>
            <td>${escapeHtml(token.token_name)}</td>
            <td>${formatPrice(token.price_usd)}</td>
            <td>${formatCurrency(token.volume_24h)}</td>
            <td class="${token.price_change_24h >= 0 ? 'positive' : 'negative'}">
                ${formatPercent(token.price_change_24h)}
            </td>
            <td>${formatCurrency(token.liquidity_usd)}</td>
            <td>${token.market_cap ? formatCurrency(token.market_cap) : '-'}</td>
        </tr>
    `).join('');
}

// Update New Tokens Table
function updateNewTokensTable(tokens) {
    const tbody = document.querySelector('#newTokensTable tbody');

    if (!tokens || tokens.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="loading">No new tokens today</td></tr>';
        return;
    }

    tbody.innerHTML = tokens.map((token, index) => `
        <tr>
            <td>${index + 1}</td>
            <td class="token-symbol">${escapeHtml(token.token_symbol)}</td>
            <td>${escapeHtml(token.token_name)}</td>
            <td>${formatPrice(token.price_usd)}</td>
            <td>${formatCurrency(token.volume_24h)}</td>
            <td class="${token.price_change_24h >= 0 ? 'positive' : 'negative'}">
                ${formatPercent(token.price_change_24h)}
            </td>
            <td>${formatCurrency(token.liquidity_usd)}</td>
            <td>${formatAge(token.created_at)}</td>
        </tr>
    `).join('');
}

// Update Trending Table
function updateTrendingTable(tokens) {
    const tbody = document.querySelector('#trendingTable tbody');

    if (!tokens || tokens.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="loading">No trending data available</td></tr>';
        return;
    }

    tbody.innerHTML = tokens.map((token, index) => `
        <tr>
            <td>${index + 1}</td>
            <td class="token-symbol">${escapeHtml(token.token_symbol)}</td>
            <td class="token-address">${truncateAddress(token.token_address)}</td>
            <td>${token.days_in_top} days</td>
            <td>${formatCurrency(token.avg_volume_24h)}</td>
            <td class="${token.avg_price_change >= 0 ? 'positive' : 'negative'}">
                ${formatPercent(token.avg_price_change)}
            </td>
        </tr>
    `).join('');
}

// Initialize Charts
function initializeCharts() {
    const chartOptions = {
        responsive: true,
        maintainAspectRatio: true,
        aspectRatio: 2,
        plugins: {
            legend: {
                labels: { color: '#e4e4e7' }
            }
        },
        scales: {
            y: {
                ticks: { color: '#a1a1aa' },
                grid: { color: '#3f3f46' }
            },
            x: {
                ticks: { color: '#a1a1aa' },
                grid: { color: '#3f3f46' }
            }
        }
    };

    const ctxVolume = document.getElementById('volumeChart').getContext('2d');
    volumeChart = new Chart(ctxVolume, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Total Volume (USD)',
                data: [],
                borderColor: '#9945FF',
                backgroundColor: 'rgba(153, 69, 255, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: chartOptions
    });

    const ctxNew = document.getElementById('newTokensChart').getContext('2d');
    newTokensChart = new Chart(ctxNew, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [{
                label: 'New Tokens',
                data: [],
                backgroundColor: '#14F195',
                borderRadius: 4
            }]
        },
        options: chartOptions
    });
}

// Update Charts with data
function updateCharts(stats) {
    if (!stats.recent_days || stats.recent_days.length === 0) return;

    const days = stats.recent_days.reverse(); // Oldest to newest
    const labels = days.map(d => d.date);
    const volumes = days.map(d => d.volume);
    const newTokens = days.map(d => d.new_tokens);

    volumeChart.data.labels = labels;
    volumeChart.data.datasets[0].data = volumes;
    volumeChart.update();

    newTokensChart.data.labels = labels;
    newTokensChart.data.datasets[0].data = newTokens;
    newTokensChart.update();
}

// Trigger collection
async function triggerCollection() {
    showLoading(true);
    try {
        const response = await fetch(`${API_BASE_URL}/collect`, { method: 'POST' });
        const result = await response.json();

        if (result.success) {
            showToast('Collection completed successfully!', 'success');
            setTimeout(loadAllData, 2000); // Reload after 2s
        } else {
            showToast('Collection failed', 'error');
        }
    } catch (error) {
        showToast(`Error: ${error.message}`, 'error');
    } finally {
        showLoading(false);
    }
}

// Export CSV
function exportCSV() {
    const today = new Date().toISOString().split('T')[0];
    window.open(`${API_BASE_URL}/export/csv?date=${today}`, '_blank');
    showToast('Downloading CSV...', 'success');
}

// Utility Functions
function formatCurrency(value) {
    if (!value) return '$0';
    if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
    if (value >= 1e6) return `$${(value / 1e6).toFixed(2)}M`;
    if (value >= 1e3) return `$${(value / 1e3).toFixed(2)}K`;
    return `$${value.toFixed(2)}`;
}

function formatPrice(value) {
    if (!value) return '$0';
    if (value < 0.000001) return `$${value.toExponential(2)}`;
    if (value < 0.01) return `$${value.toFixed(6)}`;
    return `$${value.toFixed(4)}`;
}

function formatPercent(value) {
    if (!value) return '0%';
    const sign = value >= 0 ? '+' : '';
    return `${sign}${value.toFixed(2)}%`;
}

function formatAge(timestamp) {
    if (!timestamp) return 'Unknown';
    const now = Date.now();
    const created = timestamp;
    const hours = Math.floor((now - created) / (1000 * 60 * 60));

    if (hours < 1) return '< 1h';
    if (hours < 24) return `${hours}h`;
    const days = Math.floor(hours / 24);
    return `${days}d`;
}

function truncateAddress(address) {
    if (!address) return '';
    return `${address.slice(0, 6)}...${address.slice(-4)}`;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function updateLastUpdate() {
    const now = new Date().toLocaleString();
    document.getElementById('lastUpdate').textContent = now;
}

function showLoading(show) {
    const overlay = document.getElementById('loadingOverlay');
    overlay.classList.toggle('hidden', !show);
}

function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type}`;

    setTimeout(() => {
        toast.classList.add('hidden');
    }, 3000);
}
