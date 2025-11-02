"""
Extended Marshmallow schemas for CCIE-level configuration generation.
Supports all Cisco protocols: L2, L3, Multicast, VPN, Security, QoS, Services.
"""
from marshmallow import Schema, fields, validate, validates, ValidationError


# ============ ROUTING PROTOCOLS ============

class OSPFNetworkSchema(Schema):
    """OSPF network schema."""
    network = fields.Str(required=True)
    wildcard = fields.Str(required=True)
    area = fields.Int(required=True)


class OSPFAreaSchema(Schema):
    """OSPF area configuration."""
    id = fields.Int(required=True)
    networks = fields.List(fields.Str(), required=False)
    stub = fields.Bool(required=False)
    nssa = fields.Bool(required=False)
    authentication = fields.Str(required=False, validate=validate.OneOf(['md5', 'text', 'null']))


class OSPFSchema(Schema):
    """Enhanced OSPFv2/v3 configuration."""
    process_id = fields.Int(required=True)
    router_id = fields.Str(required=False)
    areas = fields.List(fields.Nested(OSPFAreaSchema), required=False)
    passive_interfaces = fields.List(fields.Str(), required=False)
    redistribute = fields.List(fields.Str(), required=False)
    bfd = fields.Bool(required=False, load_default=False)
    nsf = fields.Bool(required=False, load_default=False)


class EIGRPSchema(Schema):
    """EIGRP configuration."""
    asn = fields.Int(required=True)
    router_id = fields.Str(required=False)
    networks = fields.List(fields.Str(), required=False)
    named_mode = fields.Bool(required=False, load_default=False)
    stub = fields.Bool(required=False)


class ISISSchema(Schema):
    """IS-IS configuration."""
    process = fields.Str(required=True)
    net = fields.Str(required=True)  # NET address
    level = fields.Str(required=False, validate=validate.OneOf(['level-1', 'level-2', 'level-1-2']))
    metric_style = fields.Str(required=False, validate=validate.OneOf(['narrow', 'wide']))


class BGPNeighborSchema(Schema):
    """BGP neighbor configuration."""
    ip = fields.Str(required=True)
    remote_as = fields.Int(required=True)
    description = fields.Str(required=False)
    update_source = fields.Str(required=False)
    ebgp_multihop = fields.Int(required=False)
    password = fields.Str(required=False)
    route_reflector_client = fields.Bool(required=False)


class BGPSchema(Schema):
    """BGP configuration."""
    asn = fields.Int(required=True)
    router_id = fields.Str(required=False)
    neighbors = fields.List(fields.Nested(BGPNeighborSchema), required=False)
    networks = fields.List(fields.Str(), required=False)
    redistribute = fields.List(fields.Str(), required=False)
    maximum_paths = fields.Int(required=False)


class RIPSchema(Schema):
    """RIP configuration."""
    version = fields.Int(required=False, validate=validate.OneOf([1, 2]))
    networks = fields.List(fields.Str(), required=False)


class RoutingSchema(Schema):
    """Complete routing configuration."""
    static = fields.List(fields.Dict(), required=False)
    ospf = fields.Nested(OSPFSchema, required=False)
    eigrp = fields.Nested(EIGRPSchema, required=False)
    isis = fields.Nested(ISISSchema, required=False)
    bgp = fields.Nested(BGPSchema, required=False)
    rip = fields.Nested(RIPSchema, required=False)


# ============ REDUNDANCY PROTOCOLS ============

class HSRPGroupSchema(Schema):
    """HSRP group configuration."""
    interface = fields.Str(required=True)
    group = fields.Int(required=True)
    vip = fields.Str(required=True)
    priority = fields.Int(required=False, load_default=100)
    preempt = fields.Bool(required=False, load_default=True)
    version = fields.Int(required=False, validate=validate.OneOf([1, 2]))


class VRRPGroupSchema(Schema):
    """VRRP group configuration."""
    interface = fields.Str(required=True)
    group = fields.Int(required=True)
    vip = fields.Str(required=True)
    priority = fields.Int(required=False, load_default=100)
    preempt = fields.Bool(required=False, load_default=True)


class GLBPGroupSchema(Schema):
    """GLBP group configuration."""
    interface = fields.Str(required=True)
    group = fields.Int(required=True)
    vip = fields.Str(required=True)
    priority = fields.Int(required=False, load_default=100)
    load_balancing = fields.Str(required=False, validate=validate.OneOf(['round-robin', 'weighted', 'host-dependent']))


class RedundancySchema(Schema):
    """FHRP configuration."""
    hsrp = fields.List(fields.Nested(HSRPGroupSchema), required=False)
    vrrp = fields.List(fields.Nested(VRRPGroupSchema), required=False)
    glbp = fields.List(fields.Nested(GLBPGroupSchema), required=False)


# ============ MULTICAST ============

class MulticastRPSchema(Schema):
    """Multicast RP configuration."""
    type = fields.Str(required=True, validate=validate.OneOf(['static', 'auto-rp', 'bsr', 'anycast']))
    address = fields.Str(required=False)
    groups = fields.List(fields.Str(), required=False)


class MulticastSchema(Schema):
    """Multicast configuration."""
    enabled = fields.Bool(required=False, load_default=False)
    igmp_version = fields.Int(required=False, validate=validate.OneOf([1, 2, 3]))
    pim_mode = fields.Str(required=False, validate=validate.OneOf(['sparse-mode', 'dense-mode', 'sparse-dense-mode', 'ssm', 'bidir']))
    rp = fields.Nested(MulticastRPSchema, required=False)
    sso = fields.Bool(required=False)


# ============ VPN ============

class IPSecPeerSchema(Schema):
    """IPSec VPN peer."""
    peer_ip = fields.Str(required=True)
    psk = fields.Str(required=False)
    local_subnet = fields.Str(required=False)
    remote_subnet = fields.Str(required=False)
    tunnel_interface = fields.Str(required=False)


class VPNSchema(Schema):
    """VPN configuration."""
    type = fields.Str(required=True, validate=validate.OneOf(['ipsec', 'dmvpn', 'getvpn', 'flexvpn', 'ssl', 'l2tp']))
    peers = fields.List(fields.Nested(IPSecPeerSchema), required=False)
    ike_version = fields.Int(required=False, validate=validate.OneOf([1, 2]), load_default=2)
    encryption = fields.Str(required=False, load_default='aes-256-gcm')
    hash = fields.Str(required=False, load_default='sha256')
    dh_group = fields.Int(required=False, load_default=19)


# ============ SECURITY ============

class ACLEntrySchema(Schema):
    """ACL entry."""
    action = fields.Str(required=True, validate=validate.OneOf(['permit', 'deny']))
    protocol = fields.Str(required=False, load_default='ip')
    source = fields.Str(required=False)
    destination = fields.Str(required=False)
    port = fields.Int(required=False)


class ACLSchema(Schema):
    """Access Control List."""
    name = fields.Str(required=True)
    type = fields.Str(required=True, validate=validate.OneOf(['standard', 'extended', 'ipv6']))
    entries = fields.List(fields.Nested(ACLEntrySchema), required=False)


class ZoneFirewallRuleSchema(Schema):
    """Zone-based firewall rule."""
    source_zone = fields.Str(required=True)
    destination_zone = fields.Str(required=True)
    action = fields.Str(required=True, validate=validate.OneOf(['inspect', 'pass', 'drop']))
    class_map = fields.Str(required=False)


class ZoneFirewallSchema(Schema):
    """Zone-based firewall configuration."""
    zones = fields.List(fields.Str(), required=False)
    rules = fields.List(fields.Nested(ZoneFirewallRuleSchema), required=False)


class AAAServerSchema(Schema):
    """AAA server configuration."""
    host = fields.Str(required=True)
    key = fields.Str(required=False)
    port = fields.Int(required=False)


class AAASchema(Schema):
    """AAA configuration."""
    radius = fields.List(fields.Nested(AAAServerSchema), required=False)
    tacacs = fields.List(fields.Nested(AAAServerSchema), required=False)
    local_users = fields.Dict(required=False)
    dot1x = fields.Bool(required=False)


class SecuritySchema(Schema):
    """Complete security configuration."""
    acl = fields.List(fields.Nested(ACLSchema), required=False)
    zone_fw = fields.Nested(ZoneFirewallSchema, required=False)
    vpn = fields.Nested(VPNSchema, required=False)
    aaa = fields.Nested(AAASchema, required=False)
    port_security = fields.Bool(required=False)
    dhcp_snooping = fields.Bool(required=False)
    dai = fields.Bool(required=False)
    ip_source_guard = fields.Bool(required=False)


# ============ NAT ============

class NATRuleSchema(Schema):
    """NAT rule."""
    source = fields.Str(required=True)
    action = fields.Str(required=True, validate=validate.OneOf(['static', 'dynamic', 'overload', 'pat']))
    pool = fields.Str(required=False)
    interface = fields.Str(required=False)


class NATSchema(Schema):
    """NAT configuration."""
    inside = fields.Str(required=False)
    outside = fields.Str(required=False)
    rules = fields.List(fields.Nested(NATRuleSchema), required=False)


# ============ QoS ============

class QoSClassSchema(Schema):
    """QoS class configuration."""
    name = fields.Str(required=True)
    match = fields.Str(required=False)
    dscp = fields.Str(required=False)
    priority = fields.Str(required=False)
    bandwidth = fields.Str(required=False)
    shape = fields.Str(required=False)
    police = fields.Str(required=False)


class QoSSchema(Schema):
    """QoS configuration."""
    enabled = fields.Bool(required=False, load_default=False)
    classes = fields.List(fields.Nested(QoSClassSchema), required=False)
    policy_name = fields.Str(required=False)


# ============ SERVICES ============

class DHCPPoolSchema(Schema):
    """DHCP pool configuration."""
    name = fields.Str(required=False)
    network = fields.Str(required=True)
    default_gateway = fields.Str(required=False)
    dns = fields.List(fields.Str(), required=False)
    lease_time = fields.Int(required=False)


class SNMPSchema(Schema):
    """SNMP configuration."""
    version = fields.Int(required=False, validate=validate.OneOf([2, 3]), load_default=3)
    community = fields.Str(required=False)
    users = fields.List(fields.Str(), required=False)
    location = fields.Str(required=False)
    contact = fields.Str(required=False)


class ServicesSchema(Schema):
    """Network services configuration."""
    ntp = fields.List(fields.Str(), required=False)
    dns = fields.List(fields.Str(), required=False)
    dhcp = fields.Nested(DHCPPoolSchema, required=False)
    snmp = fields.Nested(SNMPSchema, required=False)
    syslog = fields.List(fields.Str(), required=False)
    netflow = fields.Bool(required=False)
    ptp = fields.Bool(required=False)


# ============ L2 PROTOCOLS ============

class SpanningTreeSchema(Schema):
    """Spanning Tree configuration."""
    mode = fields.Str(required=False, validate=validate.OneOf(['pvst', 'rapid-pvst', 'mst']))
    priority = fields.Int(required=False)
    root = fields.Bool(required=False)


class EtherChannelSchema(Schema):
    """EtherChannel/Port-Channel configuration."""
    id = fields.Int(required=True)
    mode = fields.Str(required=False, validate=validate.OneOf(['active', 'passive', 'on', 'desirable', 'auto']))
    protocol = fields.Str(required=False, validate=validate.OneOf(['lacp', 'pagp', 'none']))
    members = fields.List(fields.Str(), required=False)


class VLANExtendedSchema(Schema):
    """Extended VLAN configuration."""
    id = fields.Int(required=True, validate=validate.Range(min=1, max=4094))
    name = fields.Str(required=True)
    description = fields.Str(required=False)
    stp_priority = fields.Int(required=False)
    private_vlan_type = fields.Str(required=False, validate=validate.OneOf(['primary', 'isolated', 'community']))


# ============ MAIN CONFIG SCHEMA ============

class CCIEConfigSchema(Schema):
    """Complete CCIE-level configuration schema."""
    # Device identification
    device_type = fields.Str(required=True, validate=validate.OneOf(['switch', 'router', 'firewall']))
    platform = fields.Str(required=True, validate=validate.OneOf(['ios', 'ios-xe', 'nxos', 'ios-xr', 'asa', 'ftd']))
    hostname = fields.Str(required=True)

    # Basic configuration
    domain_name = fields.Str(required=False)
    enable_secret = fields.Str(required=False)
    loopbacks = fields.List(fields.Str(), required=False)

    # Interfaces
    interfaces = fields.List(fields.Dict(), required=False)

    # VLANs (L2)
    vlans = fields.List(fields.Nested(VLANExtendedSchema), required=False)

    # L2 protocols
    spanning_tree = fields.Nested(SpanningTreeSchema, required=False)
    etherchannel = fields.List(fields.Nested(EtherChannelSchema), required=False)
    vtp = fields.Dict(required=False)

    # Routing
    routing = fields.Nested(RoutingSchema, required=False)

    # Redundancy
    redundancy = fields.Nested(RedundancySchema, required=False)

    # Multicast
    multicast = fields.Nested(MulticastSchema, required=False)

    # Security
    security = fields.Nested(SecuritySchema, required=False)

    # NAT
    nat = fields.Nested(NATSchema, required=False)

    # QoS
    qos = fields.Nested(QoSSchema, required=False)

    # Services
    services = fields.Nested(ServicesSchema, required=False)

    # Output format
    output_format = fields.Str(required=False, load_default='cli', validate=validate.OneOf(['cli', 'json', 'yaml']))

    # Metadata
    tags = fields.Str(required=False)
    version = fields.Str(required=False)
    generate_explanation = fields.Bool(required=False, load_default=True)
    generate_validation = fields.Bool(required=False, load_default=True)
