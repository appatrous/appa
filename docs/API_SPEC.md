# API Specification

## Overview

The Cisco Configuration Generator provides a RESTful API for programmatic configuration generation.

**Base URL**: `http://localhost:5000/api/v1`

**Content-Type**: `application/json`

**Authentication**: Bearer Token (JWT) or API Key

## Authentication

### Bearer Token

Include in request header:
```
Authorization: Bearer <access_token>
```

### API Key

Include in request header:
```
X-API-Key: cck_<your_api_key>
```

## Endpoints

### 1. Generate Configuration

**POST** `/api/v1/generate`

Generate device configuration from provided parameters.

#### Request Body

```json
{
  "platform": "ios",
  "hostname": "router01",
  "domain_name": "example.com",
  "enable_secret": "encrypted_password",
  "interfaces": [
    {
      "name": "GigabitEthernet0/0",
      "description": "WAN Interface",
      "ip_address": "192.168.1.1",
      "subnet_mask": "255.255.255.0",
      "enabled": true
    }
  ],
  "vlans": [
    {"id": 10, "name": "DATA", "description": "Data VLAN"},
    {"id": 20, "name": "VOICE", "description": "Voice VLAN"}
  ],
  "static_routes": [
    {
      "network": "0.0.0.0/0",
      "next_hop": "192.168.1.254",
      "distance": 1
    }
  ],
  "ospf": {
    "enabled": true,
    "process_id": 1,
    "router_id": "1.1.1.1",
    "networks": [
      {
        "network": "192.168.1.0",
        "wildcard": "0.0.0.255",
        "area": 0
      }
    ]
  },
  "ntp_servers": ["pool.ntp.org", "time.google.com"],
  "dns_servers": ["8.8.8.8", "8.8.4.4"],
  "syslog_servers": ["192.168.1.100"],
  "aaa": {
    "tacacs_servers": [
      {
        "host": "192.168.1.50",
        "key": "tacacs_key"
      }
    ],
    "local_users": {
      "admin": "admin_password",
      "netops": "netops_password"
    }
  },
  "banner_motd": "Authorized Access Only",
  "snmp_community": "public",
  "snmp_location": "Data Center",
  "snmp_contact": "netops@example.com",
  "output_format": "cli",
  "tags": "production,datacenter",
  "version": "1.0"
}
```

#### Required Fields
- `platform`: One of ["ios", "nxos", "asa", "iosxr"]
- `hostname`: Device hostname (1-63 characters)

#### Optional Fields
- `domain_name`: DNS domain name
- `enable_secret`: Enable password
- `interfaces`: Array of interface configurations
- `vlans`: Array of VLAN configurations
- `static_routes`: Array of static routes
- `ospf`: OSPF configuration object
- `ntp_servers`: Array of NTP server addresses
- `dns_servers`: Array of DNS server addresses
- `syslog_servers`: Array of syslog server addresses
- `aaa`: AAA configuration object
- `banner_motd`: MOTD banner text
- `banner_login`: Login banner text
- `snmp_community`: SNMP community string
- `snmp_location`: SNMP location
- `snmp_contact`: SNMP contact
- `output_format`: One of ["cli", "json", "yaml"] (default: "cli")
- `tags`: Comma-separated tags
- `version`: Configuration version

#### Response (200 OK)

```json
{
  "success": true,
  "platform": "ios",
  "hostname": "router01",
  "output_format": "cli",
  "configuration": "!\n! Cisco IOS Configuration\n...",
  "history_id": 123
}
```

#### Error Response (400 Bad Request)

```json
{
  "error": "Validation Error",
  "details": {
    "hostname": ["Missing required field"],
    "vlans": {
      "0": {
        "id": ["VLAN ID must be between 1-4094"]
      }
    }
  }
}
```

### 2. Validate Configuration

**POST** `/api/v1/validate`

Validate configuration data without generating output.

#### Request Body

Same as `/api/v1/generate`

#### Response (200 OK)

```json
{
  "valid": true,
  "message": "Configuration data is valid",
  "platform": "ios",
  "hostname": "router01"
}
```

Or if invalid:

```json
{
  "valid": false,
  "error": "Data Validation Error",
  "message": "Invalid VLAN ID: 5000"
}
```

### 3. List Platforms

**GET** `/api/v1/platforms`

Get list of supported platforms.

#### Response (200 OK)

```json
{
  "platforms": ["ios", "nxos", "asa", "iosxr"]
}
```

### 4. Get Schema

**GET** `/api/v1/schema`

Get API schema documentation.

#### Response (200 OK)

```json
{
  "version": "v1",
  "endpoint": "/api/v1/generate",
  "method": "POST",
  "content_type": "application/json",
  "schema": {
    "required_fields": ["platform", "hostname"],
    "supported_platforms": ["ios", "nxos", "asa", "iosxr"],
    "output_formats": ["cli", "json", "yaml"],
    "optional_fields": [...]
  },
  "example": {...}
}
```

## Platform-Specific Considerations

### IOS
- Interface names: GigabitEthernet, FastEthernet, Loopback, Vlan
- OSPF process ID: 1-65535
- Example: `GigabitEthernet0/0`

### NX-OS
- Interface names: Ethernet, loopback, Vlan, port-channel
- IP addresses use CIDR notation
- Example: `Ethernet1/1`

### ASA
- Interface names: GigabitEthernet, Management, Vlan
- Security levels required
- Example: `GigabitEthernet0/0`

### IOS-XR
- Interface names: GigabitEthernet, TenGigE, Loopback
- Different configuration syntax
- Example: `GigabitEthernet0/0/0/0`

## Rate Limiting

Default: 100 requests per hour per IP address

When rate limit exceeded:

```json
{
  "error": "Rate Limit Exceeded",
  "message": "Too many requests. Try again in X seconds."
}
```

## Error Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Missing or invalid authentication |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found |
| 409 | Conflict - Duplicate resource |
| 413 | Payload Too Large |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error |

## Examples

### Generate IOS Configuration

```bash
curl -X POST http://localhost:5000/api/v1/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "platform": "ios",
    "hostname": "edge-router",
    "vlans": [
      {"id": 10, "name": "USERS"},
      {"id": 20, "name": "SERVERS"}
    ],
    "ntp_servers": ["pool.ntp.org"]
  }'
```

### Generate with API Key

```bash
curl -X POST http://localhost:5000/api/v1/generate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: cck_your_api_key" \
  -d '{
    "platform": "nxos",
    "hostname": "dc-switch-01"
  }'
```

### Get JSON Output

```bash
curl -X POST http://localhost:5000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "ios",
    "hostname": "router01",
    "output_format": "json"
  }'
```
