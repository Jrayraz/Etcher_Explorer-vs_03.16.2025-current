import curses
import subprocess
import os
import pty
import tkinter as tk
from tkinter import filedialog, Menu, Toplevel, simpledialog, messagebox
import psutil
import threading
import time
import logging
import fcntl

class TerminalEmulator(tk.Tk):
    def __init__(self):
        super().__init__()
        self.geometry("800x600")  # Set the initial size of the window
        self.create_gui()
        self.apply_style()
        self.password = None
        self.terminal_thread = threading.Thread(target=self.terminal)
        self.terminal_thread.daemon = True
        self.terminal_thread.start()

    def run_command(self, command):
        try:
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = process.communicate()
            if stdout:
                self.display_output(stdout)
            if stderr:
                self.display_output(stderr)
        except Exception as e:
            logging.error(f"Error running command: {e}")
            messagebox.showerror("Error running command: {e}")

    def display_output(self, output):
        self.terminal_display.insert(tk.END, output)
        self.terminal_display.see(tk.END)

    def terminal(self):
        curses.wrapper(self.main, self.terminal_display)

    @staticmethod
    def main(stdscr, terminal_display):
        stdscr.clear()
        curses.noecho()
        curses.cbreak()
        stdscr.keypad(True)
        TerminalEmulator.initialize_emulator(stdscr, terminal_display)

    @staticmethod
    def initialize_emulator(screen, terminal_display):
        global master_fd, slave_fd
        master_fd, slave_fd = pty.openpty()
        proc = subprocess.Popen(
            ['/bin/bash'],
            preexec_fn=os.setsid,
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            universal_newlines=True
        )
        flags = fcntl.fcntl(master_fd, fcntl.F_GETFL)
        fcntl.fcntl(master_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)
        screen.nodelay(1)

        while True:
            try:
                data = os.read(master_fd, 1024).decode()
                if data:
                    screen.addstr(data)
                    screen.refresh()
                    terminal_display.insert(tk.END, data)
                    terminal_display.see(tk.END)
            except OSError:
                break

            try:
                key = screen.getch()
                if key != -1:
                    os.write(master_fd, chr(key).encode())
            except curses.error:
                pass

    def create_gui(self):
        # Create frames
        self.create_frames()

        # Create right-click context menu
        self.create_context_menu()

        # Create system metrics
        self.create_system_metrics()

        # Create buttons
        self.create_buttons()

        self.update_metrics_periodically()

    def apply_style(self):
        self.configure(bg='lightblue')
        self.option_add('*Button.Background', 'orange')
        self.option_add('*Button.Foreground', 'black')

    def create_frames(self):
        # Main frame
        self.main_frame = tk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Top frame for terminal emulator
        self.terminal_display = tk.Text(self.main_frame)
        self.terminal_display.pack(fill=tk.BOTH, expand=True)
        self.terminal_display.bind("<Key>", self.on_key_press)

        # Bottom frame
        self.bottom_frame = tk.Frame(self.main_frame)
        self.bottom_frame.pack(side=tk.BOTTOM, fill=tk.X)

        # Bottom-left frame for system metrics
        self.bottom_left_frame = tk.Frame(self.bottom_frame)
        self.bottom_left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Bottom-right frame for buttons
        self.bottom_right_frame = tk.Frame(self.bottom_frame)
        self.bottom_right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    def on_key_press(self, event):
        char = event.char
        if char:
            os.write(master_fd, char.encode())

    def create_context_menu(self):
        self.context_menu = Menu(self, tearoff=0)
        self.context_menu.add_command(label="Cut", command=self.cut_text)
        self.context_menu.add_command(label="Copy", command=self.copy_text)
        self.context_menu.add_command(label="Paste", command=self.paste_text)
        self.context_menu.add_command(label="Save As", command=self.save_as)
        self.context_menu.add_checkbutton(label="Read-Only", command=self.toggle_read_only)
        self.bind("<Button-3>", self.show_context_menu)

    def show_context_menu(self, event):
        self.context_menu.post(event.x_root, event.y_root)

    def cut_text(self):
        self.terminal_display.event_generate("<<Cut>>")

    def copy_text(self):
        self.terminal_display.event_generate("<<Copy>>")

    def paste_text(self):
        self.terminal_display.event_generate("<<Paste>>")

    def save_as(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".txt",
                                                 filetypes=[("Text files", "*.txt"),
                                                            ("All files", "*.*")])
        if file_path:
            with open(file_path, 'w') as file:
                file.write(self.terminal_display.get("1.0", tk.END))

    def toggle_read_only(self):
        current_state = self.terminal_display.cget('state')
        new_state = 'normal' if current_state == 'disabled' else 'disabled'
        self.terminal_display.config(state=new_state)

    def create_system_metrics(self):
        self.ram_label = tk.Label(self.bottom_left_frame, text="RAM Usage: ")
        self.swap_label = tk.Label(self.bottom_left_frame, text="SWAP Usage: ")
        self.cpu_label = tk.Label(self.bottom_left_frame, text="CPU Usage: ")
        self.disk_label = tk.Label(self.bottom_left_frame, text="Disk Usage: ")
        self.network_label = tk.Label(self.bottom_left_frame, text="Network Usage: ")
        self.locked_label = tk.Label(self.bottom_left_frame, text="")

        self.ram_label.pack(anchor='w')
        self.swap_label.pack(anchor='w')
        self.cpu_label.pack(anchor='w')
        self.disk_label.pack(anchor='w')
        self.network_label.pack(anchor='w')
        self.locked_label.pack(anchor='w')

    def update_metrics_periodically(self):
        def update_metrics():
            while True:
                self.update_metrics()
                time.sleep(5)

        threading.Thread(target=update_metrics, daemon=True).start()

    def update_metrics(self):
        ram = psutil.virtual_memory()
        swap = psutil.swap_memory()
        cpu = psutil.cpu_percent(interval=1)
        disk = psutil.disk_usage('/')
        network = psutil.net_io_counters()

        self.ram_label.config(text=f"RAM Usage: {ram.percent}%")
        self.swap_label.config(text=f"SWAP Usage: {swap.percent}%")
        self.cpu_label.config(text=f"CPU Usage: {cpu}%")
        self.disk_label.config(text=f"Disk Usage: {disk.percent}%")
        self.network_label.config(text=f"Network Usage: Sent={network.bytes_sent}, Received={network.bytes_recv}")

        self.check_process_lock()

    def get_password(self):
        try:
            # Prompt the user for their password
            self.password = simpledialog.askstring("Password", "Enter your password:", show='*')
            if self.password is not None:
                # Verify the password without causing the terminal to exit
                process = subprocess.Popen(["sudo", "-S", "echo", "root access granted"], stdin=subprocess.PIPE, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
                output, error = process.communicate(input=self.password + '\n')
                if process.returncode != 0:
                    logging.error(f"Error getting root access: {error}")
                    messagebox.showerror("Error", f"Error getting root access: {error}")
                else:
                    print(output)
        except Exception as e:
            logging.error(f"Error getting password: {e}")
            messagebox.showerror("Error getting password: {e}")

    def check_process_lock(self):
        for proc in psutil.process_iter():
            try:
                if proc.name() == "apt":
                    self.locked_label.config(text="Locked by Process")
                    return
            except psutil.NoSuchProcess:
                continue
        self.locked_label.config(text="")

    def create_buttons(self):
        buttons_info = [
            ("Autoremove", "sudo apt-get autoremove"),
            ("Clean", "sudo apt-get clean"),
            ("List Packages", "dpkg -l"),  # Corrected command for listing packages
            ("Dist Upgrade", "sudo apt-get dist-upgrade"),
            ("Deborphan", "sudo apt-get install deborphan && deborphan"),  # Install deborphan if not installed
            ("Update & Upgrade", "sudo apt-get update && sudo apt-get upgrade -y"),
            ("Install -f", "sudo apt-get install -f"),
            ("Check", "sudo apt-get check"),
            ("Purge", "sudo apt-get purge"),
            ("Autoclean", "sudo apt-get autoclean"),
            ("Build Dependencies", "sudo apt-get build-dep <package>"),  # Argument-dependent
            ("Source", "sudo apt-get source <package>"),  # Argument-dependent
            ("Changelog", "sudo apt-get changelog"),
            ("Download", "sudo apt-get download <package>"),  # Argument-dependent
            ("Reinstall", "sudo apt-get install --reinstall <package>")  # Argument-dependent
        ]

        row = 0
        col = 0

        for (text, command) in buttons_info:
            if "<package>" in command:
                button = tk.Button(self.bottom_right_frame, text=text, command=lambda cmd=command: self.open_argument_window(cmd))
            else:
                button = tk.Button(self.bottom_right_frame, text=text, command=lambda cmd=command: self.run_command_with_text(cmd))
            button.grid(row=row, column=col, padx=5, pady=5, sticky="ew")
            col += 1
            if col == 5:
                col = 0
                row += 1

    def run_command_with_text(self, command_text):
        self.run_command(command_text)

    def open_argument_window(self, command_template):
        arg_window = Toplevel(self)
        arg_window.title("Enter Arguments")
        arg_window.geometry("300x100")
        arg_window.attributes('-topmost', True)
        arg_window.grab_set()  # Make sure it grabs focus

        arg_label = tk.Label(arg_window, text="Enter package name:")
        arg_label.grid(row=0, column=0, padx=5, pady=5)

        arg_entry = tk.Entry(arg_window)
        arg_entry.grid(row=0, column=1, padx=5, pady=5)

        enter_button = tk.Button(arg_window, text="Enter", command=lambda: self.apply_argument(command_template, arg_entry.get(), arg_window))
        enter_button.grid(row=1, column=0, columnspan=2, padx=5, pady=5)

    def apply_argument(self, command_template, argument, window):
        if argument:
            command = command_template.replace("<package>", argument)
            self.run_command_with_text(command)
            window.destroy()

if __name__ == '__main__':
    app = TerminalEmulator()
    app.mainloop()
