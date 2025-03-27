"""
Configuration data for Cisco Switch Configurator, extracted from the Cisco Switch Configuration Guide.
"""

# Add a new category at the beginning of the CONFIG_DATA dictionary
CONFIG_DATA = {
    "Initial Setup": [
        {
            "name": "Skip Initial Configuration Dialog",
            "command": "no",
            "description": "Respond 'no' when the switch asks 'Would you like to enter the initial configuration dialog?'",
            "inputs": []
        },
        {
            "name": "Accept Initial Configuration Dialog",
            "command": "yes",
            "description": "Respond 'yes' when the switch asks 'Would you like to enter the initial configuration dialog?'",
            "inputs": []
        },
        {
            "name": "Set Initial Secret Password",
            "command": [
                "{password}",
                "{password}"
            ],
            "description": "Set and confirm the secret password when prompted by the switch",
            "inputs": [
                {"name": "password", "type": "string", "description": "Secret password for the switch (e.g. Cisco123!)"}
            ]
        },
        {
            "name": "Enter Privileged EXEC Mode",
            "command": [
                "enable",
                "{password}"
            ],
            "description": "Enter privileged EXEC mode with password",
            "inputs": [
                {"name": "password", "type": "string", "description": "Enable password (e.g. Cisco123!)"}
            ]
        },
        {
            "name": "Enter Global Configuration Mode",
            "command": "configure terminal",
            "description": "Enter global configuration mode",
            "inputs": []

        }
    ],
    "Stacking Configuration": [
        {
            "name": "Configure Stack-Mac Persistent",
            "command": [
                "configure terminal",
                "stack-mac persistent timer 0",
                "end"
            ],
            "description": "Ensures faster switchover time",
            "inputs": []
        },
        {
            "name": "Set Switch Priority",
            "command": [
                "configure terminal",
                "switch {switch_number} priority {priority}",
                "end"
            ],
            "description": "Set the priority of a switch in the stack. Higher priority becomes the master.",
            "inputs": [
                {"name": "switch_number", "type": "int", "description": "Switch number (e.g. 1)"},
                {"name": "priority", "type": "int", "description": "Priority value (e.g. 15)"}
            ]
        }
    ],
    "Stackwise Virtual Configuration": [
        {
            "name": "Configure Stackwise Virtual",
            "command": [
                "configure terminal",
                "stackwise-virtual",
                "domain {domain_id}",
                "exit",
                "interface range {interface_range}",
                "stackwise-virtual link 1",
                "end"
            ],
            "description": "Configure Stackwise Virtual between two Cisco 9500 switches",
            "inputs": [
                {"name": "domain_id", "type": "int", "description": "Domain ID (1-255)"},
                {"name": "interface_range", "type": "string", "description": "Interface range (e.g. hu1/0/25, hu1/0/26)"}
            ]
        }
    ],
    "Management IP Configuration": [
        {
            "name": "Configure VLAN Interface IP",
            "command": [
                "configure terminal",
                "interface vlan {vlan_id}",
                "ip address {ip_address} {subnet_mask}",
                "no shutdown",
                "exit",
                "ip default-gateway {gateway_ip}",
                "end"
            ],
            "description": "Configure management IP via VLAN interface",
            "inputs": [
                {"name": "vlan_id", "type": "int", "description": "VLAN ID (e.g. 10)"},
                {"name": "ip_address", "type": "string", "description": "IP address (e.g. 192.168.1.10)"},
                {"name": "subnet_mask", "type": "string", "description": "Subnet mask (e.g. 255.255.255.0)"},
                {"name": "gateway_ip", "type": "string", "description": "Gateway IP (e.g. 192.168.1.1)"}
            ]
        },
        {
            "name": "Configure Management Port IP",
            "command": [
                "configure terminal",
                "interface gigabitethernet 0/0",
                "ip address {ip_address} {subnet_mask}",
                "no shutdown",
                "exit",
                "ip route vrf Mgmt-vrf 0.0.0.0 0.0.0.0 {gateway_ip}",
                "end"
            ],
            "description": "Configure management IP via dedicated management port",
            "inputs": [
                {"name": "ip_address", "type": "string", "description": "IP address (e.g. 192.168.1.10)"},
                {"name": "subnet_mask", "type": "string", "description": "Subnet mask (e.g. 255.255.255.0)"},
                {"name": "gateway_ip", "type": "string", "description": "Gateway IP (e.g. 192.168.1.1)"}
            ]
        }
    ],
    "System Settings": [
        {
            "name": "Configure Hostname",
            "command": [
                "configure terminal",
                "hostname {hostname}",
                "end"
            ],
            "description": "Set the hostname of the switch",
            "inputs": [
                {"name": "hostname", "type": "string", "description": "Hostname for the switch (e.g. SWITCH01)"}
            ]
        },
        {
            "name": "Configure Domain Name",
            "command": [
                "configure terminal",
                "ip domain name {domain_name}",
                "end"
            ],
            "description": "Set the domain name for the switch",
            "inputs": [
                {"name": "domain_name", "type": "string", "description": "Domain name (e.g. example.com)"}
            ]
        },
        {
            "name": "Configure Enable Secret",
            "command": [
                "configure terminal",
                "enable secret level 15 {password}",
                "end"
            ],
            "description": "Set the enable secret password",
            "inputs": [
                {"name": "password", "type": "string", "description": "Secret password (e.g. StrongP@ss123)"}
            ]
        },
        {
            "name": "Configure Console Password",
            "command": [
                "configure terminal",
                "line console 0",
                "password {password}",
                "login",
                "logging synchronous",
                "end"
            ],
            "description": "Configure console port password",
            "inputs": [
                {"name": "password", "type": "string", "description": "Console password (e.g. ConsoleP@ss123)"}
            ]
        }
    ],
    "NTP Configuration": [
        {
            "name": "Configure NTP via VLAN Interface",
            "command": [
                "configure terminal",
                "ntp server {ntp_server} version 2",
                "clock timezone CET 1",
                "clock summer-time CEST recurring last Sun Mar 02:00 last Sun Oct 03:00",
                "service timestamps log datetime localtime",
                "end"
            ],
            "description": "Configure NTP via VLAN interface",
            "inputs": [
                {"name": "ntp_server", "type": "string", "description": "NTP server IP (e.g. 192.168.1.100)"}
            ]
        },
        {
            "name": "Configure NTP via Management Port",
            "command": [
                "configure terminal",
                "ntp server vrf Mgmt-vrf {ntp_server} version 2",
                "clock timezone CET 1",
                "clock summer-time CEST recurring last Sun Mar 02:00 last Sun Oct 03:00",
                "service timestamps log datetime localtime",
                "end"
            ],
            "description": "Configure NTP via management port",
            "inputs": [
                {"name": "ntp_server", "type": "string", "description": "NTP server IP (e.g. 192.168.1.100)"}
            ]
        }
    ],
    "Security Configuration": [
        {
            "name": "Configure SSH",
            "command": [
                "configure terminal",
                "username {username} privilege 15 secret {password}",
                "crypto key generate rsa",
                "2048",
                "ip ssh version 2",
                "ip ssh time-out {timeout}",
                "ip ssh authentication-retries {retries}",
                "end"
            ],
            "description": "Configure SSH for secure access",
            "inputs": [
                {"name": "username", "type": "string", "description": "Admin username (e.g. admin)"},
                {"name": "password", "type": "string", "description": "Admin password (e.g. StrongP@ss123)"},
                {"name": "timeout", "type": "int", "description": "SSH timeout in seconds (e.g. 60)"},
                {"name": "retries", "type": "int", "description": "Authentication retries (e.g. 3)"}
            ]
        },
        {
            "name": "Disable Telnet",
            "command": [
                "configure terminal",
                "line vty 0 15",
                "login local",
                "transport input ssh",
                "end"
            ],
            "description": "Disable Telnet access and only allow SSH",
            "inputs": []
        },
        {
            "name": "Enable Password Encryption",
            "command": [
                "configure terminal",
                "service password-encryption",
                "end"
            ],
            "description": "Encrypt all passwords in the configuration",
            "inputs": []
        },
        {
            "name": "Configure HTTPS and Disable HTTP",
            "command": [
                "configure terminal",
                "ip http secure-server",
                "no ip http server",
                "ip http authentication local",
                "end"
            ],
            "description": "Enable HTTPS and disable HTTP",
            "inputs": []
        }
    ],
    "Network Settings": [
        {
            "name": "Enable UDLD",
            "command": [
                "configure terminal",
                "udld aggressive",
                "end"
            ],
            "description": "Enable Unidirectional Link Detection on fiber ports",
            "inputs": []
        },
        {
            "name": "Increase Log Buffer Size",
            "command": [
                "configure terminal",
                "logging buffered 100000",
                "end"
            ],
            "description": "Increase the buffer size for logging",
            "inputs": []
        },
        {
            "name": "Configure Error-Disable Recovery",
            "command": [
                "configure terminal",
                "errdisable recovery interval 30",
                "errdisable recovery cause all",
                "end"
            ],
            "description": "Enable recovery from error-disable state",
            "inputs": []
        }
    ],
    "SNMP Configuration": [
        {
            "name": "Configure SNMPv2",
            "command": [
                "configure terminal",
                "snmp-server community {community} ro",
                "snmp-server host {snmp_host} version 2c {community}",
                "snmp-server contact {contact}",
                "snmp-server location {location}",
                "end"
            ],
            "description": "Configure SNMPv2 read-only access",
            "inputs": [
                {"name": "community", "type": "string", "description": "SNMP community string (e.g. public-ro)"},
                {"name": "snmp_host", "type": "string", "description": "SNMP server IP (e.g. 192.168.1.200)"},
                {"name": "contact", "type": "string", "description": "Contact information (e.g. admin@example.com)"},
                {"name": "location", "type": "string", "description": "Device location (e.g. Server Room 1)"}
            ]
        },
        {
            "name": "Configure SNMPv3",
            "command": [
                "configure terminal",
                "snmp-server view {view_name} 1 included",
                "snmp-server group {group_name} v3 priv read {view_name}",
                "snmp-server user {username} {group_name} v3 auth sha {auth_password} priv aes 128 {priv_password}",
                "end"
            ],
            "description": "Configure SNMPv3 with authentication and encryption",
            "inputs": [
                {"name": "view_name", "type": "string", "description": "SNMP view name (e.g. ReadView)"},
                {"name": "group_name", "type": "string", "description": "SNMP group name (e.g. ReadGroup)"},
                {"name": "username", "type": "string", "description": "SNMP user (e.g. snmpuser)"},
                {"name": "auth_password", "type": "string", "description": "Authentication password (e.g. AuthP@ss123)"},
                {"name": "priv_password", "type": "string", "description": "Privacy password (e.g. PrivP@ss123)"}
            ]
        },
        {
            "name": "Configure SNMP Traps",
            "command": [
                "configure terminal",
                "snmp-server enable traps snmp linkup linkdown",
                "snmp-server enable traps mac-notification change",
                "snmp-server source-interface traps gigabitethernet 0/0",
                "end"
            ],
            "description": "Enable SNMP traps for link up/down and MAC changes",
            "inputs": []
        }
    ],
    "Syslog Configuration": [
        {
            "name": "Configure Syslog via VLAN Interface",
            "command": [
                "configure terminal",
                "logging host {syslog_server}",
                "end"
            ],
            "description": "Configure syslog server via VLAN interface",
            "inputs": [
                {"name": "syslog_server", "type": "string", "description": "Syslog server IP (e.g. 192.168.1.200)"}
            ]
        },
        {
            "name": "Configure Syslog via Management Port",
            "command": [
                "configure terminal",
                "logging host {syslog_server} vrf Mgmt-vrf",
                "end"
            ],
            "description": "Configure syslog server via management port",
            "inputs": [
                {"name": "syslog_server", "type": "string", "description": "Syslog server IP (e.g. 192.168.1.200)"}
            ]
        }
    ],
    "Disable Unneeded Services": [
        {
            "name": "Disable Unnecessary Services",
            "command": [
                "configure terminal",
                "no ip finger",
                "no service dhcp",
                "no ip domain lookup",
                "no service pad",
                "no service config",
                "no lldp run",
                "ip arp proxy disable",
                "vtp mode transparent",
                "no ip routing",
                "end"
            ],
            "description": "Disable various services not needed for basic switch operation",
            "inputs": []
        }
    ],
    "LACP Configuration": [
        {
            "name": "Configure LACP",
            "command": [
                "configure terminal",
                "interface range {interface_range}",
                "channel-protocol lacp",
                "channel-group {channel_group} mode active",
                "exit",
                "end"
            ],
            "description": "Configure Link Aggregation Control Protocol",
            "inputs": [
                {"name": "interface_range", "type": "string", "description": "Interface range (e.g. Gi1/0/1, Gi1/0/2)"},
                {"name": "channel_group", "type": "int", "description": "Channel group number (e.g. 1)"}
            ]
        }
    ],
    "VLAN Configuration": [
        {
            "name": "Create VLAN",
            "command": [
                "configure terminal",
                "vlan {vlan_id}",
                "name {vlan_name}",
                "end"
            ],
            "description": "Create a new VLAN",
            "inputs": [
                {"name": "vlan_id", "type": "int", "description": "VLAN ID (e.g. 10)"},
                {"name": "vlan_name", "type": "string", "description": "VLAN name (e.g. Data)"}
            ]
        },
        {
            "name": "Configure VLAN Trunk",
            "command": [
                "configure terminal",
                "interface {interface}",
                "description {description}",
                "switchport mode trunk",
                "end"
            ],
            "description": "Configure a port as a VLAN trunk",
            "inputs": [
                {"name": "interface", "type": "string", "description": "Interface name (e.g. GigabitEthernet1/0/1)"},
                {"name": "description", "type": "string", "description": "Port description (e.g. Uplink to Core Switch)"}
            ]
        },
        {
            "name": "Configure Trunk Port to Firewall/VMware",
            "command": [
                "configure terminal",
                "interface {interface}",
                "description {description}",
                "switchport mode trunk",
                "spanning-tree portfast trunk",
                "spanning-tree bpduguard enable",
                "end"
            ],
            "description": "Configure a trunk port to Firewall, SBC, VMware or Hyper-V",
            "inputs": [
                {"name": "interface", "type": "string", "description": "Interface name (e.g. GigabitEthernet1/0/1)"},
                {"name": "description", "type": "string", "description": "Port description (e.g. customer_Firewall)"}
            ]
        },
        {
            "name": "Configure Access Port",
            "command": [
                "configure terminal",
                "interface {interface}",
                "description {description}",
                "switchport mode access",
                "switchport access vlan {vlan_id}",
                "spanning-tree portfast",
                "spanning-tree bpduguard enable",
                "end"
            ],
            "description": "Configure an access port",
            "inputs": [
                {"name": "interface", "type": "string", "description": "Interface name (e.g. GigabitEthernet1/0/1)"},
                {"name": "description", "type": "string", "description": "Port description (e.g. customer_Workstation)"},
                {"name": "vlan_id", "type": "int", "description": "VLAN ID (e.g. 10)"}
            ]
        },
        {
            "name": "Disable Unknown Unicast Flooding",
            "command": [
                "configure terminal",
                "interface {interface}",
                "switchport block unicast",
                "end"
            ],
            "description": "Disable unknown unicast flooding on a port",
            "inputs": [
                {"name": "interface", "type": "string", "description": "Interface name (e.g. GigabitEthernet1/0/1)"}
            ]
        }
    ],
    "Multicast Configuration": [
        {
            "name": "Enable Multicast Querier",
            "command": [
                "configure terminal",
                "ip igmp snooping querier",
                "end"
            ],
            "description": "Enable IGMP snooping querier",
            "inputs": []
        }
    ],
    "Spanning Tree Configuration": [
        {
            "name": "Enable Rapid-PVST",
            "command": [
                "configure terminal",
                "spanning-tree mode rapid-pvst",
                "end"
            ],
            "description": "Enable Rapid-PVST spanning tree mode",
            "inputs": []
        },
        {
            "name": "Configure Root Bridge",
            "command": [
                "configure terminal",
                "spanning-tree vlan {vlan_list} root primary",
                "end"
            ],
            "description": "Set this switch as the root bridge for specific VLANs",
            "inputs": [
                {"name": "vlan_list", "type": "string", "description": "List of VLANs (e.g. 1,10,20)"}
            ]
        },
        {
            "name": "Configure Backup Root Bridge",
            "command": [
                "configure terminal",
                "spanning-tree vlan {vlan_list} root secondary",
                "end"
            ],
            "description": "Set this switch as the backup root bridge for specific VLANs",
            "inputs": [
                {"name": "vlan_list", "type": "string", "description": "List of VLANs (e.g. 1,10,20)"}
            ]
        }
    ],
    "Special Configurations": [
        {
            "name": "Configure TAM Port",
            "command": [
                "configure terminal",
                "interface {interface}",
                "duplex auto",
                "speed 10",
                "end"
            ],
            "description": "Special port configuration for TAM (Time and Alarm Manager)",
            "inputs": [
                {"name": "interface", "type": "string", "description": "Interface name (e.g. GigabitEthernet1/0/1)"}
            ]
        },
        {
            "name": "Disable Unused Ports",
            "command": [
                "configure terminal",
                "interface range {interface_range}",
                "shutdown",
                "end"
            ],
            "description": "Disable unused switch ports",
            "inputs": [
                {"name": "interface_range", "type": "string", "description": "Interface range (e.g. Gi1/0/10-24)"}
            ]
        }
    ],
    "Configuration Archiving": [
        {
            "name": "Configure TFTP Archiving",
            "command": [
                "configure terminal",
                "archive",
                "path tftp://{tftp_server}/$h-",
                "write-memory",
                "exit",
                "end"
            ],
            "description": "Configure automatic archiving to TFTP server",
            "inputs": [
                {"name": "tftp_server", "type": "string", "description": "TFTP server IP (e.g. 192.168.1.200)"}
            ]
        },
        {
            "name": "Configure TFTP Archiving via Management Port",
            "command": [
                "configure terminal",
                "archive",
                "path tftp://{tftp_server}/$h-",
                "write-memory",
                "exit",
                "ip tftp source-interface gigabitethernet 0/0",
                "end"
            ],
            "description": "Configure automatic archiving to TFTP server via management port",
            "inputs": [
                {"name": "tftp_server", "type": "string", "description": "TFTP server IP (e.g. 192.168.1.200)"}
            ]
        },
        {
            "name": "Configure Configuration Change Logging",
            "command": [
                "configure terminal",
                "archive",
                "log config",
                "logging enable",
                "hidekeys",
                "notify syslog",
                "exit",
                "end"
            ],
            "description": "Enable logging of configuration changes",
            "inputs": []
        }
    ],
    "Troubleshooting Commands": [
        {
            "name": "Show Running Config",
            "command": "show running-config",
            "description": "Display the current running configuration",
            "inputs": []
        },
        {
            "name": "Show Version",
            "command": "show version",
            "description": "Display the IOS version",
            "inputs": []
        },
        {
            "name": "Show NTP Status",
            "command": "show ntp status",
            "description": "Display current NTP status",
            "inputs": []
        },
        {
            "name": "Show Logs",
            "command": "show logging",
            "description": "Display log information",
            "inputs": []
        },
        {
            "name": "Show Interface Status",
            "command": "show ip interface brief",
            "description": "Display interface status (up/down)",
            "inputs": []
        },
        {
            "name": "Show Routes",
            "command": "show ip route",
            "description": "Display routing table",
            "inputs": []
        },
        {
            "name": "Show Interface Detailed Status",
            "command": "show interface status",
            "description": "Display detailed interface status (including Errdisable)",
            "inputs": []
        },
        {
            "name": "Show Boot Variables",
            "command": "show boot",
            "description": "Display boot variables",
            "inputs": []
        },
        {
            "name": "Show License Information",
            "command": "show license",
            "description": "Display license information",
            "inputs": []
        },
        {
            "name": "Show SFP Information",
            "command": "show interface transceiver detail",
            "description": "Display information about SFP modules",
            "inputs": []
        },
        {
            "name": "Show IGMP Snooping",
            "command": "show ip igmp snooping",
            "description": "Display IGMP snooping information",
            "inputs": []
        },
        {
            "name": "Show IGMP Querier",
            "command": "show ip igmp snooping querier",
            "description": "Display IGMP querier information",
            "inputs": []
        },
        {
            "name": "Show CPU History",
            "command": "show processes cpu history",
            "description": "Display CPU history",
            "inputs": []
        },
        {
            "name": "Show CPU Processes",
            "command": "show processes cpu",
            "description": "Display CPU processes",
            "inputs": []
        },
        {
            "name": "Show Spanning Tree",
            "command": "show spanning-tree detail",
            "description": "Display detailed spanning tree information",
            "inputs": []
        },
        {
            "name": "Show Environment",
            "command": "show env",
            "description": "Display environment information (fan, power, etc.)",
            "inputs": []
        },
        {
            "name": "Show Switch Virtual",
            "command": "show switch virtual",
            "description": "Display switch virtual information",
            "inputs": []
        },
        {
            "name": "Show Switch Virtual Role",
            "command": "show switch virtual role",
            "description": "Display switch virtual role information",
            "inputs": []
        },
        {
            "name": "Show Switch Virtual Link",
            "command": "show switch virtual link",
            "description": "Display switch virtual link information",
            "inputs": []
        },
        {
            "name": "Show EtherChannel Summary",
            "command": "show etherchannel summary",
            "description": "Display EtherChannel summary",
            "inputs": []
        },
        {
            "name": "Show Port-Channel Switchport",
            "command": "show interfaces port-channel {channel_number} switchport",
            "description": "Display VLAN information for an EtherChannel",
            "inputs": [
                {"name": "channel_number", "type": "int", "description": "Channel number (e.g. 1)"}
            ]
        },
        {
            "name": "Show All Switchports",
            "command": "show interfaces switchport",
            "description": "Display VLAN information for all ports",
            "inputs": []
        },
        {
            "name": "Show All Interface Status",
            "command": "show interfaces status",
            "description": "Display status of all interfaces",
            "inputs": []
        },
        {
            "name": "Show Trunk Interfaces",
            "command": "show interfaces trunk",
            "description": "Display information about trunk interfaces",
            "inputs": []
        },
        {
            "name": "Show Configuration Changes",
            "command": "show archive log config all",
            "description": "Display configuration changes (if logging is active)",
            "inputs": []
        },
        {
            "name": "Show Interface Utilization",
            "command": "show controllers utilization",
            "description": "Display interface bandwidth utilization in percent",
            "inputs": []
        }
    ],
    "Stack Management": [
        {
            "name": "Show Switch Stack Information",
            "command": "show switch",
            "description": "Display information about the switch stack",
            "inputs": []
        },
        {
            "name": "Reload Switch in Stack",
            "command": "reload slot {switch_number}",
            "description": "Reload a specific switch in the stack",
            "inputs": [
                {"name": "switch_number", "type": "int", "description": "Switch number (e.g. 2)"}
            ]
        },
        {
            "name": "Renumber Switch",
            "command": "switch {current_number} renumber {new_number}",
            "description": "Renumber a switch in the stack",
            "inputs": [
                {"name": "current_number", "type": "int", "description": "Current switch number (e.g. 2)"},
                {"name": "new_number", "type": "int", "description": "New switch number (e.g. 3)"}
            ]
        }
    ],
    "SPAN Configuration": [
        {
            "name": "Configure SPAN Port",
            "command": [
                "configure terminal",
                "monitor session {session_id} source interface {source_interface} {direction}",
                "monitor session {session_id} destination interface {destination_interface} encapsulation replicate",
                "end"
            ],
            "description": "Configure a SPAN (Switched Port Analyzer) port",
            "inputs": [
                {"name": "session_id", "type": "int", "description": "Session ID (e.g. 1)"},
                {"name": "source_interface", "type": "string", "description": "Source interface (e.g. Gi1/0/1)"},
                {"name": "direction", "type": "string", "description": "Traffic direction (both, rx, or tx)"},
                {"name": "destination_interface", "type": "string", "description": "Destination interface (e.g. Gi1/0/24)"}
            ]
        }
    ],
    "Reset Commands": [
        {
            "name": "Reset to Factory Default",
            "command": "write erase\nreload",
            "description": "Reset the switch to factory default settings",
            "inputs": []
        },
        {
            "name": "Clear Running Config",
            "command": "write erase\nreload",
            "description": "Clear the running configuration",
            "inputs": []
        },
        {
            "name": "Reset Password",
            "command": "config-register 0x2142\nreload\nenable\ncopy startup-config running-config\nenable secret {new_password}\nconfig-register 0x2102\nwrite memory\nreload",
            "description": "Reset the enable password",
            "inputs": [
                {"name": "new_password", "type": "text", "description": "Enter new enable password"}
            ]
        },
        {
            "name": "Reset Interface",
            "command": [
                "configure terminal",
                "default interface {interface}",
                "end"
            ],
            "description": "Reset a specific interface to default settings",
            "inputs": [
                {"name": "interface", "type": "text", "description": "Enter interface (e.g., GigabitEthernet1/0/1)"}
            ]
        }
    ]
} 