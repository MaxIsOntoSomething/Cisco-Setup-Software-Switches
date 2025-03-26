import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import json
import os
import threading
import time
import serial
import paramiko
from serial.tools import list_ports
from config_data import CONFIG_DATA

class CiscoSwitchConfigurator:
    def __init__(self, root):
        self.root = root
        self.root.title("Cisco Switch Configurator")
        self.root.geometry("1000x700")
        
        # Keep track of multiple switch instances
        self.switch_tabs = {}
        self.switch_count = 1
        
        self.connection = None
        self.connection_type = tk.StringVar(value="COM")
        self.com_port = tk.StringVar()
        self.ssh_host = tk.StringVar()
        self.ssh_username = tk.StringVar()
        self.ssh_password = tk.StringVar()
        self.baudrate = tk.IntVar(value=9600)
        
        # Create variables for console options - needed for the first switch
        self.manual_mode = tk.BooleanVar(value=False)
        self.auto_execute = tk.BooleanVar(value=False)
        self.command_delay = tk.DoubleVar(value=0.5)
        
        # Store preview items
        self.preview_items = []
        self.preview_vars = {}
        
        # Create notification label
        self.notification_var = tk.StringVar()
        self.notification_frame = None
        
        # Path to cat GIF
        self.cat_gif_path = "media/cat-work.gif"
        
        self.setup_ui()
        
    def setup_ui(self):
        # Create a frame for additional controls
        control_frame = ttk.Frame(self.root)
        control_frame.pack(fill=tk.X, side=tk.TOP, padx=10, pady=(10, 0))
        
        # Add New Switch Tab button
        ttk.Button(control_frame, text="New Switch Tab", 
                  command=self.create_new_switch_tab).pack(side=tk.RIGHT)
        
        # Create notebook (tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Connection tab
        self.connection_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.connection_frame, text="Connection")
        
        # Configuration tab
        self.config_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.config_frame, text="Configuration")
        
        # Preview tab
        self.preview_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.preview_frame, text="Preview")
        
        # No initial console tab - will be created when connecting
        
        # Setup Connection Tab
        self.setup_connection_tab()
        
        # Setup Configuration Tab
        self.setup_configuration_tab()
        
        # Setup Preview Tab
        self.setup_preview_tab()
        
        # Setup notification area at the bottom
        self.setup_notification_area()

    def create_new_switch_tab(self):
        """Create a new tab for another switch"""
        # Increment switch count
        self.switch_count += 1
        switch_num = self.switch_count
        
        # Create a new console frame for this switch
        new_console_frame = ttk.Frame(self.notebook)
        self.notebook.add(new_console_frame, text=f"Console - Switch {switch_num}")
        
        # Create connection variables for this switch
        switch_connection_type = tk.StringVar(value="COM")
        
        # Store the switch information
        self.switch_tabs[switch_num] = {
            'frame': new_console_frame,
            'connection': None,
            'connection_type': switch_connection_type,
            'console_output': None,
            'console_input': None,
            'ssh_shell': None,
            'queued_commands': [],
            'manual_mode': tk.BooleanVar(value=False),
            'auto_execute': tk.BooleanVar(value=False),
            'command_delay': tk.DoubleVar(value=0.5),
            'name': f"Switch {switch_num}",  # Default name
            'password_var': tk.StringVar()
        }
        
        # Setup the console tab for this switch
        self.setup_console_tab(switch_num)
        
        # Select the new tab
        self.notebook.select(new_console_frame)
        
        # Show connection dialog for the new switch
        self.show_connection_dialog(switch_num)
        
    def show_connection_dialog(self, switch_num):
        """Show a dialog to configure connection for a specific switch"""
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Connect Switch {switch_num}")
        dialog.geometry("400x400")  # Made taller to accommodate the name field
        dialog.transient(self.root)
        dialog.grab_set()
        
        switch_data = self.switch_tabs[switch_num]
        
        # Switch name field
        name_frame = ttk.LabelFrame(dialog, text="Switch Identification")
        name_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(name_frame, text="Switch Name:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        switch_name = tk.StringVar(value=f"Switch {switch_num}")
        name_entry = ttk.Entry(name_frame, textvariable=switch_name, width=30)
        name_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W+tk.E)
        name_entry.select_range(0, tk.END)
        name_entry.focus()
        
        # Connection type
        conn_frame = ttk.LabelFrame(dialog, text="Connection Type")
        conn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Radiobutton(conn_frame, text="COM Port", variable=switch_data['connection_type'],
                       value="COM").grid(row=0, column=0, padx=10, pady=5)
        ttk.Radiobutton(conn_frame, text="SSH", variable=switch_data['connection_type'],
                       value="SSH").grid(row=0, column=1, padx=10, pady=5)
        
        # COM Port settings
        com_frame = ttk.LabelFrame(dialog, text="COM Port Settings")
        com_frame.pack(fill=tk.X, padx=10, pady=10)
        
        com_port = tk.StringVar()
        baudrate = tk.IntVar(value=9600)
        
        ttk.Label(com_frame, text="COM Port:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        com_combo = ttk.Combobox(com_frame, textvariable=com_port)
        com_combo.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Get available COM ports
        ports = [port.device for port in list_ports.comports()]
        com_combo['values'] = ports
        if ports:
            com_port.set(ports[0])
            
        ttk.Label(com_frame, text="Baudrate:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        baudrate_combo = ttk.Combobox(com_frame, textvariable=baudrate,
                                     values=[9600, 19200, 38400, 57600, 115200])
        baudrate_combo.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        # SSH settings
        ssh_frame = ttk.LabelFrame(dialog, text="SSH Settings")
        ssh_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ssh_host = tk.StringVar()
        ssh_username = tk.StringVar()
        ssh_password = tk.StringVar()
        
        ttk.Label(ssh_frame, text="Host:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        ttk.Entry(ssh_frame, textvariable=ssh_host).grid(row=0, column=1, padx=5, pady=5, sticky=tk.W+tk.E)
        
        ttk.Label(ssh_frame, text="Username:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        ttk.Entry(ssh_frame, textvariable=ssh_username).grid(row=1, column=1, padx=5, pady=5, sticky=tk.W+tk.E)
        
        ttk.Label(ssh_frame, text="Password:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        ttk.Entry(ssh_frame, textvariable=ssh_password, show="*").grid(row=2, column=1, padx=5, pady=5, sticky=tk.W+tk.E)
        
        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="Connect", 
                  command=lambda: self.connect_switch_from_dialog(
                      switch_num, switch_name.get(), com_port.get(), baudrate.get(), 
                      ssh_host.get(), ssh_username.get(), ssh_password.get(), dialog
                  )).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(button_frame, text="Cancel", 
                  command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
                  
    def connect_switch_from_dialog(self, switch_num, switch_name, com_port, baudrate, ssh_host, ssh_username, ssh_password, dialog):
        """Connect to a switch using the details from the dialog"""
        switch_data = self.switch_tabs[switch_num]
        
        # Save the switch name
        switch_data['name'] = switch_name
        
        # Update the tab name
        self.notebook.tab(switch_data['frame'], text=f"Console - {switch_name}")
        
        try:
            if switch_data['connection_type'].get() == "COM":
                connection = serial.Serial(
                    port=com_port,
                    baudrate=baudrate,
                    timeout=1
                )
                connection_info = f"Connected to {switch_name} via {com_port} at {baudrate} baud"
                
                # Store the connection
                switch_data['connection'] = connection
                
                # Update console
                console_output = switch_data['console_output']
                console_output.config(state=tk.NORMAL)
                console_output.insert(tk.END, f"{connection_info}\n")
                console_output.see(tk.END)
                console_output.config(state=tk.DISABLED)
                
                # Start a thread to read from serial
                threading.Thread(target=lambda: self.read_from_serial_for_switch(switch_num), 
                                daemon=True).start()
            else:
                # SSH connection
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(
                    hostname=ssh_host,
                    username=ssh_username,
                    password=ssh_password
                )
                ssh_shell = client.invoke_shell()
                connection_info = f"Connected to {switch_name} via SSH ({ssh_host})"
                
                # Store the connection
                switch_data['connection'] = client
                switch_data['ssh_shell'] = ssh_shell
                
                # Update console
                console_output = switch_data['console_output']
                console_output.config(state=tk.NORMAL)
                console_output.insert(tk.END, f"{connection_info}\n")
                console_output.see(tk.END)
                console_output.config(state=tk.DISABLED)
                
                # Start a thread to read from SSH
                threading.Thread(target=lambda: self.read_from_ssh_for_switch(switch_num), 
                                daemon=True).start()
                
            # Switch to console tab after connecting
            if 1 in self.switch_tabs:
                self.notebook.select(self.switch_tabs[1]['frame'])
                
            # Update the switch selector
            self.update_switch_selector()
            
            dialog.destroy()
            
        except Exception as e:
            messagebox.showerror("Connection Error", str(e))

    def setup_console_tab(self, switch_num=1):
        """Set up the console tab for a specific switch"""
        # Get the frame for this switch
        switch_data = self.switch_tabs[switch_num]
        console_frame = switch_data['frame']
        
        # Create frame for content
        main_frame = ttk.Frame(console_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create options frame at the top
        options_frame = ttk.Frame(main_frame)
        options_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Initialize default name for the first switch if not exists
        if switch_num == 1 and 'name' not in switch_data:
            switch_data['name'] = "Switch 1"
            
        # Switch name indicator
        switch_label = ttk.Label(options_frame, text=f"{switch_data['name']}", font=("Arial", 10, "bold"))
        switch_label.pack(side=tk.LEFT, padx=5)
        
        # For the first switch, set manual_mode, auto_execute, and command_delay to the instance variables
        if switch_num == 1:
            switch_data['manual_mode'] = self.manual_mode
            switch_data['auto_execute'] = self.auto_execute
            switch_data['command_delay'] = self.command_delay
        
        # Manual typing mode checkbox
        manual_mode_check = ttk.Checkbutton(
            options_frame, 
            text="Manual Typing Mode",
            variable=switch_data['manual_mode'],
            command=lambda: self.toggle_manual_mode_for_switch(switch_num)
        )
        manual_mode_check.pack(side=tk.LEFT, padx=10)
        
        # Auto execute checkbox
        auto_execute_check = ttk.Checkbutton(
            options_frame,
            text="Auto-execute",
            variable=switch_data['auto_execute']
        )
        auto_execute_check.pack(side=tk.LEFT, padx=10)
        
        # Command delay
        ttk.Label(options_frame, text="Delay (sec):").pack(side=tk.LEFT)
        delay_entry = ttk.Entry(options_frame, textvariable=switch_data['command_delay'], width=5)
        delay_entry.pack(side=tk.LEFT, padx=5)
        
        # Test connection button
        test_conn_button = ttk.Button(
            options_frame,
            text="Test Connection",
            command=lambda: self.test_connection_for_switch(switch_num)
        )
        test_conn_button.pack(side=tk.LEFT, padx=10)
        
        # Close tab button (only for additional tabs, not the first one)
        if switch_num > 1:
            close_button = ttk.Button(
                options_frame,
                text="Close Tab",
                command=lambda: self.close_switch_tab(switch_num)
            )
            close_button.pack(side=tk.LEFT, padx=10)
        
        # Clear console button
        clear_button = ttk.Button(
            options_frame,
            text="Clear Console",
            command=lambda: self.clear_console_for_switch(switch_num)
        )
        clear_button.pack(side=tk.RIGHT)
        
        # Console output
        console_output = scrolledtext.ScrolledText(
            main_frame, wrap=tk.WORD, bg="black", fg="green", height=20
        )
        console_output.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        console_output.tag_configure("device", foreground="#00CCCC")  # Light cyan for device responses
        console_output.config(state=tk.DISABLED)
        console_output.configure(font=("Courier New", 10))
        
        # Store the console output reference
        switch_data['console_output'] = console_output
        
        # Login frame for quick authentication
        login_frame = ttk.Frame(main_frame)
        login_frame.pack(fill=tk.X, padx=5, pady=(5, 0))
        
        ttk.Label(login_frame, text="Password:").pack(side=tk.LEFT, padx=5)
        
        # Create a password field
        password_var = tk.StringVar()
        password_entry = ttk.Entry(login_frame, textvariable=password_var, show="*", width=20)
        password_entry.pack(side=tk.LEFT, padx=5)
        
        # Store the password variable
        switch_data['password_var'] = password_var
        
        # Login button
        login_button = ttk.Button(
            login_frame, 
            text="Login",
            command=lambda: self.send_login_password(switch_num)
        )
        login_button.pack(side=tk.LEFT, padx=5)
        
        # Command input frame
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(input_frame, text="Command:").pack(side=tk.LEFT, padx=5)
        
        console_input = ttk.Entry(input_frame)
        console_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # For first switch, use the main send_command method
        if switch_num == 1:
            console_input.bind("<Return>", self.send_command)
            send_button = ttk.Button(input_frame, text="Send", command=self.send_command)
        else:
            console_input.bind("<Return>", lambda e, sn=switch_num: self.send_command_for_switch(e, sn))
            send_button = ttk.Button(input_frame, text="Send", 
                          command=lambda sn=switch_num: self.send_command_for_switch(None, sn))
        
        send_button.pack(side=tk.RIGHT, padx=5)
        
        # Store the console input reference
        switch_data['console_input'] = console_input
        
        # Welcome message
        if switch_num == 1:
            # For the first tab, we want to match the existing state
            self.log_to_console_for_switch(1, "Console ready. Connect to a device to begin.\n")
        else:
            # For additional tabs, we'll use our new method
            self.log_to_console_for_switch(switch_num, "Console ready. Connect to a device to begin.\n")
            
    def send_login_password(self, switch_num):
        """Send the password from the password field to the device"""
        if switch_num not in self.switch_tabs:
            return
            
        switch_data = self.switch_tabs[switch_num]
        
        if not switch_data['connection']:
            messagebox.showwarning("Not Connected", "Please connect to a device first")
            return
            
        # Get the password
        password = switch_data['password_var'].get()
        if not password:
            messagebox.showinfo("Login", "Please enter a password first")
            return
            
        # Log that we're sending a login (but don't show the password)
        self.log_to_console_for_switch(switch_num, "\n> [Sending login credentials...]\n")
        
        # Send the password
        try:
            if switch_data['connection_type'].get() == "COM":
                switch_data['connection'].write((password + "\r\n").encode())
                switch_data['connection'].flush()
            else:
                switch_data['ssh_shell'].send(password + "\n")
                
            # Clear the password field
            switch_data['password_var'].set("")
            
        except Exception as e:
            messagebox.showerror("Login Error", str(e))
            
    def close_switch_tab(self, switch_num):
        """Close a switch tab and cleanup its resources"""
        if switch_num == 1:
            messagebox.showinfo("Information", "Cannot close the first switch tab.")
            return
            
        switch_data = self.switch_tabs[switch_num]
        
        # Disconnect if connected
        if switch_data['connection']:
            try:
                if switch_data['connection_type'].get() == "COM":
                    switch_data['connection'].close()
                else:
                    switch_data['connection'].close()
            except:
                pass
        
        # Remove the tab
        self.notebook.forget(switch_data['frame'])
        
        # Remove from the dictionary
        del self.switch_tabs[switch_num]
        
        # Update the switch selector
        self.update_switch_selector()
        
    def read_from_serial_for_switch(self, switch_num):
        """Read data from serial port for a specific switch"""
        switch_data = self.switch_tabs[switch_num]
        connection = switch_data['connection']
        
        while connection and hasattr(connection, 'is_open') and connection.is_open:
            try:
                # Wait a bit for data to arrive
                time.sleep(0.2)
                
                if connection.in_waiting:
                    data = connection.read(connection.in_waiting).decode('utf-8', errors='replace')
                    if data:
                        self.log_to_console_for_switch(switch_num, data, from_device=True)
            except Exception as e:
                self.log_to_console_for_switch(switch_num, f"Error reading from serial: {e}\n")
                break
            time.sleep(0.1)
            
    def read_from_ssh_for_switch(self, switch_num):
        """Read data from SSH connection for a specific switch"""
        switch_data = self.switch_tabs[switch_num]
        connection = switch_data['connection']
        ssh_shell = switch_data['ssh_shell']
        
        while connection and ssh_shell:
            try:
                # Wait a bit for data to arrive
                time.sleep(0.2)
                
                if ssh_shell.recv_ready():
                    data = ssh_shell.recv(4096).decode('utf-8', errors='replace')
                    if data:
                        self.log_to_console_for_switch(switch_num, data, from_device=True)
            except Exception as e:
                self.log_to_console_for_switch(switch_num, f"Error reading from SSH: {e}\n")
                break
            time.sleep(0.1)
            
    def log_to_console_for_switch(self, switch_num, text, from_device=False):
        """Log text to the console for a specific switch"""
        if switch_num not in self.switch_tabs:
            return
            
        switch_data = self.switch_tabs[switch_num]
        console_output = switch_data['console_output']
        
        if console_output:
            console_output.config(state=tk.NORMAL)
            
            # Apply different formatting based on source
            if from_device:
                # Device responses in light cyan
                console_output.tag_config("device", foreground="#00CCCC")
                console_output.insert(tk.END, text, "device")
            else:
                # Our commands and messages in green
                console_output.insert(tk.END, text)
                
            console_output.see(tk.END)
            console_output.config(state=tk.DISABLED)
            
    def send_command_for_switch(self, event=None, switch_num=1):
        """Send a command to a specific switch"""
        if switch_num not in self.switch_tabs:
            return
            
        switch_data = self.switch_tabs[switch_num]
        connection = switch_data['connection']
        console_input = switch_data['console_input']
        
        if not connection:
            messagebox.showwarning("Not Connected", "Please connect to a switch first")
            return
            
        command = console_input.get()
        if not command:
            return
            
        # Log the command to the console
        self.log_to_console_for_switch(switch_num, f"\n> {command}\n")
        
        # Send the command
        try:
            if switch_data['connection_type'].get() == "COM":
                connection.write((command + "\r\n").encode())
                # Flush the buffer
                connection.flush()
            else:
                switch_data['ssh_shell'].send(command + "\n")
                
            # Clear the input field
            console_input.delete(0, tk.END)
            
            # If manual mode is enabled, don't process queued commands
            if switch_data['manual_mode'].get():
                # If we're in manual mode, clear all queued commands to avoid repeating them
                if hasattr(self, 'queued_commands'):
                    self.queued_commands = []
                return
                
            # If we're executing commands from the preview, check the next one
            if hasattr(self, 'queued_commands') and self.queued_commands:
                # Remove the current command from the queue if it matches
                if self.queued_commands and self.queued_commands[0] == command:
                    self.queued_commands.pop(0)
                
                # If auto-execute, queue the next one
                if self.auto_execute.get() and self.queued_commands:
                    self.root.after(int(self.command_delay.get() * 1000), self.execute_next_command_for_switch)
                # Otherwise load the next one for manual execution
                elif self.queued_commands:
                    console_input.delete(0, tk.END)
                    console_input.insert(0, self.queued_commands[0])
                    self.log_to_console_for_switch(switch_num, "Ready for next command. Press Enter or click Send to continue.\n")
                
        except Exception as e:
            messagebox.showerror("Command Error", str(e))
            
    def check_for_next_command_for_switch(self, last_command, switch_num=1):
        """Check if we should proceed to the next command for a specific switch"""
        if switch_num not in self.switch_tabs:
            return
            
        switch_data = self.switch_tabs[switch_num]
        manual_mode = switch_data['manual_mode']
        auto_execute = switch_data['auto_execute']
        console_input = switch_data['console_input']
        
        # Initialize queued_commands if not present
        if 'queued_commands' not in switch_data:
            switch_data['queued_commands'] = []
        queued_commands = switch_data['queued_commands']
        
        # Don't process queued commands if in manual mode
        if manual_mode.get():
            return
            
        if queued_commands and len(queued_commands) > 0 and not auto_execute.get():
            # Remove the current command from the queue if it matches
            if queued_commands and queued_commands[0] == last_command:
                queued_commands.pop(0)
            
            # Wait a short time before loading the next command
            if queued_commands:
                console_input.delete(0, tk.END)
                console_input.insert(0, queued_commands[0])
                self.log_to_console_for_switch(switch_num, "Ready for next command. Press Enter or click Send to continue.\n")
            else:
                # All commands executed, check if we have pending executed items
                if 'executed_preview_items' in switch_data and switch_data['executed_preview_items']:
                    for item_id in switch_data['executed_preview_items']:
                        self.mark_item_executed(item_id)
                    switch_data['executed_preview_items'] = []
                    
                self.log_to_console_for_switch(switch_num, "All commands executed.\n")
                # Show cat GIF when all commands are executed
                self.show_cat_gif()
                
    def toggle_manual_mode_for_switch(self, switch_num=1):
        """Toggle manual mode for a specific switch"""
        if switch_num not in self.switch_tabs:
            return
            
        switch_data = self.switch_tabs[switch_num]
        manual_mode = switch_data['manual_mode']
        console_input = switch_data['console_input']
        
        if manual_mode.get():
            # In manual mode, clear queued commands for both the switch and main application
            switch_data['queued_commands'] = []
            
            # Also clear the main application's queued commands if this is the main switch
            if switch_num == 1 and hasattr(self, 'queued_commands'):
                self.queued_commands = []
                
            console_input.focus_set()
            console_input.delete(0, tk.END)
            self.log_to_console_for_switch(switch_num, "Manual typing mode enabled. Type commands directly.\n")
        else:
            self.log_to_console_for_switch(switch_num, "Manual typing mode disabled. Using command queue.\n")
            
    def clear_console_for_switch(self, switch_num=1):
        """Clear the console for a specific switch"""
        if switch_num not in self.switch_tabs:
            return
            
        switch_data = self.switch_tabs[switch_num]
        console_output = switch_data['console_output']
        
        console_output.config(state=tk.NORMAL)
        console_output.delete(1.0, tk.END)
        console_output.config(state=tk.DISABLED)
        
    def test_connection_for_switch(self, switch_num=1):
        """Test the connection for a specific switch"""
        if switch_num not in self.switch_tabs:
            return
            
        switch_data = self.switch_tabs[switch_num]
        connection = switch_data['connection']
        
        if not connection:
            messagebox.showwarning("Not Connected", "Please connect to a switch first")
            return
            
        self.log_to_console_for_switch(switch_num, "\n--- Testing connection ---\n")
        
        try:
            # Send a test command based on connection type
            if switch_data['connection_type'].get() == "COM":
                # Reset buffers
                connection.reset_input_buffer()
                connection.reset_output_buffer()
                
                # Send a return
                connection.write("\r\n".encode())
                connection.flush()
                time.sleep(0.5)
                
                # Check for response
                if connection.in_waiting:
                    data = connection.read(connection.in_waiting).decode('utf-8', errors='replace')
                    if data:
                        self.log_to_console_for_switch(switch_num, data, from_device=True)
                        self.log_to_console_for_switch(switch_num, "\n--- Connection test successful! ---\n")
                        return
            else:
                # Send a return via SSH
                ssh_shell = switch_data['ssh_shell']
                ssh_shell.send("\n")
                time.sleep(0.5)
                
                # Check for response
                if ssh_shell.recv_ready():
                    data = ssh_shell.recv(4096).decode('utf-8', errors='replace')
                    if data:
                        self.log_to_console_for_switch(switch_num, data, from_device=True)
                        self.log_to_console_for_switch(switch_num, "\n--- Connection test successful! ---\n")
                        return
            
            # If we get here, no response was received
            self.log_to_console_for_switch(switch_num, "\n--- No response from device. Trying more explicit command... ---\n")
            
            # Try a more explicit command
            if switch_data['connection_type'].get() == "COM":
                connection.write("show version\r\n".encode())
                connection.flush()
            else:
                ssh_shell = switch_data['ssh_shell']
                ssh_shell.send("show version\n")
                
        except Exception as e:
            self.log_to_console_for_switch(switch_num, f"\n--- Connection test failed: {e} ---\n")
            
    def show_cat_gif(self):
        """Show a cat GIF animation when all commands complete"""
        try:
            # Check if the file exists
            if not os.path.exists(self.cat_gif_path):
                # Ensure the path exists
                os.makedirs(os.path.dirname(self.cat_gif_path), exist_ok=True)
                self.log_to_console(f"Cat GIF not found at {self.cat_gif_path}. Create this file to see the celebration!\n")
                return
                
            # Create a toplevel window for the GIF
            gif_window = tk.Toplevel(self.root)
            gif_window.title("All Commands Complete!")
            gif_window.geometry("400x350")
            gif_window.transient(self.root)
            
            # Try to load the GIF with PIL
            try:
                from PIL import Image, ImageTk
                
                # Create frames to hold the image and message
                img_frame = ttk.Frame(gif_window)
                img_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
                
                # Create a label for the message
                message_label = ttk.Label(img_frame, text="All commands have been executed successfully!", 
                                         font=("Arial", 12, "bold"))
                message_label.pack(pady=10)
                
                # Create a label for the GIF
                gif_label = ttk.Label(img_frame)
                gif_label.pack(pady=10)
                
                # Function to animate the GIF
                frames = []
                
                def animate_gif(index=0):
                    try:
                        if not frames:  # Load all frames first time
                            gif = Image.open(self.cat_gif_path)
                            for i in range(100):  # Limit to 100 frames max
                                try:
                                    gif.seek(i)
                                    frames.append(ImageTk.PhotoImage(gif.copy()))
                                except EOFError:
                                    break
                                    
                        if frames:
                            frame_index = index % len(frames)
                            gif_label.configure(image=frames[frame_index])
                            gif_window.after(100, animate_gif, frame_index + 1)
                            
                    except Exception as e:
                        ttk.Label(img_frame, text=f"Error loading animation: {e}").pack()
                
                # Start animation
                animate_gif()
                
                # Add a close button
                ttk.Button(gif_window, text="Close", command=gif_window.destroy).pack(pady=10)
                
            except ImportError:
                # If PIL is not available
                ttk.Label(gif_window, text="All commands have been executed successfully!", 
                         font=("Arial", 14, "bold")).pack(pady=20)
                ttk.Label(gif_window, text="(PIL/Pillow library is required to display the cat animation)").pack()
                ttk.Button(gif_window, text="Close", command=gif_window.destroy).pack(pady=20)
                
        except Exception as e:
            self.log_to_console(f"Error displaying completion animation: {e}\n")

    def setup_connection_tab(self):
        # Connection type
        connection_type_frame = ttk.LabelFrame(self.connection_frame, text="Connection Type")
        connection_type_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Radiobutton(connection_type_frame, text="COM Port", variable=self.connection_type, 
                       value="COM", command=self.toggle_connection_fields).grid(row=0, column=0, padx=10, pady=5)
        ttk.Radiobutton(connection_type_frame, text="SSH", variable=self.connection_type, 
                       value="SSH", command=self.toggle_connection_fields).grid(row=0, column=1, padx=10, pady=5)
        
        # COM settings
        self.com_frame = ttk.LabelFrame(self.connection_frame, text="COM Port Settings")
        self.com_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(self.com_frame, text="COM Port:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.com_port_combo = ttk.Combobox(self.com_frame, textvariable=self.com_port)
        self.com_port_combo.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        ttk.Button(self.com_frame, text="Refresh", command=self.refresh_com_ports).grid(row=0, column=2, padx=5, pady=5)
        
        ttk.Label(self.com_frame, text="Baudrate:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        baudrate_combo = ttk.Combobox(self.com_frame, textvariable=self.baudrate, 
                                      values=[9600, 19200, 38400, 57600, 115200])
        baudrate_combo.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        # SSH settings
        self.ssh_frame = ttk.LabelFrame(self.connection_frame, text="SSH Settings")
        self.ssh_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(self.ssh_frame, text="Host:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        ttk.Entry(self.ssh_frame, textvariable=self.ssh_host).grid(row=0, column=1, padx=5, pady=5, sticky=tk.W+tk.E)
        
        ttk.Label(self.ssh_frame, text="Username:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        ttk.Entry(self.ssh_frame, textvariable=self.ssh_username).grid(row=1, column=1, padx=5, pady=5, sticky=tk.W+tk.E)
        
        ttk.Label(self.ssh_frame, text="Password:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        password_entry = ttk.Entry(self.ssh_frame, textvariable=self.ssh_password, show="*")
        password_entry.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W+tk.E)
        
        # Connection buttons
        button_frame = ttk.Frame(self.connection_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="Connect", command=self.connect).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Disconnect", command=self.disconnect).pack(side=tk.LEFT, padx=5)
        
        # Initialize
        self.refresh_com_ports()
        self.toggle_connection_fields()
        
    def toggle_connection_fields(self):
        """Toggle visibility of connection fields based on connection type"""
        if self.connection_type.get() == "COM":
            self.com_frame.pack(fill=tk.X, padx=10, pady=10)
            self.ssh_frame.pack_forget()
        else:  # SSH
            self.com_frame.pack_forget()
            self.ssh_frame.pack(fill=tk.X, padx=10, pady=10)
            
    def refresh_com_ports(self):
        """Refresh the available COM ports"""
        ports = [port.device for port in list_ports.comports()]
        self.com_port_combo['values'] = ports
        if ports and not self.com_port.get():
            self.com_port.set(ports[0])
            
    def connect(self):
        """Connect to the switch via COM port or SSH"""
        try:
            # Get a switch name from the user
            switch_name = self.get_switch_name_dialog()
            if not switch_name:  # If user canceled dialog
                return
                
            if self.connection_type.get() == "COM":
                connection = serial.Serial(
                    port=self.com_port.get(),
                    baudrate=self.baudrate.get(),
                    timeout=1
                )
                connection_info = f"Connected to {switch_name} via {self.com_port.get()} at {self.baudrate.get()} baud"
                
                # Create the first switch tab if it doesn't exist
                if 1 not in self.switch_tabs:
                    # Create console tab
                    console_frame = ttk.Frame(self.notebook)
                    self.notebook.add(console_frame, text=f"Console - {switch_name}")
                    
                    # Store the first switch tab information
                    self.switch_tabs[1] = {
                        'frame': console_frame,
                        'connection': connection,
                        'connection_type': self.connection_type,
                        'console_output': None,
                        'console_input': None,
                        'ssh_shell': None,
                        'queued_commands': [],
                        'manual_mode': self.manual_mode,
                        'auto_execute': self.auto_execute,
                        'command_delay': self.command_delay,
                        'name': switch_name,
                        'password_var': tk.StringVar()
                    }
                    
                    # Setup Console Tab for the first switch
                    self.setup_console_tab(1)
                else:
                    # Update existing switch tab
                    self.switch_tabs[1]['connection'] = connection
                    self.switch_tabs[1]['name'] = switch_name
                    self.notebook.tab(self.switch_tabs[1]['frame'], text=f"Console - {switch_name}")
                
                # Store the main connection (ensure synchronized state)
                self.connection = connection
                
                # Log connection info
                self.log_to_console(f"{connection_info}\n")
                
                # Update connection status
                self.update_connection_status(True, f"COM: {self.com_port.get()} @ {self.baudrate.get()} baud")
                
                # Start a thread to read from the serial port
                threading.Thread(target=self.read_from_serial, daemon=True).start()
            else:
                # SSH connection
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(
                    hostname=self.ssh_host.get(),
                    username=self.ssh_username.get(),
                    password=self.ssh_password.get()
                )
                ssh_shell = client.invoke_shell()
                connection_info = f"Connected to {switch_name} via SSH ({self.ssh_host.get()})"
                
                # Create the first switch tab if it doesn't exist
                if 1 not in self.switch_tabs:
                    # Create console tab
                    console_frame = ttk.Frame(self.notebook)
                    self.notebook.add(console_frame, text=f"Console - {switch_name}")
                    
                    # Store the first switch tab information
                    self.switch_tabs[1] = {
                        'frame': console_frame,
                        'connection': client,
                        'connection_type': self.connection_type,
                        'console_output': None,
                        'console_input': None,
                        'ssh_shell': ssh_shell,
                        'queued_commands': [],
                        'manual_mode': self.manual_mode,
                        'auto_execute': self.auto_execute,
                        'command_delay': self.command_delay,
                        'name': switch_name,
                        'password_var': tk.StringVar()
                    }
                    
                    # Setup Console Tab for the first switch
                    self.setup_console_tab(1)
                else:
                    # Update existing switch tab
                    self.switch_tabs[1]['connection'] = client
                    self.switch_tabs[1]['ssh_shell'] = ssh_shell
                    self.switch_tabs[1]['name'] = switch_name
                    self.notebook.tab(self.switch_tabs[1]['frame'], text=f"Console - {switch_name}")
                
                # Store the main connection (ensure synchronized state)
                self.connection = client
                self.ssh_shell = ssh_shell
                
                # Log connection info
                self.log_to_console(f"{connection_info}\n")
                
                # Update connection status
                self.update_connection_status(True, f"SSH: {self.ssh_username.get()}@{self.ssh_host.get()}")
                
                # Start a thread to read from SSH
                threading.Thread(target=self.read_from_ssh, daemon=True).start()
                
            # Switch to console tab after connecting
            if 1 in self.switch_tabs:
                self.notebook.select(self.switch_tabs[1]['frame'])
                
            # Update the switch selector
            self.update_switch_selector()
                
        except Exception as e:
            messagebox.showerror("Connection Error", str(e))
            self.update_connection_status(False)
            
    def get_switch_name_dialog(self):
        """Show a dialog to get the switch name"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Switch Name")
        dialog.geometry("300x150")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Enter a name for this switch:").pack(pady=(20, 10), padx=20)
        
        switch_name = tk.StringVar(value="Switch 1")
        name_entry = ttk.Entry(dialog, textvariable=switch_name, width=30)
        name_entry.pack(padx=20, pady=5)
        name_entry.select_range(0, tk.END)  # Select all text for easy replacement
        name_entry.focus()
        
        # Variables to store the result
        result = {'name': None}
        
        def on_ok():
            result['name'] = switch_name.get()
            dialog.destroy()
            
        def on_cancel():
            dialog.destroy()
            
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=20, pady=20)
        
        ttk.Button(button_frame, text="OK", command=on_ok).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=on_cancel).pack(side=tk.RIGHT, padx=5)
        
        # Make Enter key press the OK button
        dialog.bind("<Return>", lambda e: on_ok())
        
        # Wait for the dialog to be closed
        self.root.wait_window(dialog)
        
        return result['name']
        
    def disconnect(self):
        """Disconnect from the switch"""
        if self.connection:
            try:
                if self.connection_type.get() == "COM":
                    self.connection.close()
                else:
                    self.connection.close()
                    
                # Also update the switch_tabs connection
                if 1 in self.switch_tabs:
                    self.switch_tabs[1]['connection'] = None
                    if self.connection_type.get() == "SSH":
                        self.switch_tabs[1]['ssh_shell'] = None
                
                self.connection = None
                self.log_to_console("Disconnected from switch\n")
                
                # Update connection status
                self.update_connection_status(False)
                
                # Update the switch selector
                self.update_switch_selector()
                
            except Exception as e:
                messagebox.showerror("Disconnection Error", str(e))
                
    def read_from_serial(self):
        """Read data from the serial port"""
        while self.connection and self.connection.is_open:
            try:
                # Wait a bit for data to arrive (especially after sending command)
                time.sleep(0.2)
                
                if self.connection.in_waiting:
                    data = self.connection.read(self.connection.in_waiting).decode('utf-8', errors='replace')
                    if data:
                        self.log_to_console(data, from_device=True)
            except Exception as e:
                self.log_to_console(f"Error reading from serial: {e}\n")
                break
            time.sleep(0.1)
            
    def read_from_ssh(self):
        """Read data from the SSH connection"""
        while self.connection:
            try:
                # Wait a bit for data to arrive (especially after sending command)
                time.sleep(0.2)
                
                if self.ssh_shell.recv_ready():
                    data = self.ssh_shell.recv(4096).decode('utf-8', errors='replace')
                    if data:
                        self.log_to_console(data, from_device=True)
            except Exception as e:
                self.log_to_console(f"Error reading from SSH: {e}\n")
                break
            time.sleep(0.1)
            
    def update_connection_status(self, is_connected, connection_details=None):
        """Update the connection status displayed in the Preview tab"""
        if hasattr(self, 'connection_status_label'):
            if is_connected and connection_details:
                self.connection_status_label.config(
                    text=f"Connected to: {connection_details}",
                    foreground="green"
                )
            else:
                self.connection_status_label.config(
                    text="Not connected",
                    foreground="red"
                )
                
    def log_to_console(self, text, from_device=False):
        """Log text to the console output for the main switch"""
        # Forward to the switch-specific method for switch 1
        self.log_to_console_for_switch(1, text, from_device)

    def setup_configuration_tab(self):
        # Left side - configuration categories
        config_paned = ttk.PanedWindow(self.config_frame, orient=tk.HORIZONTAL)
        config_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        left_frame = ttk.Frame(config_paned, width=200)
        right_frame = ttk.Frame(config_paned)
        
        config_paned.add(left_frame, weight=1)
        config_paned.add(right_frame, weight=3)
        
        # Category listbox
        ttk.Label(left_frame, text="Configuration Categories").pack(pady=(0, 5))
        self.category_listbox = tk.Listbox(left_frame)
        self.category_listbox.pack(fill=tk.BOTH, expand=True)
        self.category_listbox.bind('<<ListboxSelect>>', self.on_category_select)
        
        # Configuration item details
        self.config_detail_frame = ttk.LabelFrame(right_frame, text="Configuration Details")
        self.config_detail_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Buttons for saving/loading configurations
        button_frame = ttk.Frame(self.config_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="Save Configuration", command=self.save_configuration).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Load Configuration", command=self.load_configuration).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Run Selected", command=self.execute_selected_preview_items).pack(side=tk.RIGHT, padx=5)
        
        # Populate categories from CONFIG_DATA
        self.populate_categories()
        
    def setup_preview_tab(self):
        """Setup the preview tab with a list of commands to execute"""
        # Create a frame with scrollbar for preview items
        preview_container = ttk.Frame(self.preview_frame)
        preview_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Connection status and switch selector at the top
        status_frame = ttk.Frame(preview_container)
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Connection status
        self.connection_status_frame = ttk.LabelFrame(status_frame, text="Connection Status")
        self.connection_status_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        self.connection_status_label = ttk.Label(self.connection_status_frame, 
                                               text="Not connected",
                                               foreground="red",
                                               font=("Arial", 10, "bold"))
        self.connection_status_label.pack(pady=5, padx=10)
        
        # Switch selector
        self.switch_selector_frame = ttk.LabelFrame(status_frame, text="Target Switch")
        self.switch_selector_frame.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5, 0))
        
        # Variable to store the selected switch
        self.selected_switch = tk.IntVar(value=1)  # Default to first switch
        
        # Create radio buttons for switch selection (initially only shows one switch)
        self.switch_radios_frame = ttk.Frame(self.switch_selector_frame)
        self.switch_radios_frame.pack(fill=tk.X, pady=5, padx=10)
        
        # Top section - instructions and buttons
        top_frame = ttk.Frame(preview_container)
        top_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(top_frame, text="Select configurations to execute:").pack(side=tk.LEFT, padx=5)
        
        # Buttons
        ttk.Button(top_frame, text="Execute Selected", 
                  command=self.execute_selected_preview_items).pack(side=tk.RIGHT, padx=5)
        ttk.Button(top_frame, text="Clear All", 
                  command=self.clear_preview_items).pack(side=tk.RIGHT, padx=5)
        
        # Create a canvas with scrollbar for preview items
        canvas_frame = ttk.Frame(preview_container)
        canvas_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.preview_canvas = tk.Canvas(canvas_frame)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.preview_canvas.yview)
        self.preview_scrollable_frame = ttk.Frame(self.preview_canvas)
        
        self.preview_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.preview_canvas.configure(scrollregion=self.preview_canvas.bbox("all"))
        )
        
        self.preview_canvas.create_window((0, 0), window=self.preview_scrollable_frame, anchor="nw")
        self.preview_canvas.configure(yscrollcommand=scrollbar.set)
        
        self.preview_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Add a label when no items
        self.empty_preview_label = ttk.Label(self.preview_scrollable_frame, 
                                           text="No configurations added to preview.\nAdd configurations from the Configuration tab.")
        self.empty_preview_label.pack(pady=20)
        
        # Update the switch selector
        self.update_switch_selector()
        
    def update_switch_selector(self):
        """Update the switch selector with connected switches"""
        # Clear previous radio buttons
        for widget in self.switch_radios_frame.winfo_children():
            widget.destroy()
            
        # Add radio buttons for each connected switch
        connected_switches = []
        for switch_num, switch_data in self.switch_tabs.items():
            if switch_data.get('connection'):
                connected_switches.append(switch_num)
                switch_name = switch_data.get('name', f"Switch {switch_num}")
                ttk.Radiobutton(
                    self.switch_radios_frame,
                    text=switch_name,
                    variable=self.selected_switch,
                    value=switch_num
                ).pack(side=tk.LEFT, padx=5)
        
        # If no connected switches, show a message
        if not connected_switches:
            ttk.Label(self.switch_radios_frame, 
                     text="No connected switches",
                     foreground="red").pack(pady=5)
        # If the currently selected switch is not connected, select the first connected one
        elif self.selected_switch.get() not in connected_switches and connected_switches:
            self.selected_switch.set(connected_switches[0])
    
    def setup_notification_area(self):
        """Create a notification area at the bottom of the window"""
        self.notification_frame = ttk.Frame(self.root)
        self.notification_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=5)
        self.notification_frame.pack_forget()  # Hide it initially
        
        self.notification_label = ttk.Label(
            self.notification_frame, 
            textvariable=self.notification_var,
            background="#e6ffe6",  # Light green background
            foreground="#006400",  # Dark green text
            font=("Arial", 10),
            padding=10
        )
        self.notification_label.pack(side=tk.RIGHT, padx=10, pady=5)
        
    def show_notification(self, message, duration=3000):
        """Show a notification message at the bottom of the window for a limited time"""
        self.notification_var.set(message)
        self.notification_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=5)
        
        # Schedule to hide the notification after duration
        self.root.after(duration, self.hide_notification)
        
    def hide_notification(self):
        """Hide the notification area"""
        self.notification_frame.pack_forget()
        
    def populate_categories(self):
        """Populate the category listbox with categories from CONFIG_DATA"""
        for category in CONFIG_DATA.keys():
            self.category_listbox.insert(tk.END, category)
            
    def on_category_select(self, event):
        """Handle category selection"""
        selection = self.category_listbox.curselection()
        if not selection:
            return
            
        # Clear the current detail frame
        for widget in self.config_detail_frame.winfo_children():
            widget.destroy()
            
        # Get selected category
        category = self.category_listbox.get(selection[0])
        
        # Display config items for the selected category
        if category in CONFIG_DATA:
            # Create a canvas with scrollbar for many config items
            canvas = tk.Canvas(self.config_detail_frame)
            scrollbar = ttk.Scrollbar(self.config_detail_frame, orient="vertical", command=canvas.yview)
            scrollable_frame = ttk.Frame(canvas)
            
            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            for i, item in enumerate(CONFIG_DATA[category]):
                frame = ttk.LabelFrame(scrollable_frame, text=item["name"])
                frame.pack(fill=tk.X, expand=True, padx=5, pady=5)
                
                ttk.Label(frame, text=item["description"], wraplength=500).pack(padx=5, pady=5)
                
                # Show the command(s) that will be executed
                command_frame = ttk.LabelFrame(frame, text="Command(s)")
                command_frame.pack(fill=tk.X, padx=5, pady=5)
                
                if isinstance(item["command"], list):
                    command_text = "\n".join(item["command"])
                else:
                    command_text = item["command"]
                    
                ttk.Label(command_frame, text=command_text, wraplength=500, justify=tk.LEFT).pack(padx=5, pady=5, anchor=tk.W)
                
                # Create input fields for this config item
                if item.get("inputs"):
                    inputs_frame = ttk.LabelFrame(frame, text="Inputs")
                    inputs_frame.pack(fill=tk.X, padx=5, pady=5)
                    
                    item_vars = {}
                    for input_field in item.get("inputs", []):
                        input_frame = ttk.Frame(inputs_frame)
                        input_frame.pack(fill=tk.X, padx=5, pady=2)
                        
                        ttk.Label(input_frame, text=f"{input_field['description']}:").pack(side=tk.LEFT, padx=5)
                        
                        if input_field['type'] == 'int':
                            var = tk.StringVar()  # Use StringVar for validation
                        else:
                            var = tk.StringVar()
                            
                        ttk.Entry(input_frame, textvariable=var).pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=5)
                        item_vars[input_field['name']] = var
                
                    # Store the variables with the frame for later access
                    frame.item = item
                    frame.vars = item_vars
                else:
                    # No inputs needed
                    frame.item = item
                    frame.vars = {}
                
                # Add buttons for this item
                button_frame = ttk.Frame(frame)
                button_frame.pack(fill=tk.X, padx=5, pady=5)
                
                ttk.Button(button_frame, text="Add to Preview",
                          command=lambda f=frame: self.add_config_to_preview(f.item, f.vars)).pack(side=tk.RIGHT, padx=5)
                ttk.Button(button_frame, text="Run", 
                          command=lambda f=frame: self.run_config_item(f.item, f.vars)).pack(side=tk.RIGHT, padx=5)
        
    def save_configuration(self):
        """Save the current configuration values to a file"""
        # This is a stub - you need to implement this from the original code
        pass
        
    def load_configuration(self):
        """Load configuration values from a file"""
        # This is a stub - you need to implement this from the original code
        pass
        
    def execute_selected_preview_items(self):
        """Execute all selected preview items"""
        # Get the selected switch number
        switch_num = self.selected_switch.get()
        
        # Check if the selected switch is in the switch_tabs and connected
        if switch_num not in self.switch_tabs or not self.switch_tabs[switch_num]['connection']:
            messagebox.showwarning("Not Connected", f"Selected switch is not connected")
            return
            
        # Reference to the switch data
        switch_data = self.switch_tabs[switch_num]
            
        # Collect all selected items
        selected_items = []
        executed_item_ids = []  # Store IDs of items that will be executed
        
        for item in self.preview_items:
            if self.preview_vars[item['id']].get():
                selected_items.append(item)
                executed_item_ids.append(item['id'])
        
        if not selected_items:
            messagebox.showinfo("Information", "No configurations selected")
            return
        
        # Switch to console tab for the selected switch
        self.notebook.select(switch_data['frame'])
        
        # Store selected items for command sequencing (in the specific switch data)
        switch_data['queued_commands'] = []
        switch_data['executed_preview_items'] = executed_item_ids
        
        # Build a flat list of all commands to execute
        for preview_item in selected_items:
            item = preview_item['item']
            inputs = preview_item['inputs'] or {}
            
            commands = item["command"]
            if not isinstance(commands, list):
                commands = [commands]
            
            for cmd in commands:
                try:
                    # Format command with inputs
                    formatted_cmd = cmd.format(**inputs)
                    switch_data['queued_commands'].append(formatted_cmd)
                except KeyError as e:
                    self.log_to_console_for_switch(switch_num, f"Error: Missing input value {e} for command: {cmd}\n")
                except Exception as e:
                    self.log_to_console_for_switch(switch_num, f"Error formatting command: {e}\n")
        
        # Execute the first command or queue all if auto-execute
        if switch_data['queued_commands']:
            console_input = switch_data['console_input']
            
            if switch_data['auto_execute'].get():
                # Start executing all commands automatically
                self.execute_next_command_for_switch(switch_num)
            else:
                # Just load the first command for manual execution
                console_input.delete(0, tk.END)
                console_input.insert(0, switch_data['queued_commands'][0])
                self.log_to_console_for_switch(switch_num, "Ready to execute command. Press Enter or click Send to continue.\n")
                
    def execute_next_command_for_switch(self, switch_num):
        """Execute the next command in the queue for a specific switch"""
        if switch_num not in self.switch_tabs:
            return
            
        switch_data = self.switch_tabs[switch_num]
        
        # Check if manual mode is enabled - if so, don't auto-execute
        if switch_data['manual_mode'].get():
            # Clear the queue when in manual mode
            switch_data['queued_commands'] = []
            self.log_to_console_for_switch(switch_num, "Manual mode enabled. Auto-execution cancelled.\n")
            return
            
        # No more commands to execute
        if not switch_data['queued_commands']:
            self.log_to_console_for_switch(switch_num, "All commands executed.\n")
            
            # Mark executed items
            if hasattr(switch_data, 'executed_preview_items') and switch_data['executed_preview_items']:
                for item_id in switch_data['executed_preview_items']:
                    self.mark_item_executed(item_id)
                    
            # Show cat GIF when all commands are executed
            self.show_cat_gif()
            return
            
        # Get but don't remove the first command from the queue
        cmd = switch_data['queued_commands'][0]
        
        # Send the command
        try:
            # Log the command to the console
            self.log_to_console_for_switch(switch_num, f"\n> {cmd}\n")
            
            # Send the command based on connection type
            if switch_data['connection_type'].get() == "COM":
                switch_data['connection'].write((cmd + "\r\n").encode())
                # Flush the buffer
                switch_data['connection'].flush()
            else:
                switch_data['ssh_shell'].send(cmd + "\n")
                
            # If auto-execute, wait and run the next one
            if switch_data['auto_execute'].get() and len(switch_data['queued_commands']) > 1:
                # Remove the command we just executed
                switch_data['queued_commands'].pop(0)
                delay_ms = int(switch_data['command_delay'].get() * 1000)
                self.root.after(delay_ms, lambda: self.execute_next_command_for_switch(switch_num))
            elif len(switch_data['queued_commands']) > 1:
                # Manual mode but more commands - load the next one
                console_input = switch_data['console_input']
                
                # Remove the command we just executed
                switch_data['queued_commands'].pop(0)
                
                # Load the next command
                console_input.delete(0, tk.END)
                console_input.insert(0, switch_data['queued_commands'][0])
                self.log_to_console_for_switch(switch_num, "Ready for next command. Press Enter or click Send to continue.\n")
            else:
                # Only one command left, remove it after execution
                switch_data['queued_commands'].pop(0)
                
        except Exception as e:
            self.log_to_console_for_switch(switch_num, f"Error sending command: {e}\n")
            
    def mark_item_executed(self, item_id):
        """Mark a preview item as executed with a checkmark"""
        for item in self.preview_items:
            if item['id'] == item_id:
                # Create checkmark if it doesn't already exist
                if 'checkmark_label' not in item:
                    checkmark_label = ttk.Label(item['frame'], text="✓", foreground="green", font=("Arial", 10, "bold"))
                    checkmark_label.pack(side=tk.LEFT, after=item['checkbox'], padx=(0, 5))
                    item['checkmark_label'] = checkmark_label
                    item['executed'] = True
                break
                
    def add_config_to_preview(self, item, vars_dict):
        """Add a configuration item to the preview tab"""
        # Get the values from the input fields
        input_values = {name: var.get() for name, var in vars_dict.items()}
        
        # Validate inputs
        for input_field in item.get("inputs", []):
            name = input_field["name"]
            if name in input_values:
                value = input_values[name]
                if not value:
                    messagebox.showerror("Input Error", f"Please enter a value for {input_field['description']}")
                    return
                
                # Convert to int if needed
                if input_field["type"] == "int":
                    try:
                        input_values[name] = int(value)
                    except ValueError:
                        messagebox.showerror("Input Error", 
                                            f"Invalid value for {input_field['description']}. Must be a number.")
                        return
        
        # Add to preview
        self.add_to_preview(item, input_values if input_values else None)
        
        # Show a notification instead of switching tabs
        self.show_notification(f"Added '{item['name']}' to preview")
    
    def run_config_item(self, item, vars_dict):
        """Run a specific configuration item"""
        if not self.connection:
            messagebox.showwarning("Not Connected", "Please connect to a switch first")
            return
            
        # Get the selected switch number
        switch_num = self.selected_switch.get()
        
        # Check if the selected switch is in the switch_tabs and connected
        if switch_num not in self.switch_tabs or not self.switch_tabs[switch_num]['connection']:
            messagebox.showwarning("Not Connected", f"Selected switch is not connected")
            return
        
        # Get the values from the input fields
        input_values = {name: var.get() for name, var in vars_dict.items()}
        
        # Validate inputs
        for input_field in item.get("inputs", []):
            name = input_field["name"]
            if name in input_values:
                value = input_values[name]
                if not value:
                    messagebox.showerror("Input Error", f"Please enter a value for {input_field['description']}")
                    return
                
                # Convert to int if needed
                if input_field["type"] == "int":
                    try:
                        input_values[name] = int(value)
                    except ValueError:
                        messagebox.showerror("Input Error", 
                                            f"Invalid value for {input_field['description']}. Must be a number.")
                        return
        
        # Format the command with the input values
        commands = item["command"]
        if not isinstance(commands, list):
            commands = [commands]
            
        # Switch to console tab for the selected switch
        self.notebook.select(self.switch_tabs[switch_num]['frame'])
        
        # Process each command
        def run_commands():
            for cmd in commands:
                try:
                    formatted_cmd = cmd.format(**input_values)
                    # If auto-execute is enabled, send directly
                    if self.switch_tabs[switch_num]['auto_execute'].get():
                        self.send_command_to_switch(formatted_cmd, switch_num)
                        time.sleep(self.switch_tabs[switch_num]['command_delay'].get())
                    else:
                        # Otherwise, put in input field for manual execution
                        console_input = self.switch_tabs[switch_num]['console_input']
                        console_input.delete(0, tk.END)
                        console_input.insert(0, formatted_cmd)
                        # Wait for user to press Enter
                        self.log_to_console_for_switch(switch_num, "Ready to execute command. Press Enter or click Send to continue.\n")
                        break  # Only queue the first command for manual execution
                except KeyError as e:
                    messagebox.showerror("Input Error", f"Missing input value: {e}")
                    return
                except Exception as e:
                    messagebox.showerror("Command Error", str(e))
                    return
        
        # Run in a separate thread to avoid blocking the UI
        threading.Thread(target=run_commands, daemon=True).start()
            
    def send_command_to_switch(self, command, switch_num):
        """Send a command to a specific switch"""
        if switch_num not in self.switch_tabs:
            return
            
        switch_data = self.switch_tabs[switch_num]
        
        # Check if manual mode is enabled - if so, don't auto-send
        if switch_data['manual_mode'].get():
            # If in manual mode, just put the command in the input field but don't send
            console_input = switch_data['console_input']
            console_input.delete(0, tk.END)
            console_input.insert(0, command)
            self.log_to_console_for_switch(switch_num, "Manual mode enabled. Command loaded but not sent automatically.\n")
            return
            
        # Log the command
        self.log_to_console_for_switch(switch_num, f"\n> {command}\n")
        
        # Send the command
        try:
            if switch_data['connection_type'].get() == "COM":
                switch_data['connection'].write((command + "\r\n").encode())
                # Flush the buffer
                switch_data['connection'].flush()
            else:
                switch_data['ssh_shell'].send(command + "\n")
                
        except Exception as e:
            raise Exception(f"Error sending command: {e}")
            
    def update_item_highlight(self, item_id):
        """Update the highlighting of a preview item based on its selection state"""
        for item in self.preview_items:
            if item['id'] == item_id:
                is_selected = self.preview_vars[item_id].get()
                
                if is_selected:
                    # Highlight in green
                    item['frame'].configure(style="Selected.TFrame")
                    item['label'].configure(style="Selected.TLabel")
                else:
                    # Normal styling
                    item['frame'].configure(style="")
                    item['label'].configure(style="")
                break
    
    def remove_preview_item(self, item_id):
        """Remove an item from the preview"""
        for i, item in enumerate(self.preview_items):
            if item['id'] == item_id:
                # Destroy the frame
                item['frame'].destroy()
                # Remove from list and dict
                self.preview_items.pop(i)
                self.preview_vars.pop(item_id)
                break
        
        # Show empty label if no items
        if not self.preview_items:
            self.empty_preview_label = ttk.Label(self.preview_scrollable_frame, 
                                              text="No configurations added to preview.\nAdd configurations from the Configuration tab.")
            self.empty_preview_label.pack(pady=20)
    
    def clear_preview_items(self):
        """Clear all items from the preview"""
        for item in self.preview_items:
            item['frame'].destroy()
        
        self.preview_items = []
        self.preview_vars = {}
        
        # Show empty label
        self.empty_preview_label = ttk.Label(self.preview_scrollable_frame, 
                                          text="No configurations added to preview.\nAdd configurations from the Configuration tab.")
        self.empty_preview_label.pack(pady=20)

    def send_command(self, event=None):
        """Send a command to the switch"""
        # Forward to the switch-specific command for switch 1
        self.send_command_for_switch(event, 1)

    def add_to_preview(self, item, inputs=None):
        """Add a configuration item to the preview tab"""
        # Remove empty label if present
        if hasattr(self, 'empty_preview_label') and self.empty_preview_label.winfo_exists():
            self.empty_preview_label.destroy()
        
        # Create a frame for this preview item
        item_frame = ttk.Frame(self.preview_scrollable_frame)
        item_frame.pack(fill=tk.X, padx=5, pady=2)
        
        # Add a checkbutton
        var = tk.BooleanVar(value=True)
        check = ttk.Checkbutton(item_frame, variable=var)
        check.pack(side=tk.LEFT, padx=(5, 10))
        
        # Create a label for the item
        category_name = next((cat for cat, items in CONFIG_DATA.items() 
                             if item in items), "Unknown")
        
        label_text = f"{category_name} > {item['name']}"
        if inputs:
            # Format command with inputs
            if isinstance(item['command'], list):
                commands = []
                for cmd in item['command']:
                    try:
                        commands.append(cmd.format(**inputs))
                    except KeyError:
                        commands.append(cmd)  # Keep original if format fails
                command_text = "\n".join(commands)
            else:
                try:
                    command_text = item['command'].format(**inputs)
                except KeyError:
                    command_text = item['command']  # Keep original if format fails
            
            # Add input information to label
            input_text = ", ".join([f"{k}={v}" for k, v in inputs.items()])
            label_text += f" ({input_text})"
        else:
            # Just display the raw command
            if isinstance(item['command'], list):
                command_text = "\n".join(item['command'])
            else:
                command_text = item['command']
        
        label = ttk.Label(item_frame, text=label_text)
        label.pack(side=tk.LEFT, padx=5, anchor=tk.W)
        
        # Store the preview item info including the checkbox variable
        preview_id = len(self.preview_items)
        self.preview_vars[preview_id] = var
        
        # Store the item and created widgets for later reference
        preview_item = {
            'id': preview_id,
            'item': item,
            'inputs': inputs,
            'frame': item_frame,
            'checkbox': check,
            'label': label,
            'command_text': command_text,
            'executed': False
        }
        self.preview_items.append(preview_item)
        
        # Add Remove button
        ttk.Button(item_frame, text="×", width=3,
                  command=lambda i=preview_id: self.remove_preview_item(i)).pack(side=tk.RIGHT, padx=5)
        
        # Add detailed command text in a collapsible frame
        detail_frame = ttk.LabelFrame(item_frame, text="Command")
        detail_frame.pack(fill=tk.X, padx=30, pady=5, after=label)
        
        # Add command text
        cmd_label = ttk.Label(detail_frame, text=command_text, wraplength=800, justify=tk.LEFT)
        cmd_label.pack(fill=tk.X, padx=5, pady=5, anchor=tk.W)
        
        # Update highlight based on checkbox
        self.update_item_highlight(preview_id)
        
        # Bind checkbox to highlight update
        var.trace_add("write", lambda *args, i=preview_id: self.update_item_highlight(i))


if __name__ == "__main__":
    root = tk.Tk()
    
    # Create custom styles
    style = ttk.Style()
    style.configure("Selected.TFrame", background="#e6ffe6")  # Light green
    style.configure("Selected.TLabel", background="#e6ffe6")  # Light green
    
    app = CiscoSwitchConfigurator(root)
    root.mainloop() 