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
        
        self.connection = None
        self.connection_type = tk.StringVar(value="COM")
        self.com_port = tk.StringVar()
        self.ssh_host = tk.StringVar()
        self.ssh_username = tk.StringVar()
        self.ssh_password = tk.StringVar()
        self.baudrate = tk.IntVar(value=9600)
        
        # Store preview items
        self.preview_items = []
        self.preview_vars = {}
        
        # Create notification label
        self.notification_var = tk.StringVar()
        self.notification_frame = None
        
        self.setup_ui()
        
    def setup_ui(self):
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
        
        # Console tab
        self.console_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.console_frame, text="Console")
        
        # Setup Connection Tab
        self.setup_connection_tab()
        
        # Setup Configuration Tab
        self.setup_configuration_tab()
        
        # Setup Preview Tab
        self.setup_preview_tab()
        
        # Setup Console Tab
        self.setup_console_tab()
        
        # Setup notification area at the bottom
        self.setup_notification_area()
        
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
        ttk.Button(button_frame, text="Run Selected", command=self.run_selected_config).pack(side=tk.RIGHT, padx=5)
        
        # Populate categories from CONFIG_DATA
        self.populate_categories()
        
    def setup_preview_tab(self):
        """Setup the preview tab with a list of commands to execute"""
        # Create a frame with scrollbar for preview items
        preview_container = ttk.Frame(self.preview_frame)
        preview_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Connection status at the top
        self.connection_status_frame = ttk.LabelFrame(preview_container, text="Connection Status")
        self.connection_status_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.connection_status_label = ttk.Label(self.connection_status_frame, 
                                               text="Not connected",
                                               foreground="red",
                                               font=("Arial", 10, "bold"))
        self.connection_status_label.pack(pady=5, padx=10)
        
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
    
    def setup_console_tab(self):
        """Set up the console tab"""
        console_frame = ttk.Frame(self.console_frame)
        console_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create a frame for the console options
        options_frame = ttk.Frame(console_frame)
        options_frame.pack(fill=tk.X, side=tk.TOP, pady=(0, 5))
        
        # Create variables for console options
        self.manual_mode = tk.BooleanVar(value=False)
        self.auto_execute = tk.BooleanVar(value=False)
        self.command_delay = tk.DoubleVar(value=0.5)
        
        # Add a checkbox to toggle manual mode
        manual_mode_check = ttk.Checkbutton(
            options_frame,
            text="Manual Typing Mode",
            variable=self.manual_mode,
            command=self.toggle_manual_mode
        )
        manual_mode_check.pack(side=tk.LEFT)
        
        # Add auto-execute option
        auto_execute_check = ttk.Checkbutton(
            options_frame,
            text="Auto-execute commands",
            variable=self.auto_execute
        )
        auto_execute_check.pack(side=tk.LEFT, padx=15)
        
        # Add delay option
        ttk.Label(options_frame, text="Delay (sec):").pack(side=tk.LEFT, padx=(15, 5))
        delay_entry = ttk.Entry(options_frame, textvariable=self.command_delay, width=5)
        delay_entry.pack(side=tk.LEFT)
        
        # Add a Test Connection button
        test_conn_button = ttk.Button(
            options_frame,
            text="Test Connection",
            command=self.test_connection
        )
        test_conn_button.pack(side=tk.LEFT, padx=20)
        
        # Add a button to clear the console
        clear_button = ttk.Button(
            options_frame,
            text="Clear Console",
            command=self.clear_console
        )
        clear_button.pack(side=tk.RIGHT)
        
        # Create the console output text box
        self.console_output = scrolledtext.ScrolledText(
            console_frame, wrap=tk.WORD, width=80, height=20, bg="black", fg="green"
        )
        self.console_output.pack(fill=tk.BOTH, expand=True)
        self.console_output.tag_configure("device_response", foreground="#00FFFF")  # Light cyan for device responses
        
        # Set the font
        self.console_output.configure(font=("Courier New", 10))
        
        # Make it read-only
        self.console_output.config(state=tk.DISABLED)
        
        # Create the input field
        input_frame = ttk.Frame(console_frame)
        input_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Label(input_frame, text="Command:").pack(side=tk.LEFT)
        self.console_input = ttk.Entry(input_frame)
        self.console_input.pack(fill=tk.X, expand=True, side=tk.LEFT, padx=5)
        self.console_input.bind("<Return>", self.send_command)
        
        ttk.Button(input_frame, text="Send", command=self.send_command).pack(side=tk.RIGHT)
        
        # Add an initial welcome message
        self.log_to_console("Console ready. Connect to a device to begin.\n")
        
        # Bind the tab change event to set focus on the console input field
        self.notebook.bind("<<NotebookTabChanged>>", self.handle_tab_change)
        
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
        
    def refresh_com_ports(self):
        """Refresh the available COM ports"""
        ports = [port.device for port in list_ports.comports()]
        self.com_port_combo['values'] = ports
        if ports and not self.com_port.get():
            self.com_port.set(ports[0])
            
    def toggle_connection_fields(self):
        """Toggle visibility of connection fields based on connection type"""
        if self.connection_type.get() == "COM":
            self.com_frame.pack(fill=tk.X, padx=10, pady=10)
            self.ssh_frame.pack_forget()
        else:  # SSH
            self.com_frame.pack_forget()
            self.ssh_frame.pack(fill=tk.X, padx=10, pady=10)
            
    def connect(self):
        """Connect to the switch via COM port or SSH"""
        try:
            if self.connection_type.get() == "COM":
                self.connection = serial.Serial(
                    port=self.com_port.get(),
                    baudrate=self.baudrate.get(),
                    timeout=1
                )
                connection_info = f"Connected to {self.com_port.get()} at {self.baudrate.get()} baud"
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
                self.connection = client
                self.ssh_shell = client.invoke_shell()
                connection_info = f"Connected to {self.ssh_host.get()} via SSH"
                self.log_to_console(f"{connection_info}\n")
                
                # Update connection status
                self.update_connection_status(True, f"SSH: {self.ssh_username.get()}@{self.ssh_host.get()}")
                
                # Start a thread to read from SSH
                threading.Thread(target=self.read_from_ssh, daemon=True).start()
                
            # Switch to console tab after connecting
            self.notebook.select(3)  # Index 3 is the Console tab (after Preview tab)
                
        except Exception as e:
            messagebox.showerror("Connection Error", str(e))
            self.update_connection_status(False)
            
    def disconnect(self):
        """Disconnect from the switch"""
        if self.connection:
            try:
                if self.connection_type.get() == "COM":
                    self.connection.close()
                else:
                    self.connection.close()
                    
                self.connection = None
                self.log_to_console("Disconnected from switch\n")
                
                # Update connection status
                self.update_connection_status(False)
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
            
    def send_command(self, event=None):
        """Send a command to the switch"""
        if not self.connection:
            messagebox.showwarning("Not Connected", "Please connect to a switch first")
            return
            
        command = self.console_input.get()
        if not command:
            return
            
        # Log the command to the console
        self.log_to_console(f"\n> {command}\n")
        
        # Send the command
        try:
            if self.connection_type.get() == "COM":
                self.connection.write((command + "\r\n").encode())
                # Flush the buffer
                self.connection.flush()
            else:
                self.ssh_shell.send(command + "\n")
                
            # Clear the input field
            self.console_input.delete(0, tk.END)
            
            # If manual mode is enabled, don't process queued commands
            if self.manual_mode.get():
                # Keep focus on the input field for next manual command
                self.console_input.focus_set()
            else:
                # Wait a bit for response to come in before proceeding to next queued command
                self.root.after(500, lambda: self.check_for_next_command(command))
                
        except Exception as e:
            messagebox.showerror("Command Error", str(e))
            
    def check_for_next_command(self, last_command):
        """Check if we should proceed to the next command after waiting for a response"""
        # Don't process queued commands if in manual mode
        if self.manual_mode.get():
            return
            
        # If we have queued commands, advance to the next one
        if hasattr(self, 'queued_commands') and len(self.queued_commands) > 0 and not self.auto_execute.get():
            # Remove the current command from the queue if it matches
            if self.queued_commands and self.queued_commands[0] == last_command:
                self.queued_commands.pop(0)
            
            # Wait a short time before loading the next command (to allow response to be seen)
            if self.queued_commands:
                self.console_input.delete(0, tk.END)
                self.console_input.insert(0, self.queued_commands[0])
                self.log_to_console("Ready for next command. Press Enter or click Send to continue.\n")
    
    def log_to_console(self, text, from_device=False):
        """Log text to the console output"""
        self.console_output.config(state=tk.NORMAL)
        
        # Apply different formatting based on source
        if from_device:
            # Device responses in light cyan
            self.console_output.tag_config("device", foreground="#00CCCC")
            self.console_output.insert(tk.END, text, "device")
        else:
            # Our commands and messages in green
            self.console_output.insert(tk.END, text)
            
        self.console_output.see(tk.END)
        self.console_output.config(state=tk.DISABLED)
    
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
                
                # Add Run button for this item
                button_frame = ttk.Frame(frame)
                button_frame.pack(fill=tk.X, padx=5, pady=5)
                
                ttk.Button(button_frame, text="Add to Preview",
                          command=lambda f=frame: self.add_config_to_preview(f.item, f.vars)).pack(side=tk.RIGHT, padx=5)
                ttk.Button(button_frame, text="Run", 
                          command=lambda f=frame: self.run_config_item(f.item, f.vars)).pack(side=tk.RIGHT, padx=5)
    
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
    
    def run_config_item(self, item, vars_dict):
        """Run a specific configuration item"""
        if not self.connection:
            messagebox.showwarning("Not Connected", "Please connect to a switch first")
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
            
        # Switch to console tab
        self.notebook.select(2)  # Index 2 is the console tab
        
        # Process each command
        def run_commands():
            for cmd in commands:
                try:
                    formatted_cmd = cmd.format(**input_values)
                    # If auto-execute is enabled, send directly
                    if self.auto_execute.get():
                        self.send_command_to_device(formatted_cmd)
                        time.sleep(self.command_delay.get())
                    else:
                        # Otherwise, put in input field for manual execution
                        self.console_input.delete(0, tk.END)
                        self.console_input.insert(0, formatted_cmd)
                        # Wait for user to press Enter
                        self.log_to_console("Ready to execute command. Press Enter or click Send to continue.\n")
                        break  # Only queue the first command for manual execution
                except KeyError as e:
                    messagebox.showerror("Input Error", f"Missing input value: {e}")
                    return
                except Exception as e:
                    messagebox.showerror("Command Error", str(e))
                    return
        
        # Run in a separate thread to avoid blocking the UI
        threading.Thread(target=run_commands, daemon=True).start()
                
    def send_command_to_device(self, command):
        """Send a command to the device and switch to console tab"""
        # Log the command
        self.log_to_console(f"\n> {command}\n")
        
        # Send the command
        try:
            if self.connection_type.get() == "COM":
                self.connection.write((command + "\r\n").encode())
                # Flush the buffer
                self.connection.flush()
            else:
                self.ssh_shell.send(command + "\n")
                
            # If auto-execute mode is not enabled, just put it in the input field
            if not self.auto_execute.get() and hasattr(self, 'queued_commands') and self.queued_commands:
                # Fill the console input with this command
                self.console_input.delete(0, tk.END)
                self.console_input.insert(0, command)
                
        except Exception as e:
            raise Exception(f"Error sending command: {e}")
        
    def run_selected_config(self):
        """Run the selected configuration item from the category list"""
        selection = self.category_listbox.curselection()
        if not selection:
            messagebox.showinfo("Information", "Please select a category first")
            return
            
        category = self.category_listbox.get(selection[0])
        
        if category in CONFIG_DATA:
            items = CONFIG_DATA[category]
            if not items:
                messagebox.showinfo("Information", "No configuration items in this category")
                return
                
            # Create a selection dialog
            select_dialog = tk.Toplevel(self.root)
            select_dialog.title(f"Select {category} Items")
            select_dialog.geometry("400x300")
            select_dialog.transient(self.root)
            select_dialog.grab_set()
            
            ttk.Label(select_dialog, text=f"Select {category} items to run:").pack(pady=10)
            
            # Create a frame with checkboxes for each item
            frame = ttk.Frame(select_dialog)
            frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Add a scrollbar
            canvas = tk.Canvas(frame)
            scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
            scrollable_frame = ttk.Frame(canvas)
            
            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            # Add checkboxes for each item
            vars = []
            for i, item in enumerate(items):
                var = tk.BooleanVar(value=False)
                ttk.Checkbutton(scrollable_frame, text=item["name"], variable=var).pack(anchor=tk.W, padx=5, pady=2)
                vars.append((var, item))
                
            # Add buttons
            button_frame = ttk.Frame(select_dialog)
            button_frame.pack(fill=tk.X, padx=10, pady=10)
            
            ttk.Button(button_frame, text="Run Selected", 
                      command=lambda: self.run_multiple_items(vars, select_dialog)).pack(side=tk.RIGHT, padx=5)
            ttk.Button(button_frame, text="Cancel", 
                      command=select_dialog.destroy).pack(side=tk.RIGHT, padx=5)
                      
    def run_multiple_items(self, vars, dialog):
        """Run multiple selected configuration items"""
        selected_items = [item for var, item in vars if var.get()]
        
        if not selected_items:
            messagebox.showinfo("Information", "No items selected")
            return
            
        dialog.destroy()
        
        # Switch to console tab
        self.notebook.select(2)  # Index 2 is the console tab
        
        # For each selected item, show a dialog to collect inputs
        for item in selected_items:
            if item.get("inputs"):
                # Create input dialog
                input_dialog = tk.Toplevel(self.root)
                input_dialog.title(f"Inputs for {item['name']}")
                input_dialog.transient(self.root)
                input_dialog.grab_set()
                
                ttk.Label(input_dialog, text=f"Enter inputs for {item['name']}:").pack(pady=10)
                
                # Create input fields
                input_frame = ttk.Frame(input_dialog)
                input_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
                
                item_vars = {}
                for i, input_field in enumerate(item.get("inputs", [])):
                    field_frame = ttk.Frame(input_frame)
                    field_frame.pack(fill=tk.X, padx=5, pady=5)
                    
                    ttk.Label(field_frame, text=f"{input_field['description']}:").pack(side=tk.LEFT, padx=5)
                    
                    if input_field['type'] == 'int':
                        var = tk.StringVar()
                    else:
                        var = tk.StringVar()
                        
                    ttk.Entry(field_frame, textvariable=var).pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=5)
                    item_vars[input_field['name']] = var
                    
                # Add buttons
                button_frame = ttk.Frame(input_dialog)
                button_frame.pack(fill=tk.X, padx=10, pady=10)
                
                ttk.Button(button_frame, text="Run", 
                          command=lambda i=item, v=item_vars, d=input_dialog: self.run_item_with_inputs(i, v, d)).pack(side=tk.RIGHT, padx=5)
                ttk.Button(button_frame, text="Cancel", 
                          command=input_dialog.destroy).pack(side=tk.RIGHT, padx=5)
                          
                # Wait for dialog to close
                self.root.wait_window(input_dialog)
            else:
                # No inputs needed, run directly
                self.run_config_item(item, {})
                
    def run_item_with_inputs(self, item, vars_dict, dialog):
        """Run a configuration item with inputs from dialog"""
        # Get values from dialog
        input_values = {name: var.get() for name, var in vars_dict.items()}
        
        # Close the dialog
        dialog.destroy()
        
        # Run the item
        try:
            self.run_config_item(item, vars_dict)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            
    def save_configuration(self):
        """Save the current configuration values to a file"""
        # Create a dialog to get the configuration name
        save_dialog = tk.Toplevel(self.root)
        save_dialog.title("Save Configuration")
        save_dialog.geometry("400x150")
        save_dialog.transient(self.root)
        save_dialog.grab_set()
        
        ttk.Label(save_dialog, text="Enter a name for this configuration:").pack(pady=(20, 10))
        
        config_name = tk.StringVar()
        name_entry = ttk.Entry(save_dialog, textvariable=config_name, width=40)
        name_entry.pack(padx=20, pady=5)
        name_entry.focus_set()
        
        button_frame = ttk.Frame(save_dialog)
        button_frame.pack(fill=tk.X, padx=20, pady=15)
        
        ttk.Button(button_frame, text="Save", 
                  command=lambda: self.do_save_config(config_name.get(), save_dialog)).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", 
                  command=save_dialog.destroy).pack(side=tk.RIGHT, padx=5)
        
    def do_save_config(self, config_name, dialog):
        """Actually save the configuration after name is provided"""
        if not config_name:
            messagebox.showerror("Error", "Please enter a name for the configuration", parent=dialog)
            return
            
        # Create saved_configs directory if it doesn't exist
        os.makedirs("saved_configs", exist_ok=True)
        
        # Create a filename based on the config name
        safe_name = "".join(c for c in config_name if c.isalnum() or c in " _-").strip().replace(" ", "_")
        file_path = os.path.join("saved_configs", f"{safe_name}.json")
        
        # Check if file already exists
        if os.path.exists(file_path):
            overwrite = messagebox.askyesno("Confirm Overwrite", 
                                           f"Configuration '{config_name}' already exists. Overwrite?", 
                                           parent=dialog)
            if not overwrite:
                return
                
        # Collect all input values from visible frames
        config = {
            "name": config_name,
            "date_saved": time.strftime("%Y-%m-%d %H:%M:%S"),
            "data": {}
        }
        
        # Iterate through all category frames
        for category in CONFIG_DATA.keys():
            config["data"][category] = {}
            
            # For each item in the category, save any input values
            for i, item in enumerate(CONFIG_DATA[category]):
                item_name = item["name"]
                config["data"][category][item_name] = {}
                
                # Look for visible frames with this item
                for widget in self.config_detail_frame.winfo_children():
                    if hasattr(widget, 'item') and widget.item == item and hasattr(widget, 'vars'):
                        # Save the values
                        for name, var in widget.vars.items():
                            config["data"][category][item_name][name] = var.get()
                            
        # Save to file
        try:
            with open(file_path, 'w') as f:
                json.dump(config, f, indent=2)
            messagebox.showinfo("Success", f"Configuration '{config_name}' saved successfully", parent=dialog)
            dialog.destroy()
        except Exception as e:
            messagebox.showerror("Save Error", str(e), parent=dialog)
            
    def load_configuration(self):
        """Load configuration values from a file"""
        # Create saved_configs directory if it doesn't exist
        os.makedirs("saved_configs", exist_ok=True)
        
        # Get list of saved configurations
        try:
            config_files = [f for f in os.listdir("saved_configs") if f.endswith(".json")]
        except Exception:
            config_files = []
            
        if not config_files:
            messagebox.showinfo("Information", "No saved configurations found.\nSave a configuration first.")
            return
            
        # Create a dialog to select a configuration
        load_dialog = tk.Toplevel(self.root)
        load_dialog.title("Load Configuration")
        load_dialog.geometry("400x200")
        load_dialog.transient(self.root)
        load_dialog.grab_set()
        
        ttk.Label(load_dialog, text="Select a configuration to load:").pack(pady=(20, 10))
        
        # Create a frame for the combobox
        select_frame = ttk.Frame(load_dialog)
        select_frame.pack(fill=tk.X, padx=20, pady=5)
        
        # Dictionary to map displayed names to filenames
        self.config_map = {}
        config_names = []
        
        # Load configuration names from files
        for filename in config_files:
            try:
                with open(os.path.join("saved_configs", filename), 'r') as f:
                    config_data = json.load(f)
                    if "name" in config_data:
                        name = config_data["name"]
                        date = config_data.get("date_saved", "Unknown date")
                        display_name = f"{name} ({date})"
                        config_names.append(display_name)
                        self.config_map[display_name] = filename
                    else:
                        # If no name in config, use filename
                        display_name = filename.replace(".json", "")
                        config_names.append(display_name)
                        self.config_map[display_name] = filename
            except Exception:
                # If error reading file, just use filename
                display_name = filename.replace(".json", "")
                config_names.append(display_name)
                self.config_map[display_name] = filename
        
        # Sort by name
        config_names.sort()
        
        # Create combobox
        self.selected_config = tk.StringVar()
        if config_names:
            self.selected_config.set(config_names[0])
            
        config_combo = ttk.Combobox(select_frame, textvariable=self.selected_config, 
                                   values=config_names, width=50, state="readonly")
        config_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Preview of selected config
        preview_frame = ttk.LabelFrame(load_dialog, text="Configuration Details")
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.config_preview = ttk.Label(preview_frame, text="", wraplength=350, justify=tk.LEFT)
        self.config_preview.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)
        
        # Update preview when selection changes
        config_combo.bind("<<ComboboxSelected>>", lambda e: self.update_config_preview())
        
        # Initialize preview
        self.update_config_preview()
        
        # Buttons
        button_frame = ttk.Frame(load_dialog)
        button_frame.pack(fill=tk.X, padx=20, pady=15)
        
        ttk.Button(button_frame, text="Load", 
                  command=lambda: self.do_load_config(load_dialog)).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Delete", 
                  command=lambda: self.delete_config(load_dialog)).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", 
                  command=load_dialog.destroy).pack(side=tk.RIGHT, padx=5)
        
    def update_config_preview(self):
        """Update the preview of the selected configuration"""
        if not hasattr(self, 'selected_config') or not self.selected_config.get():
            return
            
        selected = self.selected_config.get()
        if selected in self.config_map:
            filename = self.config_map[selected]
            try:
                with open(os.path.join("saved_configs", filename), 'r') as f:
                    config = json.load(f)
                    
                # Create preview text
                if "name" in config and "date_saved" in config:
                    preview = f"Name: {config['name']}\nSaved: {config['date_saved']}\n\n"
                else:
                    preview = f"File: {filename}\n\n"
                    
                # Show categories and item counts
                if "data" in config:
                    for category, items in config["data"].items():
                        if items:  # Only show non-empty categories
                            item_count = sum(1 for item, values in items.items() if values)
                            if item_count > 0:
                                preview += f"• {category}: {item_count} items\n"
                                
                self.config_preview.config(text=preview)
            except Exception as e:
                self.config_preview.config(text=f"Error loading preview: {e}")
                
    def delete_config(self, dialog):
        """Delete the selected configuration"""
        if not hasattr(self, 'selected_config') or not self.selected_config.get():
            return
            
        selected = self.selected_config.get()
        if selected in self.config_map:
            filename = self.config_map[selected]
            confirm = messagebox.askyesno("Confirm Delete", 
                                        f"Are you sure you want to delete configuration '{selected}'?", 
                                        parent=dialog)
            if confirm:
                try:
                    os.remove(os.path.join("saved_configs", filename))
                    messagebox.showinfo("Success", f"Configuration '{selected}' deleted successfully", parent=dialog)
                    dialog.destroy()
                    # Reopen the load dialog to refresh the list
                    self.load_configuration()
                except Exception as e:
                    messagebox.showerror("Delete Error", str(e), parent=dialog)
                    
    def do_load_config(self, dialog):
        """Actually load the selected configuration"""
        if not hasattr(self, 'selected_config') or not self.selected_config.get():
            return
            
        selected = self.selected_config.get()
        if selected in self.config_map:
            filename = self.config_map[selected]
            try:
                with open(os.path.join("saved_configs", filename), 'r') as f:
                    config = json.load(f)
                    
                # Apply loaded values to any visible input fields
                if "data" in config:
                    data = config["data"]
                else:
                    data = config  # Handle legacy format
                    
                for category, items in data.items():
                    # Select the category to make it visible
                    for i in range(self.category_listbox.size()):
                        if self.category_listbox.get(i) == category:
                            self.category_listbox.selection_clear(0, tk.END)
                            self.category_listbox.selection_set(i)
                            self.on_category_select(None)
                            break
                            
                    # Now apply the values to visible frames
                    for item_name, values in items.items():
                        # Find the frame with this item
                        for widget in self.config_detail_frame.winfo_children():
                            if hasattr(widget, 'item') and widget.item["name"] == item_name and hasattr(widget, 'vars'):
                                # Apply the values
                                for name, value in values.items():
                                    if name in widget.vars:
                                        widget.vars[name].set(value)
                                        
                messagebox.showinfo("Success", f"Configuration '{selected}' loaded successfully", parent=dialog)
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Load Error", str(e), parent=dialog)

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
        
        # Store the preview item info including the checkbox variable
        preview_id = len(self.preview_items)
        self.preview_vars[preview_id] = var
        
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
        
        # Store the item and created widgets for later reference
        preview_item = {
            'id': preview_id,
            'item': item,
            'inputs': inputs,
            'frame': item_frame,
            'checkbox': check,
            'label': label,
            'command_text': command_text
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
        
        # Show notification instead of switching tabs
        self.show_notification(f"Successfully added '{item['name']}' to preview")
    
    def update_item_highlight(self, item_id):
        """Update the highlighting of a preview item based on its selection state"""
        if item_id < len(self.preview_items):
            item = self.preview_items[item_id]
            is_selected = self.preview_vars[item_id].get()
            
            if is_selected:
                # Highlight in green
                item['frame'].configure(style="Selected.TFrame")
                item['label'].configure(style="Selected.TLabel")
            else:
                # Normal styling
                item['frame'].configure(style="")
                item['label'].configure(style="")
    
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
    
    def execute_selected_preview_items(self):
        """Execute all selected preview items"""
        if not self.connection:
            messagebox.showwarning("Not Connected", "Please connect to a switch first")
            return
        
        # Collect all selected items
        selected_items = []
        for item in self.preview_items:
            if self.preview_vars[item['id']].get():
                selected_items.append(item)
        
        if not selected_items:
            messagebox.showinfo("Information", "No configurations selected")
            return
        
        # Switch to console tab
        self.notebook.select(3)  # Index 3 is now the Console tab
        
        # Store selected items for command sequencing
        self.queued_commands = []
        
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
                    self.queued_commands.append(formatted_cmd)
                except KeyError as e:
                    self.log_to_console(f"Error: Missing input value {e} for command: {cmd}\n")
                except Exception as e:
                    self.log_to_console(f"Error formatting command: {e}\n")
        
        # Execute the first command or queue all if auto-execute
        if self.queued_commands:
            if self.auto_execute.get():
                # Start executing all commands automatically
                self.execute_next_command()
            else:
                # Just load the first command for manual execution
                self.console_input.delete(0, tk.END)
                self.console_input.insert(0, self.queued_commands[0])
                self.log_to_console("Ready to execute command. Press Enter or click Send to continue.\n")
    
    def execute_next_command(self):
        """Execute the next command in the queue"""
        if not self.queued_commands:
            self.log_to_console("All commands executed.\n")
            return
            
        # Get but don't remove the first command from the queue (send_command will do that)
        cmd = self.queued_commands[0]
        
        # Send the command
        self.send_command_to_device(cmd)
        
        # If auto-execute, wait and run the next one
        if self.auto_execute.get() and len(self.queued_commands) > 1:
            # Remove the command we just executed
            self.queued_commands.pop(0)
            self.root.after(int(self.command_delay.get() * 1000), self.execute_next_command)
        elif len(self.queued_commands) > 1:
            # If manual mode, load the next command into the input field after this one is processed
            # The send_command method will handle removing the current command and loading the next one
            pass

    def update_connection_status(self, is_connected, connection_details=None):
        """Update the connection status displayed in the Preview tab"""
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

    def handle_tab_change(self, event):
        """Handle tab change events"""
        selected_tab = self.notebook.select()
        tab_index = self.notebook.index(selected_tab)
        
        # If the console tab is selected, focus on the input field
        if tab_index == 3:  # Index 3 is the Console tab
            self.console_input.focus_set()
    
    def toggle_manual_mode(self):
        """Toggle between manual and automated typing modes"""
        if self.manual_mode.get():
            # In manual mode, clear any queued commands
            if hasattr(self, 'queued_commands'):
                self.queued_commands = []
            # Focus on the input field
            self.console_input.focus_set()
            self.console_input.delete(0, tk.END)
            self.log_to_console("Manual typing mode enabled. Type commands directly.\n")
        else:
            self.log_to_console("Manual typing mode disabled. Using command queue.\n")
    
    def clear_console(self):
        """Clear the console output"""
        self.console_output.config(state=tk.NORMAL)
        self.console_output.delete(1.0, tk.END)
        self.console_output.config(state=tk.DISABLED)
        # Focus back on the input field
        self.console_input.focus_set()

    def test_connection(self):
        """Test the connection by sending a simple command"""
        if not self.connection:
            messagebox.showwarning("Not Connected", "Please connect to a switch first")
            return
            
        self.log_to_console("\n--- Testing connection ---\n")
        
        # Send a simple, harmless command
        try:
            # Clear any pending data in the buffer before testing
            if self.connection_type.get() == "COM" and self.connection.is_open:
                self.connection.reset_input_buffer()
                self.connection.reset_output_buffer()
                
            # Send a test command based on connection type
            if self.connection_type.get() == "COM":
                self.connection.write("\r\n".encode())  # Just send a return
                self.connection.flush()
                time.sleep(0.5)  # Wait a bit longer for response
                
                # Check if we got any response
                if self.connection.in_waiting:
                    data = self.connection.read(self.connection.in_waiting).decode('utf-8', errors='replace')
                    if data:
                        self.log_to_console(data, from_device=True)
                        self.log_to_console("\n--- Connection test successful! ---\n")
                        return
            else:  # SSH
                self.ssh_shell.send("\n")  # Just send a return
                time.sleep(0.5)  # Wait a bit longer for response
                
                # Check if we got any response
                if self.ssh_shell.recv_ready():
                    data = self.ssh_shell.recv(4096).decode('utf-8', errors='replace')
                    if data:
                        self.log_to_console(data, from_device=True)
                        self.log_to_console("\n--- Connection test successful! ---\n")
                        return
            
            # If we get here, we didn't get a response
            self.log_to_console("\n--- No response from device. Connection may be inactive. ---\n")
            
            # Try sending a more explicit command
            self.log_to_console("\n--- Trying with explicit command ---\n")
            if self.connection_type.get() == "COM":
                self.connection.write("show version\r\n".encode())
                self.connection.flush()
            else:
                self.ssh_shell.send("show version\n")
                
            # The response will be handled by the normal read threads
                
        except Exception as e:
            self.log_to_console(f"\n--- Connection test failed: {str(e)} ---\n")
            messagebox.showerror("Connection Test Failed", f"Test failed: {str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    
    # Create custom styles
    style = ttk.Style()
    style.configure("Selected.TFrame", background="#e6ffe6")  # Light green
    style.configure("Selected.TLabel", background="#e6ffe6")  # Light green
    
    app = CiscoSwitchConfigurator(root)
    root.mainloop() 