# CCIE Configuration Generator Guide

## Overview

The CCIE Configuration Generator is an advanced feature that supports **ALL Cisco protocols** across **Switch, Router, and Firewall** platforms. This tool is designed for **CCIE-level engineers** who need to generate complex, production-ready configurations.

## Supported Protocols

### Layer 2 Protocols (Switch)
- **VLANs**: Standard (1-4094), voice VLANs, private VLANs
- **Spanning Tree**: PVST+, Rapid-PVST+, MST
- **EtherChannel**: LACP, PAgP, static aggregation
- **VTP**: Server, client, transparent modes
- **QinQ**: 802.1Q tunneling
- **Security**: Port security, DAI, DHCP snooping, IGMP snooping

### Layer 3 Protocols (Router/L3 Switch)
- **Static Routing**: IPv4/IPv6 static routes with administrative distance
- **OSPF**: v2/v3, multi-area, stub/NSSA, authentication, BFD
- **EIGRP**: Classic and named mode, stub configuration
- **IS-IS**: Multi-level, wide metrics
- **RIP**: v1/v2
- **BGP**: iBGP, eBGP, route reflectors, confederations, multipath
- **PBR**: Policy-based routing
- **VRF**: VRF-Lite for segmentation
- **MPLS**: Label switching, VPNv4
- **Segment Routing**: SR-MPLS

### Redundancy Protocols
- **HSRP**: v1/v2, preemption, authentication
- **VRRP**: Standard FHRP
- **GLBP**: Load balancing across multiple gateways

### Multicast
- **IGMP**: v1/v2/v3
- **PIM**: Sparse Mode, Dense Mode, SSM, BIDIR
- **MSDP**: Multicast source discovery
- **Rendezvous Points**: Static, Auto-RP, BSR, Anycast-RP

### VPN Technologies
- **IPsec**: Site-to-site, IKEv1/v2, AES-256, SHA-256
- **GRE**: Generic Routing Encapsulation
- **DMVPN**: Dynamic Multipoint VPN (Phase 1/2/3)
- **FlexVPN**: Next-generation IKEv2-based VPN
- **GETVPN**: Group Encrypted Transport VPN
- **L2TP**: Layer 2 tunneling
- **SSL VPN**: Remote access (AnyConnect)

### Security
- **ACLs**: Standard, extended, IPv6 ACLs
- **Zone-Based Firewall**: Stateful inspection
- **CBAC**: Context-Based Access Control (legacy)
- **ASA Policies**: Object groups, NAT, access rules
- **IPS/IDS**: Intrusion prevention/detection
- **TrustSec**: SGT tagging
- **802.1X**: Port-based authentication
- **DAI**: Dynamic ARP Inspection
- **DHCP Snooping**: Rogue DHCP prevention

### Quality of Service (QoS)
- **Classification**: DSCP, CoS, ACLs, NBAR2
- **Marking**: Layer 2/3 marking
- **Queueing**: LLQ (Low-Latency Queue), CBWFQ
- **Shaping**: Traffic shaping policies
- **Policing**: Rate limiting
- **WRED**: Weighted Random Early Detection
- **AutoQoS**: Automatic QoS configuration

### Network Services
- **NAT/PAT**: Static, dynamic, overload
- **DHCP**: Server, relay, snooping
- **DNS**: Client, proxy
- **SNMP**: v2c, v3 with authentication/encryption
- **Syslog**: Centralized logging
- **NTP**: Time synchronization with authentication
- **PTP**: Precision Time Protocol
- **NetFlow/IPFIX**: Traffic analysis
- **EEM**: Embedded Event Manager

### Infrastructure Services
- **BFD**: Bidirectional Forwarding Detection (sub-second failover)
- **NSF/SSO**: Non-Stop Forwarding, Stateful Switchover
- **ISSU**: In-Service Software Upgrade
- **Stack/Cluster**: StackWise, VSS, vPC
- **CoPP**: Control Plane Policing
- **Smart Licensing**: Cisco licensing framework
- **NETCONF/RESTCONF**: Programmable interfaces

## API Endpoint

### CCIE Generate Endpoint

**URL**: `POST /api/v1/generate-ccie`

**Headers**:
```
Content-Type: application/json
Authorization: Bearer <token>  (optional)
X-API-Key: <api-key>           (optional)
```

### Request Schema

```json
{
  "device_type": "router",           // required: "switch" | "router" | "firewall"
  "platform": "ios-xe",              // required: "ios" | "ios-xe" | "nxos" | "ios-xr" | "asa" | "ftd"
  "hostname": "PAR-CORE-1",          // required

  // Basic configuration
  "domain_name": "enterprise.com",
  "enable_secret": "encrypted_secret",
  "loopbacks": ["10.255.0.1/32"],

  // Interfaces
  "interfaces": [
    {
      "name": "GigabitEthernet0/0",
      "description": "WAN Link",
      "ip": "192.168.1.1/24",
      "speed": "1000",
      "duplex": "full"
    }
  ],

  // VLANs (for switches)
  "vlans": [
    {
      "id": 10,
      "name": "DATA",
      "description": "User data VLAN"
    }
  ],

  // Layer 2 protocols
  "spanning_tree": {
    "mode": "rapid-pvst",
    "priority": 8192,
    "root": true
  },

  "etherchannel": [
    {
      "id": 1,
      "mode": "active",
      "protocol": "lacp",
      "members": ["GigabitEthernet0/1", "GigabitEthernet0/2"]
    }
  ],

  // Routing configuration
  "routing": {
    "static": [
      {
        "prefix": "0.0.0.0/0",
        "next_hop": "192.168.1.254",
        "distance": 1
      }
    ],

    "ospf": {
      "process_id": 100,
      "router_id": "10.255.0.1",
      "bfd": true,
      "nsf": true,
      "areas": [
        {
          "id": 0,
          "networks": ["10.10.0.0/16"],
          "stub": false,
          "nssa": false,
          "authentication": "md5"
        }
      ]
    },

    "eigrp": {
      "asn": 100,
      "router_id": "10.255.0.1",
      "named_mode": true,
      "networks": ["10.20.0.0/16"],
      "stub": false
    },

    "isis": {
      "process": "CORE",
      "net": "49.0001.1921.6800.1001.00",
      "level": "level-2",
      "metric_style": "wide"
    },

    "bgp": {
      "asn": 65010,
      "router_id": "10.255.0.1",
      "neighbors": [
        {
          "ip": "192.0.2.1",
          "remote_as": 65000,
          "description": "MPLS PE",
          "update_source": "Loopback0",
          "ebgp_multihop": 2
        }
      ],
      "networks": ["10.10.0.0/16"],
      "maximum_paths": 4
    },

    "rip": {
      "version": 2,
      "networks": ["10.30.0.0/16"]
    }
  },

  // Redundancy
  "redundancy": {
    "hsrp": [
      {
        "interface": "GigabitEthernet0/1",
        "group": 10,
        "vip": "10.10.0.254",
        "priority": 110,
        "preempt": true,
        "version": 2
      }
    ],

    "vrrp": [
      {
        "interface": "GigabitEthernet0/2",
        "group": 5,
        "vip": "10.20.0.254",
        "priority": 100
      }
    ],

    "glbp": [
      {
        "interface": "GigabitEthernet0/3",
        "group": 1,
        "vip": "10.30.0.254",
        "load_balancing": "round-robin"
      }
    ]
  },

  // Multicast
  "multicast": {
    "enabled": true,
    "igmp_version": 3,
    "pim_mode": "sparse-mode",
    "rp": {
      "type": "static",
      "address": "10.255.0.10"
    }
  },

  // Security
  "security": {
    "aaa": {
      "tacacs": [
        {"host": "10.1.1.1", "key": "tacacs_secret"}
      ],
      "radius": [
        {"host": "10.1.1.2", "key": "radius_secret"}
      ],
      "local_users": {
        "admin": "admin_password",
        "netops": "netops_password"
      }
    },

    "acl": [
      {
        "name": "ACL-MGMT",
        "type": "extended",
        "entries": [
          {
            "action": "permit",
            "protocol": "tcp",
            "source": "10.0.0.0/8",
            "destination": "any",
            "port": 22
          }
        ]
      }
    ],

    "zone_fw": {
      "zones": ["INSIDE", "OUTSIDE", "DMZ"],
      "rules": [
        {
          "source_zone": "INSIDE",
          "destination_zone": "OUTSIDE",
          "action": "inspect"
        }
      ]
    },

    "vpn": {
      "type": "ipsec",
      "ike_version": 2,
      "encryption": "aes-256-gcm",
      "hash": "sha256",
      "dh_group": 19,
      "peers": [
        {
          "peer_ip": "203.0.113.2",
          "psk": "vpn_secret",
          "local_subnet": "10.10.0.0/24",
          "remote_subnet": "10.20.0.0/24"
        }
      ]
    },

    "port_security": true,
    "dhcp_snooping": true,
    "dai": true
  },

  // NAT
  "nat": {
    "inside": "GigabitEthernet0/1",
    "outside": "GigabitEthernet0/0",
    "rules": [
      {
        "source": "10.10.0.0/24",
        "action": "overload"
      }
    ]
  },

  // QoS
  "qos": {
    "enabled": true,
    "policy_name": "WAN-QOS",
    "classes": [
      {
        "name": "VOICE",
        "dscp": "dscp ef",
        "priority": "strict"
      },
      {
        "name": "CRITICAL",
        "dscp": "dscp af31",
        "bandwidth": "30%"
      }
    ]
  },

  // Services
  "services": {
    "ntp": ["192.0.2.10", "192.0.2.11"],
    "dns": ["8.8.8.8", "8.8.4.4"],
    "syslog": ["10.255.1.10"],
    "snmp": {
      "version": 3,
      "users": ["netmon"],
      "location": "Paris Data Center",
      "contact": "netops@enterprise.com"
    },
    "dhcp": {
      "network": "10.10.0.0/24",
      "default_gateway": "10.10.0.1",
      "dns": ["8.8.8.8"]
    },
    "netflow": true,
    "ptp": false
  },

  // Output options
  "output_format": "cli",           // "cli" | "json" | "yaml"
  "generate_validation": true,
  "generate_explanation": true,
  "tags": "production,datacenter",
  "version": "1.0"
}
```

### Response Schema

```json
{
  "success": true,
  "platform": "ios-xe",
  "device_type": "router",
  "hostname": "PAR-CORE-1",
  "output_format": "cli",
  "history_id": 123,

  "configuration": "! Complete CLI configuration...",

  "validation": {
    "valid": true,
    "errors": [],
    "warnings": [
      "Enable secret not configured - set immediately for production"
    ],
    "suggestions": [
      "Consider enabling BFD on OSPF for faster convergence"
    ],
    "total_checks": 15,
    "timestamp": "2024-01-15T10:30:00.000Z"
  },

  "explanation": "=== CCIE-Level Configuration Explanation ===\n\n..."
}
```

## Usage Examples

### Example 1: Enterprise Edge Router

```bash
curl -X POST http://localhost:5000/api/v1/generate-ccie \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "device_type": "router",
    "platform": "ios-xe",
    "hostname": "EDGE-RTR-01",
    "domain_name": "corp.local",
    "loopbacks": ["10.255.1.1/32"],

    "interfaces": [
      {
        "name": "GigabitEthernet0/0",
        "description": "Internet",
        "ip": "203.0.113.10/30"
      },
      {
        "name": "GigabitEthernet0/1",
        "description": "LAN",
        "ip": "10.10.1.1/24"
      }
    ],

    "routing": {
      "static": [
        {"prefix": "0.0.0.0/0", "next_hop": "203.0.113.9"}
      ],
      "ospf": {
        "process_id": 1,
        "router_id": "10.255.1.1",
        "bfd": true,
        "areas": [
          {"id": 0, "networks": ["10.10.0.0/16"]}
        ]
      }
    },

    "security": {
      "aaa": {
        "tacacs": [{"host": "10.10.1.100"}],
        "local_users": {"admin": "Cisco123!"}
      },
      "vpn": {
        "type": "ipsec",
        "peers": [
          {
            "peer_ip": "198.51.100.10",
            "local_subnet": "10.10.0.0/16",
            "remote_subnet": "10.20.0.0/16"
          }
        ]
      }
    },

    "nat": {
      "inside": "GigabitEthernet0/1",
      "outside": "GigabitEthernet0/0",
      "rules": [
        {"source": "10.10.0.0/16", "action": "overload"}
      ]
    },

    "qos": {
      "enabled": true,
      "classes": [
        {"name": "VOICE", "dscp": "dscp ef", "priority": "strict"},
        {"name": "DATA", "bandwidth": "50%"}
      ]
    },

    "services": {
      "ntp": ["pool.ntp.org"],
      "snmp": {"version": 3, "users": ["netmon"]},
      "syslog": ["10.10.1.200"]
    }
  }'
```

### Example 2: Data Center Switch with VXLAN

```json
{
  "device_type": "switch",
  "platform": "nxos",
  "hostname": "DC-SPINE-01",

  "vlans": [
    {"id": 10, "name": "WEB"},
    {"id": 20, "name": "APP"},
    {"id": 30, "name": "DB"}
  ],

  "spanning_tree": {
    "mode": "mst",
    "priority": 4096
  },

  "etherchannel": [
    {
      "id": 10,
      "mode": "active",
      "members": ["Ethernet1/1", "Ethernet1/2"]
    }
  ],

  "routing": {
    "ospf": {
      "process_id": 1,
      "bfd": true,
      "areas": [{"id": 0, "networks": ["10.0.0.0/8"]}]
    },
    "bgp": {
      "asn": 65001,
      "neighbors": [
        {"ip": "10.0.1.1", "remote_as": 65001},
        {"ip": "10.0.1.2", "remote_as": 65001}
      ]
    }
  }
}
```

## Validation and Best Practices

The CCIE generator automatically:

1. **Validates all inputs**: IP addresses, ASNs, VLAN IDs, interface names
2. **Applies security hardening**:
   - SSH v2 only (Telnet disabled)
   - Control Plane Policing (CoPP)
   - AAA authentication
   - Encrypted passwords
3. **Implements best practices**:
   - Service timestamps for logging
   - BFD for fast convergence
   - Explicit router IDs
   - Proper command hierarchy
4. **Generates warnings**:
   - Missing enable secret
   - Weak crypto settings
   - Deprecated protocols
5. **Provides suggestions**:
   - BFD enablement
   - NTP configuration
   - Centralized logging

## Output Formats

### CLI Format (Default)
Complete Cisco CLI configuration with:
- Hierarchical structure
- Commented sections
- Best practices applied

### JSON Format
Structured JSON representing the configuration

### YAML Format
YAML format for automation tools

## CCIE-Level Features

### Explanation Generation

When `generate_explanation: true`, you receive a detailed technical explanation covering:

- **Protocol operation**: How each protocol works
- **Design decisions**: Why certain configurations are applied
- **Convergence**: Expected convergence times
- **Scalability**: Scalability considerations
- **Best practices**: CCIE-level best practices applied

### Validation Report

When `generate_validation: true`, you receive:

- **Errors**: Configuration errors that must be fixed
- **Warnings**: Important issues that should be addressed
- **Suggestions**: Optional improvements for better design

## Integration with CI/CD

Use the CCIE API in your automation pipelines:

```python
import requests

config_data = {
    "device_type": "router",
    "platform": "ios-xe",
    "hostname": "ROUTER-01",
    # ... rest of config
}

response = requests.post(
    'http://localhost:5000/api/v1/generate-ccie',
    json=config_data,
    headers={'X-API-Key': 'your-api-key'}
)

if response.json()['validation']['valid']:
    config = response.json()['configuration']
    # Deploy configuration
else:
    errors = response.json()['validation']['errors']
    print(f"Configuration errors: {errors}")
```

## Troubleshooting

### Common Issues

**Issue**: Schema validation error

**Solution**: Check that all required fields are present and field types are correct

**Issue**: Template not found

**Solution**: Ensure the platform is supported: ios, ios-xe, nxos, ios-xr, asa, ftd

**Issue**: Invalid IP address format

**Solution**: Use CIDR notation (e.g., 192.168.1.0/24) or separate IP and mask

## Support

For CCIE-specific questions:
- Review the API schema: `GET /api/v1/ccie-schema`
- Check examples: `GET /api/v1/ccie-examples`
- Consult documentation: `docs/CCIE_GUIDE.md`

## References

- Cisco IOS Configuration Guide
- Cisco NX-OS Configuration Guide
- Cisco ASA Configuration Guide
- RFC standards for routing protocols
- CCIE Routing & Switching Study Guide
- CCIE Security Study Guide
