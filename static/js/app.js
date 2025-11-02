// Cisco Configuration Generator - JavaScript
// Token storage
let authToken = localStorage.getItem('authToken');

// OSPF toggle
document.getElementById('ospfEnabled').addEventListener('change', function() {
    document.getElementById('ospfConfig').style.display = this.checked ? 'block' : 'none';
});

// Form submission
document.getElementById('configForm').addEventListener('submit', async function(e) {
    e.preventDefault();

    const formData = getFormData();

    // Show loading
    document.getElementById('loadingSpinner').style.display = 'block';
    document.getElementById('configOutput').textContent = '';
    document.getElementById('errorAlert').style.display = 'none';
    document.getElementById('downloadBtn').style.display = 'none';

    try {
        const response = await fetch('/api/v1/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...(authToken && { 'Authorization': `Bearer ${authToken}` })
            },
            body: JSON.stringify(formData)
        });

        const data = await response.json();

        if (response.ok) {
            document.getElementById('configOutput').textContent = data.configuration;
            document.getElementById('downloadBtn').style.display = 'block';
            document.getElementById('downloadBtn').onclick = () => downloadConfig(data.configuration, data.hostname, data.platform);
        } else {
            showError(data.message || data.error || 'Failed to generate configuration');
        }
    } catch (error) {
        showError('Network error: ' + error.message);
    } finally {
        document.getElementById('loadingSpinner').style.display = 'none';
    }
});

function getFormData() {
    const data = {
        platform: document.getElementById('platform').value,
        hostname: document.getElementById('hostname').value,
        output_format: document.getElementById('output_format').value
    };

    // Optional fields
    if (document.getElementById('domain_name').value) {
        data.domain_name = document.getElementById('domain_name').value;
    }

    if (document.getElementById('enable_secret').value) {
        data.enable_secret = document.getElementById('enable_secret').value;
    }

    // VLANs
    const vlansJson = document.getElementById('vlansJson').value;
    if (vlansJson) {
        try {
            data.vlans = JSON.parse(vlansJson);
        } catch (e) {
            console.error('Invalid VLANs JSON:', e);
        }
    }

    // Static routes
    const routesJson = document.getElementById('staticRoutesJson').value;
    if (routesJson) {
        try {
            data.static_routes = JSON.parse(routesJson);
        } catch (e) {
            console.error('Invalid static routes JSON:', e);
        }
    }

    // OSPF
    if (document.getElementById('ospfEnabled').checked) {
        data.ospf = {
            enabled: true,
            process_id: parseInt(document.getElementById('ospfProcessId').value) || 1,
            router_id: document.getElementById('ospfRouterId').value || null
        };
    }

    // NTP servers
    const ntpServers = document.getElementById('ntpServers').value;
    if (ntpServers) {
        data.ntp_servers = ntpServers.split(',').map(s => s.trim()).filter(s => s);
    }

    // DNS servers
    const dnsServers = document.getElementById('dnsServers').value;
    if (dnsServers) {
        data.dns_servers = dnsServers.split(',').map(s => s.trim()).filter(s => s);
    }

    // Syslog servers
    const syslogServers = document.getElementById('syslogServers').value;
    if (syslogServers) {
        data.syslog_servers = syslogServers.split(',').map(s => s.trim()).filter(s => s);
    }

    return data;
}

function showError(message) {
    const errorAlert = document.getElementById('errorAlert');
    errorAlert.textContent = message;
    errorAlert.style.display = 'block';
}

function downloadConfig(content, hostname, platform) {
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${hostname}_${platform}_config.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

function loadExample() {
    document.getElementById('platform').value = 'ios';
    document.getElementById('hostname').value = 'router01';
    document.getElementById('domain_name').value = 'example.com';
    document.getElementById('vlansJson').value = JSON.stringify([
        { id: 10, name: 'DATA' },
        { id: 20, name: 'VOICE' },
        { id: 30, name: 'MGMT' }
    ], null, 2);
    document.getElementById('staticRoutesJson').value = JSON.stringify([
        { network: '0.0.0.0/0', next_hop: '192.168.1.254' }
    ], null, 2);
    document.getElementById('ntpServers').value = 'pool.ntp.org, time.google.com';
    document.getElementById('dnsServers').value = '8.8.8.8, 8.8.4.4';
}

// Login
document.getElementById('loginBtn').addEventListener('click', function() {
    const loginModal = new bootstrap.Modal(document.getElementById('loginModal'));
    loginModal.show();
});

document.getElementById('loginForm').addEventListener('submit', async function(e) {
    e.preventDefault();

    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    try {
        const response = await fetch('/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        });

        const data = await response.json();

        if (response.ok) {
            authToken = data.access_token;
            localStorage.setItem('authToken', authToken);
            bootstrap.Modal.getInstance(document.getElementById('loginModal')).hide();
            document.getElementById('loginBtn').textContent = 'Logout (' + username + ')';
            alert('Login successful!');
        } else {
            document.getElementById('loginError').textContent = data.message || 'Login failed';
            document.getElementById('loginError').style.display = 'block';
        }
    } catch (error) {
        document.getElementById('loginError').textContent = 'Network error: ' + error.message;
        document.getElementById('loginError').style.display = 'block';
    }
});

// History button
document.getElementById('historyBtn').addEventListener('click', async function() {
    if (!authToken) {
        alert('Please login to view history');
        return;
    }

    try {
        const response = await fetch('/history/list', {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        const data = await response.json();

        if (response.ok) {
            alert(`You have ${data.total} configurations in history`);
            // TODO: Show history in a modal
        } else {
            alert('Failed to fetch history');
        }
    } catch (error) {
        alert('Network error: ' + error.message);
    }
});

// Interface management
let interfaceCount = 0;

function addInterface() {
    interfaceCount++;
    const interfaceDiv = document.createElement('div');
    interfaceDiv.className = 'border rounded p-2 mb-2';
    interfaceDiv.innerHTML = `
        <div class="mb-2">
            <input type="text" class="form-control form-control-sm" placeholder="Interface name (e.g., GigabitEthernet0/0)" id="interface_name_${interfaceCount}">
        </div>
        <div class="row">
            <div class="col-6">
                <input type="text" class="form-control form-control-sm" placeholder="IP Address" id="interface_ip_${interfaceCount}">
            </div>
            <div class="col-6">
                <input type="text" class="form-control form-control-sm" placeholder="Mask" id="interface_mask_${interfaceCount}">
            </div>
        </div>
        <button type="button" class="btn btn-sm btn-danger mt-2" onclick="this.parentElement.remove()">Remove</button>
    `;
    document.getElementById('interfaceList').appendChild(interfaceDiv);
}
