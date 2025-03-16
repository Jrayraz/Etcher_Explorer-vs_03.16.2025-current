import os
import sys
import json
from PySide6.QtWidgets import (QApplication, QMainWindow, QScrollArea, QVBoxLayout, QWidget, QLabel, QPushButton, QLineEdit, QMenu, QDialog, QFormLayout, QHBoxLayout, QSizePolicy)
from PySide6.QtCore import Qt
import logging
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.fernet import Fernet
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import psutil
import signal
from gpg_manager import GPGManager
from keyring_manager import KeyringManager
import keyring

# Enable GPU acceleration
os.environ["QT_OPENGL"] = "angle"

# Configure logging
logging.basicConfig(filename='pass_save.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class PassSave(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PassSave")
        self.setGeometry(100, 100, 600, 400)

        self.secrets_dir = os.path.join(os.getcwd(), ".config/.secrets")
        self.keys_dir = os.path.join(os.getcwd(), ".config/.keys")
        os.makedirs(self.keys_dir, exist_ok=True)
        os.makedirs(self.secrets_dir, exist_ok=True)

        self.key = None

        self.gpg_manager = GPGManager()
        self.keyring_manager = KeyringManager()

        self.initUI()
        self.load_key()
        self.dekrypt_directory(self.secrets_dir)
        self.load_system_keyrings()  # Ensure system keyrings are loaded first
        self.load_accounts()
        self.fetch_secrets()

    def initUI(self):
        self.centralWidget = QWidget()
        self.setCentralWidget(self.centralWidget)

        self.layout = QVBoxLayout(self.centralWidget)

        self.scrollArea = QScrollArea(self)
        self.scrollArea.setWidgetResizable(True)
        self.scrollContent = QWidget()
        self.scrollLayout = QVBoxLayout(self.scrollContent)
        self.scrollContent.setLayout(self.scrollLayout)
        self.scrollArea.setWidget(self.scrollContent)

        self.layout.addWidget(self.scrollArea)

        # Add "+" button
        self.addButton = QPushButton("+", self)
        self.addButton.setFixedSize(40, 40)
        self.addButton.clicked.connect(self.showAddMenu)
        
        # Add red "x" button
       # self.closeButton = QPushButton("x", self)
       # self.closeButton.setFixedSize(40, 40)
       # self.closeButton.setStyleSheet("QPushButton { color: red; }")
       # self.closeButton.clicked.connect(self.closeApplication)

        self.buttonLayout = QHBoxLayout()
        self.buttonLayout.addWidget(self.addButton)
#        self.buttonLayout.addWidget(self.closeButton)
        self.layout.addLayout(self.buttonLayout)

    def showAddMenu(self):
        menu = QMenu(self)
        
        actions = {
            "Online Account": "Online Account",
            "Bank Card": "Bank Card",
            "Membership Card": "Membership Card",
            "Driver's License": "Driver's License",
            "PIN": "PIN",
            "Passcode": "Passcode",
            "SSN": "SSN",
            "Contact": "Contact",
            "GPG Key": "GPG Key"
        }
        
        for action_text, account_type in actions.items():
            action = menu.addAction(action_text)
            action.triggered.connect(lambda _, at=account_type: self.openAddAccountDialog(at))
            
        menu.exec(self.addButton.mapToGlobal(self.addButton.rect().bottomLeft()))

    def openAddAccountDialog(self, account_type):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Add {account_type}")
        layout = QFormLayout(dialog)

        inputs = []

        name_input = QLineEdit(dialog)
        layout.addRow("Name:", name_input)
        inputs.append(name_input)

        if account_type == "Online Account":
            email_input = QLineEdit(dialog)
            username_input = QLineEdit(dialog)
            secret_input = QLineEdit(dialog)
            business_input = QLineEdit(dialog)
            website_input = QLineEdit(dialog)
            
            layout.addRow("Name:", name_input)
            layout.addRow("Email:", email_input)
            layout.addRow("Username:", username_input)
            layout.addRow("Secret:", secret_input)
            layout.addRow("Business:", business_input)
            layout.addRow("Website:", website_input)
            
            inputs.extend([email_input, username_input, secret_input, business_input, website_input])
        
        elif account_type == "Driver's License":
            expiration_input = QLineEdit(dialog)
            number_input = QLineEdit(dialog)
            
            layout.addRow("Name:", name_input)
            layout.addRow("Expiration:", expiration_input)
            layout.addRow("Number:", number_input)
            
            inputs.extend([expiration_input, number_input])
        
        elif account_type == "Bank Card":
            card_owner_input = QLineEdit(dialog)
            expiration_input = QLineEdit(dialog)
            card_number_input = QLineEdit(dialog)
            issuer_input = QLineEdit(dialog)
            cvc_input = QLineEdit(dialog)
            pin_input = QLineEdit(dialog)
            
            layout.addRow("Name:", name_input)
            layout.addRow("Name on Card:", card_owner_input)
            layout.addRow("Expiration:", expiration_input)
            layout.addRow("Card Number:", card_number_input)
            layout.addRow("Issuer:", issuer_input)
            layout.addRow("CVC:", cvc_input)
            layout.addRow("PIN:", pin_input)

            inputs.extend([card_owner_input, expiration_input, card_number_input, issuer_input, cvc_input, pin_input])

        elif account_type == "Membership Card":
            issuer_input = QLineEdit(dialog)
            number_input = QLineEdit(dialog)
            
            layout.addRow("Name:", name_input)
            layout.addRow("Issuer:", issuer_input)
            layout.addRow("Number:", number_input)
            
            inputs.extend([issuer_input, number_input])
        
        elif account_type == "SSN":
            number_input = QLineEdit(dialog)
            
            layout.addRow("Name:", name_input)
            layout.addRow("Number:", number_input)

            inputs.extend([number_input])
        
        elif account_type in ["PIN", "Passcode"]:
            type_input = QLineEdit(dialog)
            passcode_input = QLineEdit(dialog)
            
            layout.addRow("Name:", name_input)
            layout.addRow("Type:", type_input)
            layout.addRow(f"{account_type}:", passcode_input)

            inputs.extend([type_input, passcode_input])
        
        elif account_type == "Contact":
            work_phone_input = QLineEdit(dialog)
            home_phone_input = QLineEdit(dialog)
            cell_phone_input = QLineEdit(dialog)
            address_input = QLineEdit(dialog)
            position_input = QLineEdit(dialog)
            company_input = QLineEdit(dialog)
            email_input = QLineEdit(dialog)
            
            layout.addRow("Name:", name_input)
            layout.addRow("Work Phone:", work_phone_input)
            layout.addRow("Home Phone:", home_phone_input)
            layout.addRow("Cell Phone:", cell_phone_input)
            layout.addRow("Address:", address_input)
            layout.addRow("Position:", position_input)
            layout.addRow("Company:", company_input)
            layout.addRow("Email:", email_input)

            inputs.extend([work_phone_input, home_phone_input, cell_phone_input, address_input, position_input, company_input, email_input])
        elif account_type == "GPG Key":
                realname_input = QLineEdit(dialog)
                email_input = QLineEdit(dialog)
                
                layout.addRow("Real Name:", realname_input)
                layout.addRow("Email:", email_input)
                
                inputs.extend([realname_input, email_input])    

        save_button = QPushButton("Save", dialog)
        save_button.clicked.connect(lambda: self.saveNewAccount(account_type, inputs, dialog))
        layout.addRow("", save_button)
        dialog.setLayout(layout)
        dialog.exec()

    def saveNewAccount(self, account_type, inputs, dialog):
        account = {"Type": account_type}

        # Adjust for capturing the 'Name', 'Realname', and 'Email' fields
        name = inputs[0].text()
        realname = inputs[1].text() if len(inputs) > 1 else ""
        email = inputs[2].text() if len(inputs) > 2 else ""

        if account_type == "Online Account":
            account.update({
                "Name": name,
                "Email": email,
                "Realname": realname,
                "Secret": inputs[3].text() if len(inputs) > 3 else "",
                "Business": inputs[4].text() if len(inputs) > 4 else "",
                "Website": inputs[5].text() if len(inputs) > 5 else ""
            })
        elif account_type == "Driver's License":
            account.update({
                "Name": name,
                "Expiration": inputs[1].text() if len(inputs) > 1 else "",
                "Number": inputs[2].text() if len(inputs) > 2 else ""
            })
        elif account_type == "Bank Card":
            account.update({
                "Name": name,
                "Name on Card": inputs[1].text() if len(inputs) > 1 else "",
                "Expiration": inputs[2].text() if len(inputs) > 2 else "",
                "Card Number": inputs[3].text() if len(inputs) > 3 else "",
                "Issuer": inputs[4].text() if len(inputs) > 4 else "",
                "CVC": inputs[5].text() if len(inputs) > 5 else "",
                "PIN": inputs[6].text() if len(inputs) > 6 else ""
            })
        elif account_type == "Membership Card":
            account.update({
                "Name": name,
                "Issuer": inputs[1].text() if len(inputs) > 1 else "",
                "Number": inputs[2].text() if len(inputs) > 2 else ""
            })
        elif account_type == "SSN":
            account.update({
                "Name": name,
                "Number": inputs[1].text() if len(inputs) > 1 else ""
            })
        elif account_type in ["PIN", "Passcode"]:
            account.update({
                "Name": name,
                "Type": inputs[1].text() if len(inputs) > 1 else "",
                account_type: inputs[2].text() if len(inputs) > 2 else ""
            })
        elif account_type == "Contact":
            account.update({
                "Name": name,
                "Work Phone": inputs[1].text() if len(inputs) > 1 else "",
                "Home Phone": inputs[2].text() if len(inputs) > 2 else "",
                "Cell Phone": inputs[3].text() if len(inputs) > 3 else "",
                "Address": inputs[4].text() if len(inputs) > 4 else "",
                "Position": inputs[5].text() if len(inputs) > 5 else "",
                "Company": inputs[6].text() if len(inputs) > 6 else "",
                "Email": email
            })
        elif account_type == "GPG Key":
            self.create_gpg_key(realname, email)  # Use realname for creating GPG key
            account.update({
                "Name": name,
                "Realname": realname,
                "Email": email
            })

        # Ensure the 'Name' key exists in the account dictionary
        account_name = account.get("Name")
        if not account_name:
            # Handle the case where the 'Name' field is missing or empty
            print("Error: 'Name' field is missing or empty.")
            return

        # Save the account details to the appropriate location (e.g., secrets directory)
        account_file_path = os.path.join(self.secrets_dir, f"{account_name}.json")
        with open(account_file_path, 'w') as file:
            json.dump(account, file)

        self.addAccountWidget(account_name, account)
        dialog.accept()

    def addAccountWidget(self, account_name, account):
        widget = QWidget()
        widget.setFixedHeight(60)  # Set the fixed height for account widget
        layout = QHBoxLayout(widget)
        
        account_label = QLabel(f"{account_name}", self)
        layout.addWidget(account_label)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layout.addWidget(spacer)
        
        view_button = QPushButton("View", self)
        view_button.clicked.connect(lambda: self.viewAccountDetails(account_name, account))
        layout.addWidget(view_button)
        
        widget.setLayout(layout)
        self.scrollLayout.addWidget(widget)


    def viewAccountDetails(self, account_name, account):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"{account_name} Details")
        
        layout = QFormLayout(dialog)
        for key, value in account.items():
            if value is None:
                value = ""  # Set default value for None
            layout.addRow(f"{key}:", QLabel(str(value), dialog))
        
        if account["Type"] == "GPG Key":
            export_button = QPushButton("Export", dialog)
            export_button.clicked.connect(lambda: self.export_gpg_key(account_name))
            layout.addRow(export_button)

        edit_button = QPushButton("Edit", dialog)
        edit_button.clicked.connect(lambda: self.editAccountDetails(account_name, account, dialog))
        layout.addRow(edit_button)
        
        dialog.exec()

    def editAccountDetails(self, account_name, account, dialog):
        dialog.close()
        
        edit_dialog = QDialog(self)
        edit_dialog.setWindowTitle(f"Edit {account_name}")
        
        layout = QFormLayout(edit_dialog)
        inputs = {}
        for key, value in account.items():
            input_field = QLineEdit(edit_dialog)
            input_field.setText(value)
            layout.addRow(f"{key}:", input_field)
            inputs[key] = input_field
        
        save_button = QPushButton("Save", edit_dialog)
        save_button.clicked.connect(lambda: self.saveEditedAccount(account_name, inputs, edit_dialog))
        layout.addRow(save_button)
        
        edit_dialog.exec()

    def saveEditedAccount(self, account_name, inputs, dialog):
        account = {key: input_field.text() for key, input_field in inputs.items()}
        
        account_file_path = os.path.join(self.secrets_dir, f"{account_name}.json")
        
        with open(account_file_path, 'w') as file:
            json.dump(account, file)
        
        dialog.accept()
        self.refreshAccountWidgets()

    def refreshAccountWidgets(self):
        logging.debug("Refreshing account widgets.")
        # Clear existing widgets
        for i in reversed(range(self.scrollLayout.count())):
            widget = self.scrollLayout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        
        # Load and display updated account widgets
        for filename in os.listdir(self.secrets_dir):
            if filename.endswith(".json"):
                account_name = filename[:-5]  # Remove .json extension
                account_file_path = os.path.join(self.secrets_dir, filename)
                
                try:
                    with open(account_file_path, 'r', encoding='utf-8') as file:
                        account = json.load(file)
                    self.addAccountWidget(account_name, account)
                except (UnicodeDecodeError, json.JSONDecodeError) as e:
                    logging.error(f"Error loading {account_file_path}: {e}")

        # Display system keyrings
        self.display_system_keyrings()

    def create_key(self):
        try:
            self.key = AESGCM.generate_key(bit_length=256)
            self.save_key()
            logging.info("Key created and saved successfully.")
        except Exception as e:
            logging.error(f"An error occurred during key creation: {e}")

    def save_key(self):
        try:
            if not self.key:
                logging.error("No key to save. Please create a key first.")
                return
            salt = os.urandom(16)
            kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100000, backend=default_backend())
            key = base64.urlsafe_b64encode(kdf.derive(b"password"))  # Replace 'password' with actual password logic
            fernet = Fernet(key)
            encrypted_key = fernet.encrypt(self.key)
            file_path = os.path.join(self.keys_dir, 'pass_save.key')
            with open(file_path, 'wb') as file:
                file.write(salt)
                file.write(encrypted_key)
            logging.info("Key saved successfully.")
        except Exception as e:
            logging.error(f"Failed to save key: {e}")

    def load_system_keyrings(self):
        services = self.keyring_manager.get_services()
        for service in services:
            usernames = self.keyring_manager.get_usernames(service)
            for username in usernames:
                password = self.keyring_manager.get_password(service, username)
                self.display_account(service, username, password)
                logging.info(f"Service: {service}, Username: {username}, Password: {password}")

    def load_key(self):
        file_path = os.path.join(self.keys_dir, 'pass_save.key')
        if not os.path.exists(file_path):
            self.create_key()
        else:
            try:
                with open(file_path, 'rb') as file:
                    salt = file.read(16)
                    encrypted_key = file.read()
                kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100000, backend=default_backend())
                key = base64.urlsafe_b64encode(kdf.derive(b"password"))  # Replace 'password' with actual password logic
                fernet = Fernet(key)
                self.key = fernet.decrypt(encrypted_key)
                logging.info("Key loaded successfully.")
            except Exception as e:
                logging.error(f"Failed to load key: {e}")

    def encrypt(self, data):
        nonce = os.urandom(12)
        aesgcm = AESGCM(self.key)
        encrypted_data = aesgcm.encrypt(nonce, data, None)
        return nonce + encrypted_data

    def decrypt(self, encrypted_data):
        nonce = encrypted_data[:12]
        ciphertext = encrypted_data[12:]
        aesgcm = AESGCM(self.key)
        try:
            return aesgcm.decrypt(nonce, ciphertext, None)
        except Exception as e:
            logging.error(f"Error decrypting data: {e}")
            raise

    def krypt_directory(self, dir_path):
        try:
            for root, dirs, files in os.walk(dir_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    with open(file_path, 'rb') as f:
                        data = f.read()
                    encrypted_data = self.encrypt(data)
                    with open(file_path + '.krypt', 'wb') as f:
                        f.write(encrypted_data)
                    os.remove(file_path)
            logging.info("Directory encrypted successfully.")
        except Exception as e:
            logging.error(f"An error occurred during directory encryption: {e}")

    def dekrypt_directory(self, dir_path):
        try:
            for root, dirs, files in os.walk(dir_path):
                for file in files:
                    if file.endswith('.krypt'):
                        file_path = os.path.join(root, file)
                        with open(file_path, 'rb') as f:
                            encrypted_data = f.read()
                        decrypted_data = self.decrypt(encrypted_data)
                        new_file_path = file_path.replace('.krypt', '')
                        with open(new_file_path, 'wb') as f:
                            f.write(decrypted_data)
                        os.remove(file_path)
            logging.info("Directory decrypted successfully.")
        except Exception as e:
            logging.error(f"An error occurred during directory decryption: {e}")

    def load_accounts(self):
        logging.debug("Loading accounts.")
        self.refreshAccountWidgets()
        self.load_gpg_keys()
        self.load_system_keyrings()

    def load_gpg_keys(self):
        self.gpg_keys = self.gpg_manager.list_keys()
        logging.info(f"Loaded GPG keys: {self.gpg_keys}")

    def create_gpg_key(self, name, email):
        key = self.gpg_manager.create_gpg_key(name, email)
        logging.info(f"Created GPG key: {key}")

    def save_to_keyring(self, service, username, password):
        self.keyring_manager.save_password(service, username, password)
        logging.info(f"Saved password to keyring for service: {service}, username: {username}")

    def get_from_keyring(self, service, username):
        password = self.keyring_manager.get_password(service, username)
        logging.info(f"Retrieved password from keyring for service: {service}, username: {username}")
        return password

    def export_gpg_key(self, key_id):
        self.gpg_manager.export_key(key_id)
        logging.info(f"Exported GPG key: {key_id}")

    def load_system_keyrings(self):
        self.system_keyrings = {}
        for backend in keyring.backend.get_all_keyring():
            try:
                for service in backend.get_services():
                    self.system_keyrings[service] = []
                    for username in backend.get_usernames(service):
                        password = self.keyring_manager.get_password(service, username)
                        self.system_keyrings[service].append((username, password))
            except AttributeError:
                pass
        self.display_system_keyrings()

    def display_system_keyrings(self):
        for service, credentials in self.system_keyrings.items():
            service_label = QLabel(f"Service: {service}", self)
            self.scrollLayout.addWidget(service_label)
            for username, password in credentials:
                credential_label = QLabel(f"Username: {username}, Password: {password}", self)
                self.scrollLayout.addWidget(credential_label)
# pass_save.py

    def fetch_secrets(self):
        # Load system keyrings
        services = self.keyring_manager.get_services()
        for service in services:
            usernames = self.keyring_manager.get_usernames(service)
            for username in usernames:
                password = self.keyring_manager.get_password(service, username)
                # Display the credentials in the UI using addAccountWidget
                account_name = f"{service}-{username}"
                account = {"Service": service, "Username": username, "Password": password, "Type": "System Keyring"}
                self.addAccountWidget(account_name, account)

        # Load secrets from the secrets directory
        self.load_secrets(self.secrets_dir)

    def load_secrets(self, directory):
        for root, _, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                with open(file_path, 'r') as f:
                    secret_data = f.read()
                    service, username, password = self.parse_secret(secret_data)
                    account_name = f"{service}-{username}"
                    account = {"Service": service, "Username": username, "Password": password, "Type": "Secret"}
                    self.addAccountWidget(account_name, account)

    def parse_secret(self, secret_data, add_account_widget=True):
        # Implement the logic to parse secret data with error handling
        lines = secret_data.splitlines()
        
        try:
            service = lines[0].split(": ")[1]
            username = lines[1].split(": ")[1]
            password = lines[2].split(": ")[1]
        except IndexError as e:
            logging.error(f"Error parsing secret data: {e}")
            return None, None, None

        if add_account_widget:
            account_name = f"{service}-{username}"
            account = {"Service": service, "Username": username, "Password": password, "Type": "Secret"}
            self.addAccountWidget(account_name, account)
        
        return service, username, password

    def closeEvent(self, event):
        super().closeEvent(event)
        self.krypt_directory(self.secrets_dir)
        event.accept()
        # Find the parent terminal process and terminate it
        parent_pid = psutil.Process(os.getpid()).ppid()
        os.kill(parent_pid, signal.SIGTERM)
        self.destroy()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PassSave()
    window.show()
    sys.exit(app.exec())











