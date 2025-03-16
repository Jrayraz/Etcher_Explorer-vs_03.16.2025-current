import subprocess
import sys
import logging
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QMessageBox
from PySide6.QtCore import QTimer, QThread, Signal

class CommandThread(QThread):
    output = Signal(str)

    def __init__(self, command):
        super().__init__()
        self.command = command

    def run(self):
        process = subprocess.Popen(self.command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                self.output.emit(output.strip())
            QThread.msleep(100)  # Sleep for 100ms to prevent excessive CPU usage

class GPUMonAPP(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("GPU Monitor")
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet("background-color: lightblue;")

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout(self.central_widget)

        self.text_area = QTextEdit()
        self.text_area.setStyleSheet("background-color: lemonchiffon;")
        self.layout.addWidget(self.text_area)

        self.button_layout = QHBoxLayout()
        self.layout.addLayout(self.button_layout)

        self.create_button("GPU Device", "lspci -vnn | grep VGA")
        self.create_button("Performance", "radeontop", use_terminal=True)
        self.create_button("GPU/Display", "sudo lshw -C display")
        self.create_button("OpenGL", "glxinfo | grep -i opengl")
        self.create_button("Health", "sudo dmesg | grep -i 'gpu\\|radeon' && sudo journal -xe | grep -i 'gpu\\|radeon'")

        self.current_thread = None
        self.current_command = None
        
        # Timer for GUI updates
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_gpu_info)
        self.timer.start(5000)  # Update every 5 seconds

        # Run the program with GPU acceleration if available
        if self.is_gpu_accelerated():
            print("GPU acceleration is enabled.")
        else:
            print("GPU acceleration is not enabled.")

    def create_button(self, label, command, use_terminal=False):
        button = QPushButton(label)
        button.setStyleSheet("background-color: orange;")
        if use_terminal:
            button.clicked.connect(lambda: self.open_new_terminal(command))
        else:
            button.clicked.connect(lambda: self.run_command(command))
        self.button_layout.addWidget(button)

    def open_new_terminal(self, command):
        try:
            subprocess.Popen(['alacritty', '-e', 'bash', '-c', f"{command}; exec bash"])
        except Exception as e:
            QMessageBox.information(self, "Error", f"Error opening terminal: {e}")
            logging.error(f"Error opening terminal: {e}")

    def run_command(self, command):
        if self.current_thread:
            self.current_thread.terminate()

        self.current_command = f"DRI_PRIME=1 {command}"
        self.current_thread = CommandThread(self.current_command)
        self.current_thread.output.connect(self.update_text_area)
        self.current_thread.start()

    def update_text_area(self, output):
        self.text_area.append(output)

    def update_gpu_info(self):
        if self.current_command and "radeontop" not in self.current_command:
            result = subprocess.run(self.current_command, capture_output=True, text=True, shell=True)
            self.update_text_area(result.stdout)

    def is_gpu_accelerated(self):
        try:
            result = subprocess.run("DRI_PRIME=1 glxinfo | grep -i opengl", capture_output=True, text=True, shell=True)
            return "OpenGL" in result.stdout
        except Exception as e:
            return False

    def show_no_gpu_message(self):
        QMessageBox.information(self, "Error", "No compatible GPU found or required tools are not installed.\n"
                                                "For NVIDIA, try: sudo apt-get install nvidia-driver\n"
                                                "For AMD, try: sudo apt-get install radeon-top mesa-utils")

if __name__ == "__main__":
    app = QApplication(sys.argv)

    main_window = GPUMonAPP()
    main_window.show()

    try:
        sys.exit(app.exec())
    except SystemExit:
        pass

