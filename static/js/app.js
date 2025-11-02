/**
 * Cisco Configuration Generator - Professional Edition
 * Modern JavaScript Application with Monaco Editor
 */

// Global Variables
let monacoEditor = null;
let currentWizardStep = 1;
let wizardData = {};
let authToken = localStorage.getItem('authToken');

// CCIE-Level Templates
const ccieTemplates = {
    dataCenterCore: {
        name: "Data Center Core Switch",
        icon: "🏢",
        description: "Enterprise data center core with VSS, HSRP, OSPF",
        platform: "nxos",
        config: {
            hostname: "DC-CORE-01",
            domain_name: "datacenter.example.com",
            interfaces: [
                {name: "Ethernet1/1", description: "Uplink to Spine", ip_address: "10.1.1.1", subnet_mask: "255.255.255.252"},
                {name: "Vlan100", description: "Management VLAN", ip_address: "10.100.1.1", subnet_mask: "255.255.255.0"}
            ],
            vlans: [
                {id: 10, name: "PROD-DATA"},
                {id: 20, name: "PROD-VOICE"},
                {id: 100, name: "MGMT"}
            ],
            ospf: {
                enabled: true,
                process_id: 1,
                router_id: "10.1.1.1"
            },
            ntp_servers: ["10.0.1.10", "10.0.1.11"],
            dns_servers: ["10.0.1.53", "8.8.8.8"]
        }
    },
    branchRouter: {
        name: "Branch Office Router",
        icon: "🏪",
        description: "Branch router with EIGRP, GRE tunnel, NAT",
        platform: "ios",
        config: {
            hostname: "BRANCH-RTR-01",
            domain_name: "branch.example.com",
            interfaces: [
                {name: "GigabitEthernet0/0", description: "WAN Interface", ip_address: "192.168.1.1", subnet_mask: "255.255.255.252"},
                {name: "GigabitEthernet0/1", description: "LAN Interface", ip_address: "10.10.10.1", subnet_mask: "255.255.255.0"}
            ],
            static_routes: [
                {network: "0.0.0.0/0", next_hop: "192.168.1.2"}
            ],
            ntp_servers: ["pool.ntp.org"],
            dns_servers: ["8.8.8.8", "8.8.4.4"]
        }
    },
    campusAccess: {
        name: "Campus Access Switch",
        icon: "🎓",
        description: "Campus access with Port Security, DHCP Snooping, DAI",
        platform: "ios",
        config: {
            hostname: "CAMPUS-ACC-01",
            domain_name: "campus.example.com",
            vlans: [
                {id: 10, name: "STUDENTS"},
                {id: 20, name: "FACULTY"},
                {id: 30, name: "GUESTS"},
                {id: 99, name: "MGMT"}
            ],
            interfaces: [
                {name: "GigabitEthernet0/1", description: "Access Port - Student", vlan: 10},
                {name: "GigabitEthernet0/24", description: "Uplink to Distribution", trunk: true}
            ],
            ntp_servers: ["10.0.0.1"],
            dns_servers: ["10.0.0.53"]
        }
    },
    internetEdge: {
        name: "Internet Edge Router",
        icon: "🌐",
        description: "Internet edge with BGP, NAT, firewall",
        platform: "iosxr",
        config: {
            hostname: "EDGE-RTR-01",
            domain_name: "edge.example.com",
            interfaces: [
                {name: "GigabitEthernet0/0/0/0", description: "ISP Primary", ip_address: "203.0.113.2", subnet_mask: "255.255.255.252"},
                {name: "GigabitEthernet0/0/0/1", description: "Internal DMZ", ip_address: "10.255.0.1", subnet_mask: "255.255.255.0"}
            ],
            static_routes: [
                {network: "0.0.0.0/0", next_hop: "203.0.113.1"}
            ],
            ntp_servers: ["ntp.example.com"],
            dns_servers: ["1.1.1.1", "8.8.8.8"]
        }
    },
    dmzFirewall: {
        name: "DMZ Firewall",
        icon: "🔥",
        description: "ASA firewall with zones, ACLs, VPN",
        platform: "asa",
        config: {
            hostname: "DMZ-FW-01",
            domain_name: "dmz.example.com",
            interfaces: [
                {name: "GigabitEthernet0/0", description: "Outside", ip_address: "203.0.113.10", subnet_mask: "255.255.255.0"},
                {name: "GigabitEthernet0/1", description: "DMZ", ip_address: "10.10.10.1", subnet_mask: "255.255.255.0"},
                {name: "GigabitEthernet0/2", description: "Inside", ip_address: "172.16.0.1", subnet_mask: "255.255.255.0"}
            ],
            ntp_servers: ["time.nist.gov"],
            dns_servers: ["8.8.8.8"]
        }
    },
    mpls_pe: {
        name: "MPLS Provider Edge",
        icon: "☁️",
        description: "Service provider PE router with MPLS, BGP, QoS",
        platform: "iosxr",
        config: {
            hostname: "PE-RTR-01",
            domain_name: "sp.example.com",
            interfaces: [
                {name: "TenGigE0/0/0/0", description: "P router link", ip_address: "10.0.1.1", subnet_mask: "255.255.255.252"},
                {name: "GigabitEthernet0/0/0/1", description: "Customer A", ip_address: "192.168.100.1", subnet_mask: "255.255.255.252"}
            ],
            ospf: {
                enabled: true,
                process_id: 100,
                router_id: "1.1.1.1"
            },
            ntp_servers: ["10.0.0.1"],
            dns_servers: ["10.0.0.53"]
        }
    }
};

// Initialize Monaco Editor
function initMonacoEditor() {
    require.config({ paths: { vs: 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.44.0/min/vs' } });

    require(['vs/editor/editor.main'], function() {
        const isDarkTheme = document.documentElement.getAttribute('data-theme') === 'dark';

        monacoEditor = monaco.editor.create(document.getElementById('monaco-editor'), {
            value: '! Welcome to Cisco Configuration Generator Pro\n! Generate your configuration to see results here\n',
            language: 'plaintext',
            theme: isDarkTheme ? 'vs-dark' : 'vs',
            automaticLayout: true,
            minimap: { enabled: true },
            fontSize: 14,
            wordWrap: 'on',
            lineNumbers: 'on',
            readOnly: false,
            scrollBeyondLastLine: false,
            renderWhitespace: 'selection'
        });
    });
}

// Theme Toggle
function toggleTheme() {
    const html = document.documentElement;
    const currentTheme = html.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

    html.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);

    // Update Monaco theme
    if (monacoEditor) {
        monaco.editor.setTheme(newTheme === 'dark' ? 'vs-dark' : 'vs');
    }

    // Update theme toggle icon
    const icon = document.querySelector('.theme-toggle');
    icon.textContent = newTheme === 'dark' ? '☀️' : '🌙';
}

// Load saved theme
function loadTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    const icon = document.querySelector('.theme-toggle');
    if (icon) {
        icon.textContent = savedTheme === 'dark' ? '☀️' : '🌙';
    }
}

// Tab Navigation
function showTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.content-tab').forEach(tab => {
        tab.style.display = 'none';
    });

    // Show selected tab
    const tab = document.getElementById(tabName + 'Tab');
    if (tab) {
        tab.style.display = 'block';
    }

    // Load templates if templates tab
    if (tabName === 'templates') {
        loadTemplates();
    }

    // Initialize wizard if wizard tab
    if (tabName === 'wizard') {
        initWizard();
    }
}

// Load CCIE Templates
function loadTemplates() {
    const templatesList = document.getElementById('templatesList');
    templatesList.innerHTML = '';

    for (const [key, template] of Object.entries(ccieTemplates)) {
        const col = document.createElement('div');
        col.className = 'col-md-4 mb-3';

        col.innerHTML = `
            <div class="card template-card h-100 border-2" onclick="loadTemplate('${key}')">
                <div class="card-body">
                    <div class="text-center mb-3" style="font-size: 3rem;">${template.icon}</div>
                    <h5 class="card-title">${template.name}</h5>
                    <p class="card-text text-muted">${template.description}</p>
                    <div class="mt-3">
                        <span class="badge bg-primary">${template.platform.toUpperCase()}</span>
                    </div>
                </div>
            </div>
        `;

        templatesList.appendChild(col);
    }
}

// Load Template
function loadTemplate(templateKey) {
    const template = ccieTemplates[templateKey];
    if (!template) return;

    // Fill form with template data
    document.getElementById('platform').value = template.config.platform || 'ios';
    document.getElementById('hostname').value = template.config.hostname || '';
    document.getElementById('domain_name').value = template.config.domain_name || '';

    if (template.config.ntp_servers) {
        document.getElementById('ntpServers').value = template.config.ntp_servers.join(', ');
    }

    if (template.config.dns_servers) {
        document.getElementById('dnsServers').value = template.config.dns_servers.join(', ');
    }

    // Switch to custom tab
    showTab('custom');

    // Show notification
    showNotification(`Template "${template.name}" loaded successfully!`, 'success');

    // Generate configuration immediately
    setTimeout(() => {
        generateConfig(template.config);
    }, 500);
}

// Initialize Wizard
function initWizard() {
    currentWizardStep = 1;
    wizardData = {};
    updateWizardStep();
}

// Wizard Navigation
function nextWizardStep() {
    if (currentWizardStep < 5) {
        // Save current step data
        saveWizardStepData(currentWizardStep);

        currentWizardStep++;
        updateWizardStep();
    } else {
        // Final step - generate
        generateFromWizard();
    }
}

function prevWizardStep() {
    if (currentWizardStep > 1) {
        currentWizardStep--;
        updateWizardStep();
    }
}

function updateWizardStep() {
    // Update step indicators
    document.querySelectorAll('.step-item').forEach((item, index) => {
        item.classList.remove('active', 'completed');
        if (index + 1 < currentWizardStep) {
            item.classList.add('completed');
        } else if (index + 1 === currentWizardStep) {
            item.classList.add('active');
        }
    });

    // Update buttons
    document.getElementById('wizardPrev').disabled = currentWizardStep === 1;
    document.getElementById('wizardNext').textContent = currentWizardStep === 5 ? '🚀 Generate' : 'Next →';

    // Render step content
    renderWizardStep(currentWizardStep);
}

function renderWizardStep(step) {
    const container = document.getElementById('wizardSteps');

    switch(step) {
        case 1:
            container.innerHTML = `
                <h4>Step 1: Device Information</h4>
                <div class="mb-3">
                    <label class="form-label">Platform *</label>
                    <select class="form-select" id="wizardPlatform">
                        <option value="ios">Cisco IOS</option>
                        <option value="nxos">Cisco NX-OS</option>
                        <option value="asa">Cisco ASA</option>
                        <option value="iosxr">Cisco IOS-XR</option>
                    </select>
                </div>
                <div class="mb-3">
                    <label class="form-label">Hostname *</label>
                    <input type="text" class="form-control" id="wizardHostname" value="${wizardData.hostname || ''}" placeholder="router01">
                </div>
                <div class="mb-3">
                    <label class="form-label">Domain Name</label>
                    <input type="text" class="form-control" id="wizardDomain" value="${wizardData.domain_name || ''}" placeholder="example.com">
                </div>
            `;
            break;
        case 2:
            container.innerHTML = `
                <h4>Step 2: Network Interfaces</h4>
                <p class="text-muted">Add interfaces for your device</p>
                <div id="wizardInterfacesList"></div>
                <button type="button" class="btn btn-secondary btn-sm mt-2" onclick="addWizardInterface()">+ Add Interface</button>
            `;
            break;
        case 3:
            container.innerHTML = `
                <h4>Step 3: Routing Configuration</h4>
                <div class="form-check mb-3">
                    <input class="form-check-input" type="checkbox" id="wizardOspf">
                    <label class="form-check-label" for="wizardOspf">
                        Enable OSPF Routing
                    </label>
                </div>
                <div class="mb-3">
                    <label class="form-label">Static Default Route (Optional)</label>
                    <input type="text" class="form-control" id="wizardDefaultRoute" placeholder="192.168.1.254">
                </div>
            `;
            break;
        case 4:
            container.innerHTML = `
                <h4>Step 4: Services & Management</h4>
                <div class="mb-3">
                    <label class="form-label">NTP Servers (comma-separated)</label>
                    <input type="text" class="form-control" id="wizardNtp" value="${wizardData.ntp || ''}" placeholder="pool.ntp.org, time.google.com">
                </div>
                <div class="mb-3">
                    <label class="form-label">DNS Servers (comma-separated)</label>
                    <input type="text" class="form-control" id="wizardDns" value="${wizardData.dns || ''}" placeholder="8.8.8.8, 8.8.4.4">
                </div>
                <div class="mb-3">
                    <label class="form-label">Enable Secret (Password)</label>
                    <input type="password" class="form-control" id="wizardSecret">
                </div>
            `;
            break;
        case 5:
            container.innerHTML = `
                <h4>Step 5: Review Configuration</h4>
                <div class="alert alert-info">
                    <strong>Review your configuration:</strong>
                    <ul class="mt-2 mb-0">
                        <li>Platform: <strong>${wizardData.platform || 'Not set'}</strong></li>
                        <li>Hostname: <strong>${wizardData.hostname || 'Not set'}</strong></li>
                        <li>Domain: <strong>${wizardData.domain_name || 'Not set'}</strong></li>
                        <li>Interfaces: <strong>${(wizardData.interfaces || []).length}</strong></li>
                    </ul>
                </div>
                <p class="text-muted">Click "Generate" to create your configuration.</p>
            `;
            break;
    }
}

function saveWizardStepData(step) {
    switch(step) {
        case 1:
            wizardData.platform = document.getElementById('wizardPlatform').value;
            wizardData.hostname = document.getElementById('wizardHostname').value;
            wizardData.domain_name = document.getElementById('wizardDomain').value;
            break;
        case 4:
            wizardData.ntp = document.getElementById('wizardNtp').value;
            wizardData.dns = document.getElementById('wizardDns').value;
            wizardData.enable_secret = document.getElementById('wizardSecret').value;
            break;
    }
}

function generateFromWizard() {
    const config = {
        platform: wizardData.platform,
        hostname: wizardData.hostname,
        domain_name: wizardData.domain_name,
        enable_secret: wizardData.enable_secret,
        output_format: 'cli'
    };

    if (wizardData.ntp) {
        config.ntp_servers = wizardData.ntp.split(',').map(s => s.trim());
    }

    if (wizardData.dns) {
        config.dns_servers = wizardData.dns.split(',').map(s => s.trim());
    }

    showTab('custom');
    generateConfig(config);
}

function addWizardInterface() {
    // Add interface logic for wizard
    const list = document.getElementById('wizardInterfacesList');
    const index = list.children.length;

    const div = document.createElement('div');
    div.className = 'card mb-2 p-2';
    div.innerHTML = `
        <input type="text" class="form-control form-control-sm mb-1" placeholder="Interface name (e.g., GigabitEthernet0/0)">
        <input type="text" class="form-control form-control-sm" placeholder="IP address (e.g., 192.168.1.1)">
    `;
    list.appendChild(div);
}

// Add Interface
function addInterface() {
    const list = document.getElementById('interfacesList');
    const index = list.children.length;

    const div = document.createElement('div');
    div.className = 'card mb-2 p-3';
    div.innerHTML = `
        <div class="d-flex justify-content-between align-items-center mb-2">
            <strong>Interface ${index + 1}</strong>
            <button type="button" class="btn btn-sm btn-danger" onclick="this.parentElement.parentElement.remove()">×</button>
        </div>
        <div class="mb-2">
            <input type="text" class="form-control form-control-sm" placeholder="Name (e.g., GigabitEthernet0/0)" name="int_name_${index}">
        </div>
        <div class="mb-2">
            <input type="text" class="form-control form-control-sm" placeholder="Description" name="int_desc_${index}">
        </div>
        <div class="row">
            <div class="col-6">
                <input type="text" class="form-control form-control-sm" placeholder="IP Address" name="int_ip_${index}">
            </div>
            <div class="col-6">
                <input type="text" class="form-control form-control-sm" placeholder="Subnet Mask" name="int_mask_${index}">
            </div>
        </div>
    `;

    list.appendChild(div);
}

// Parse Configuration (Import)
function parseConfig() {
    const configText = document.getElementById('importConfigText').value;

    if (!configText.trim()) {
        showNotification('Please paste a configuration first', 'danger');
        return;
    }

    // Simple parser
    const lines = configText.split('\n');
    const parsed = {
        hostname: '',
        domain_name: '',
        interfaces: [],
        platform: 'ios'
    };

    let currentInterface = null;

    lines.forEach(line => {
        line = line.trim();

        if (line.startsWith('hostname ')) {
            parsed.hostname = line.replace('hostname ', '');
        } else if (line.includes('domain-name') || line.includes('domain name')) {
            parsed.domain_name = line.split(' ').pop();
        } else if (line.startsWith('interface ')) {
            currentInterface = {
                name: line.replace('interface ', ''),
                description: '',
                ip_address: '',
                subnet_mask: ''
            };
            parsed.interfaces.push(currentInterface);
        } else if (currentInterface && line.startsWith('description ')) {
            currentInterface.description = line.replace('description ', '');
        } else if (currentInterface && line.includes('ip address ')) {
            const parts = line.split(' ');
            currentInterface.ip_address = parts[2];
            currentInterface.subnet_mask = parts[3];
        }
    });

    // Load into form
    document.getElementById('platform').value = parsed.platform;
    document.getElementById('hostname').value = parsed.hostname;
    document.getElementById('domain_name').value = parsed.domain_name;

    showTab('custom');
    showNotification(`Configuration parsed! Found ${parsed.interfaces.length} interfaces`, 'success');

    // Generate
    generateConfig(parsed);
}

// Generate Configuration
function generateConfig(configData = null) {
    const data = configData || collectFormData();

    document.getElementById('loadingSpinner').style.display = 'block';
    document.getElementById('errorAlert').style.display = 'none';

    fetch('/api/v1/generate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            ...(authToken && { 'Authorization': `Bearer ${authToken}` })
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        document.getElementById('loadingSpinner').style.display = 'none';

        if (result.success) {
            if (monacoEditor) {
                monacoEditor.setValue(result.configuration);
            }
            showNotification('Configuration generated successfully!', 'success');
        } else {
            throw new Error(result.error || 'Generation failed');
        }
    })
    .catch(error => {
        document.getElementById('loadingSpinner').style.display = 'none';
        document.getElementById('errorAlert').textContent = error.message;
        document.getElementById('errorAlert').style.display = 'block';
        showNotification('Error: ' + error.message, 'danger');
    });
}

// Collect Form Data
function collectFormData() {
    const data = {
        platform: document.getElementById('platform').value,
        hostname: document.getElementById('hostname').value,
        domain_name: document.getElementById('domain_name').value,
        enable_secret: document.getElementById('enable_secret').value,
        output_format: document.getElementById('output_format').value,
        interfaces: [],
        ntp_servers: [],
        dns_servers: []
    };

    // NTP
    const ntp = document.getElementById('ntpServers').value;
    if (ntp) {
        data.ntp_servers = ntp.split(',').map(s => s.trim()).filter(s => s);
    }

    // DNS
    const dns = document.getElementById('dnsServers').value;
    if (dns) {
        data.dns_servers = dns.split(',').map(s => s.trim()).filter(s => s);
    }

    // OSPF
    if (document.getElementById('ospfEnabled').checked) {
        data.ospf = {
            enabled: true,
            process_id: parseInt(document.getElementById('ospfProcessId').value) || 1,
            router_id: document.getElementById('ospfRouterId').value || ''
        };
    }

    return data;
}

// Copy Configuration
function copyConfig() {
    if (monacoEditor) {
        const config = monacoEditor.getValue();
        navigator.clipboard.writeText(config).then(() => {
            showNotification('Configuration copied to clipboard!', 'success');
        });
    }
}

// Download Configuration
function downloadConfig() {
    if (monacoEditor) {
        const config = monacoEditor.getValue();
        const hostname = document.getElementById('hostname').value || 'config';
        const blob = new Blob([config], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${hostname}.txt`;
        a.click();
        URL.revokeObjectURL(url);
        showNotification('Configuration downloaded!', 'success');
    }
}

// Show Notification
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} copy-notification`;
    notification.textContent = message;
    notification.style.position = 'fixed';
    notification.style.top = '20px';
    notification.style.right = '20px';
    notification.style.zIndex = '9999';

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// Event Listeners
document.addEventListener('DOMContentLoaded', function() {
    // Load theme
    loadTheme();

    // Initialize Monaco Editor
    initMonacoEditor();

    // Form submission
    const form = document.getElementById('configForm');
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            generateConfig();
        });
    }

    // OSPF toggle
    const ospfToggle = document.getElementById('ospfEnabled');
    if (ospfToggle) {
        ospfToggle.addEventListener('change', function() {
            document.getElementById('ospfConfig').style.display = this.checked ? 'block' : 'none';
        });
    }

    // Login button
    const loginBtn = document.getElementById('loginBtn');
    if (loginBtn) {
        loginBtn.addEventListener('click', function() {
            const loginModal = new bootstrap.Modal(document.getElementById('loginModal'));
            loginModal.show();
        });
    }

    // Login form
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;

            fetch('/auth/login', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({username, password})
            })
            .then(response => response.json())
            .then(data => {
                if (data.access_token) {
                    authToken = data.access_token;
                    localStorage.setItem('authToken', data.access_token);
                    showNotification('Login successful!', 'success');
                    bootstrap.Modal.getInstance(document.getElementById('loginModal')).hide();
                } else {
                    document.getElementById('loginError').textContent = data.error || 'Login failed';
                    document.getElementById('loginError').style.display = 'block';
                }
            });
        });
    }

    // History button
    const historyBtn = document.getElementById('historyBtn');
    if (historyBtn) {
        historyBtn.addEventListener('click', function() {
            window.location.href = '/history/list';
        });
    }
});
