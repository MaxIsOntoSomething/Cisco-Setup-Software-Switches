# Cisco Switch Configurator

A GUI application to automate Cisco switch configuration tasks based on Cisco's configuration guide.

## Features

- Connect to Cisco switches via COM port or SSH
- Step-by-step configuration with clear input examples
- Save and load configuration settings
- Auto-execute mode or manual command execution
- Interactive console with command history
- Comprehensive set of Cisco switch commands organized by category

## Installation

1. Make sure you have Python 3.6+ installed
2. Clone this repository or download the files
3. Install the required dependencies:

```
pip install -r requirements.txt
```

## Usage

1. Run the application:

```
python cisco_switch_configurator.py
```

2. Connect to your switch:
   - For serial connection: Select the COM port and baud rate
   - For SSH connection: Enter the switch IP address, username, and password

3. Navigate to the Configuration tab and select a configuration category

4. Select the configuration item you want to run and fill in the required inputs

5. Click "Run" to execute the commands on the switch

## Connection Types

### Serial (COM Port)
- Select the COM port from the dropdown (refresh button available)
- Set the baud rate (default: 9600)
- Click Connect

### SSH
- Enter the switch's IP address
- Enter your username and password
- Click Connect

## Configuration Options

The configurator includes the following categories of configurations:

- Stacking Configuration
- Stackwise Virtual Configuration
- Management IP Configuration
- System Settings
- NTP Configuration
- Security Configuration
- Network Settings
- SNMP Configuration
- Syslog Configuration
- Disable Unneeded Services
- LACP Configuration
- VLAN Configuration
- Multicast Configuration
- Spanning Tree Configuration
- Special Configurations
- Configuration Archiving
- Troubleshooting Commands
- Stack Management
- SPAN Configuration

## Auto-Execute Mode

Toggle the "Auto-execute commands" checkbox in the Console tab to automatically send commands in sequence. You can adjust the delay between commands.

## Saving and Loading Configurations

- Click "Save Configuration" to save all your input values to a JSON file
- Click "Load Configuration" to load saved values from a file

## Troubleshooting

If you encounter connection issues:
- Verify you have the correct COM port or IP address
- Ensure the baud rate matches your switch's console settings
- Check that you have the proper credentials for SSH
- Try disconnecting and reconnecting

For questions or issues, please refer to the Cisco Switch Configuration Guide. 