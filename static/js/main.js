/* ==========================================================================
   Quantum Catalyst Design System - Main JavaScript Logic
   Custom REST API client & Chart.js rendering
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
    
    // State variables
    let catalysts = [];
    let currentMaterial = 'Pt';
    let comparisonChart = null;

    // DOM Elements
    const materialSelect = document.getElementById('material-select');
    const infoMaterialName = document.getElementById('info-material-name');
    const infoCategory = document.getElementById('info-category');
    const infoSiteName = document.getElementById('info-site-name');
    
    const sliderDistance = document.getElementById('slider-distance');
    const sliderAccessibility = document.getElementById('slider-accessibility');
    const sliderCharge = document.getElementById('slider-charge');
    
    const valDistance = document.getElementById('val-distance');
    const valAccessibility = document.getElementById('val-accessibility');
    const valCharge = document.getElementById('val-charge');
    
    const btnRun = document.getElementById('btn-run');
    const staleWarning = document.getElementById('stale-warning');

    const dynamicSiteControls = document.getElementById('dynamic-site-controls');
    const mos2Controls = document.getElementById('mos2-controls');
    const nimoControls = document.getElementById('nimo-controls');

    // Initialize App
    init();

    async function init() {
        setupTabs();
        setupSliders();
        await fetchCatalysts();
        setupEventListeners();
        await runAnalysis();
    }

    // 1. Tab Navigation Setup
    function setupTabs() {
        const navBtns = document.querySelectorAll('.nav-btn');
        const tabContents = document.querySelectorAll('.tab-content');

        navBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const tabId = btn.getAttribute('data-tab');
                
                navBtns.forEach(b => b.classList.remove('active'));
                tabContents.forEach(c => c.classList.remove('active'));

                btn.classList.add('active');
                document.getElementById(tabId).classList.add('active');

                if (tabId === 'compare-tab') {
                    loadComparisonData();
                }
            });
        });
    }

    // 2. Sliders Setup
    function setupSliders() {
        sliderDistance.addEventListener('input', (e) => {
            valDistance.textContent = `${parseFloat(e.target.value).toFixed(2)} Å`;
            showStaleWarning();
        });

        sliderAccessibility.addEventListener('input', (e) => {
            valAccessibility.textContent = parseFloat(e.target.value).toFixed(2);
            showStaleWarning();
        });

        sliderCharge.addEventListener('input', (e) => {
            valCharge.textContent = parseFloat(e.target.value).toFixed(2);
            showStaleWarning();
        });
    }

    function showStaleWarning() {
        staleWarning.classList.remove('hidden');
    }

    function hideStaleWarning() {
        staleWarning.classList.add('hidden');
    }

    // 3. Fetch Catalysts List
    async function fetchCatalysts() {
        try {
            const res = await fetch('/api/catalysts');
            catalysts = await res.json();
            
            materialSelect.innerHTML = catalysts.map(c => 
                `<option value="${c.id}">${c.name} | ${c.formula}</option>`
            ).join('');

            updateMaterialInfo(catalysts[0]);
        } catch (err) {
            console.error('Failed to fetch catalysts:', err);
        }
    }

    function updateMaterialInfo(cat) {
        currentMaterial = cat.id;
        infoMaterialName.textContent = cat.name;
        infoCategory.textContent = cat.category;
        
        if (cat.id === 'MoS2') {
            infoSiteName.textContent = 'MoS₂ edge-site surrogate';
            showDynamicControls('MoS2');
        } else if (cat.id === 'WS2') {
            infoSiteName.textContent = 'WS₂ edge-site surrogate';
            showDynamicControls('MoS2'); // Shares edge controls
        } else if (cat.id === 'NiMo') {
            infoSiteName.textContent = 'NiₓMoᵧ interface surrogate';
            showDynamicControls('NiMo');
        } else {
            infoSiteName.textContent = `${cat.id} active-site surrogate (under-coordinated site)`;
            hideDynamicControls();
        }
    }

    function showDynamicControls(type) {
        dynamicSiteControls.classList.remove('hidden');
        if (type === 'MoS2') {
            mos2Controls.classList.remove('hidden');
            nimoControls.classList.add('hidden');
        } else if (type === 'NiMo') {
            nimoControls.classList.remove('hidden');
            mos2Controls.classList.add('hidden');
        }
    }

    function hideDynamicControls() {
        dynamicSiteControls.classList.add('hidden');
        mos2Controls.classList.add('hidden');
        nimoControls.classList.add('hidden');
    }

    // 4. Event Listeners
    function setupEventListeners() {
        materialSelect.addEventListener('change', (e) => {
            const cat = catalysts.find(c => c.id === e.target.value);
            if (cat) {
                updateMaterialInfo(cat);
                runAnalysis();
            }
        });

        btnRun.addEventListener('click', () => {
            runAnalysis();
        });

        document.querySelectorAll('.site-param').forEach(elem => {
            elem.addEventListener('change', () => {
                showStaleWarning();
            });
        });
    }

    // 5. Run Analysis API Call
    async function runAnalysis() {
        hideStaleWarning();
        const cid = materialSelect.value;
        
        const payload = {
            catalyst_id: cid,
            adsorption_distance: parseFloat(sliderDistance.value),
            site_factor: parseFloat(sliderAccessibility.value),
            local_charge: parseFloat(sliderCharge.value)
        };

        if (cid === 'MoS2' || cid === 'WS2') {
            payload.phase = document.getElementById('mos2-phase').value;
            payload.edge = document.getElementById('mos2-edge').value;
            payload.geometry = document.getElementById('mos2-geometry').value;
        } else if (cid === 'NiMo') {
            payload.ni_fraction = parseFloat(document.getElementById('nimo-fraction').value);
            payload.geometry = document.getElementById('nimo-geometry').value;
            payload.adsorption_site = document.getElementById('nimo-site').value;
        }

        try {
            const res = await fetch('/api/calculate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await res.json();
            renderResults(data);
        } catch (err) {
            console.error('Calculation error:', err);
        }
    }

    // 6. Render Results UI
    function renderResults(data) {
        document.getElementById('res-material-title').textContent = `${data.name} | ${data.formula}`;
        document.getElementById('res-subtitle').textContent = `${data.structure} • ${data.active_site}`;

        const badge = document.getElementById('decision-badge');
        badge.className = 'badge-decision';

        if (data.decision === 'SHORTLIST') {
            badge.classList.add('shortlist');
            badge.textContent = 'SHORTLIST';
        } else if (data.decision.includes('BORDERLINE')) {
            badge.classList.add('borderline');
            badge.textContent = 'BORDERLINE';
        } else if (data.decision === 'NOT SHORTLISTED') {
            badge.classList.add('not-shortlisted');
            badge.textContent = 'NOT SHORTLISTED';
        } else {
            badge.classList.add('incomplete');
            badge.textContent = 'MODEL INCOMPLETE';
        }

        // Evidence Cards
        if (data.status === 'calculated') {
            document.getElementById('card-val-model').textContent = 'DEFINED';
            document.getElementById('card-sub-model').textContent = data.model_type;

            document.getElementById('card-val-quantum').textContent = '✓ Validated';
            document.getElementById('card-val-quantum').className = 'card-value status-pass';
            document.getElementById('card-sub-quantum').textContent = `Error: ${data.max_vqe_error_ev.toExponential(2)} eV`;

            document.getElementById('card-val-interaction').textContent = `${data.interaction_energy_ev > 0 ? '+' : ''}${data.interaction_energy_ev.toFixed(4)} eV`;
            document.getElementById('card-val-proxy').textContent = `${data.her_screening_proxy_ev > 0 ? '+' : ''}${data.her_screening_proxy_ev.toFixed(4)} eV`;
        } else if (data.status === 'model_incomplete') {
            document.getElementById('card-val-model').textContent = 'INCOMPLETE';
            document.getElementById('card-sub-model').textContent = `Missing: ${data.missing_fields.join(', ')}`;

            document.getElementById('card-val-quantum').textContent = 'N/A';
            document.getElementById('card-val-quantum').className = 'card-value';
            document.getElementById('card-sub-quantum').textContent = 'No calculation available';

            document.getElementById('card-val-interaction').textContent = 'N/A';
            document.getElementById('card-val-proxy').textContent = 'N/A';
        }

        document.getElementById('decision-reason-text').textContent = data.decision_reason || data.reason;
        document.getElementById('next-action-text').textContent = data.next_action;
    }

    // 7. Load Comparison Data & Chart.js Rendering
    async function loadComparisonData() {
        try {
            const res = await fetch('/api/compare');
            const data = await res.json();
            
            renderComparisonTable(data);
            renderComparisonChart(data);
        } catch (err) {
            console.error('Failed to load comparison data:', err);
        }
    }

    function renderComparisonTable(data) {
        const tbody = document.getElementById('comparison-tbody');
        tbody.innerHTML = data.map(item => `
            <tr>
                <td><strong>${item.name}</strong> (${item.formula})</td>
                <td>${item.category}</td>
                <td>${item.clean_vqe !== 'N/A' ? item.clean_vqe : 'N/A'}</td>
                <td>${item.ads_vqe !== 'N/A' ? item.ads_vqe : 'N/A'}</td>
                <td>${item.interaction !== 'N/A' ? item.interaction : 'N/A'}</td>
                <td><strong>${item.proxy !== 'N/A' ? item.proxy : 'N/A'}</strong></td>
                <td>${item.vqe_error !== 'N/A' ? item.vqe_error : 'N/A'}</td>
                <td><span class="badge ${item.decision === 'SHORTLIST' ? 'badge-purple' : 'badge-gray'}">${item.decision}</span></td>
            </tr>
        `).join('');
    }

    function renderComparisonChart(data) {
        const ctx = document.getElementById('comparison-chart').getContext('2d');
        
        const validItems = data.filter(d => d.proxy !== 'N/A');
        const labels = validItems.map(d => `${d.name} (${d.formula})`);
        const values = validItems.map(d => parseFloat(d.proxy));
        
        const bgColors = validItems.map(d => 
            d.decision === 'SHORTLIST' ? 'rgba(37, 99, 235, 0.85)' : 'rgba(245, 158, 11, 0.85)'
        );

        if (comparisonChart) {
            comparisonChart.destroy();
        }

        comparisonChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'HER Screening Proxy ΔG_H* (eV)',
                    data: values,
                    backgroundColor: bgColors,
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { labels: { color: '#334155', font: { weight: '600' } } }
                },
                scales: {
                    x: { ticks: { color: '#64748b' }, grid: { color: '#e2e8f0' } },
                    y: { 
                        ticks: { color: '#64748b' }, 
                        grid: { color: '#e2e8f0' },
                        title: { display: true, text: 'ΔG_H* (eV)', color: '#475569', font: { weight: '600' } }
                    }
                }
            }
        });
    }

});
