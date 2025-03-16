import gnupg
import logging

class GPGManager:
    def __init__(self):
        self.gpg = gnupg.GPG()

    def create_gpg_key(self, realname, email):
        input_data = self.gpg.gen_key_input(name_real=realname, name_email=email)
        key = self.gpg.gen_key(input_data)
        logging.info(f"Created GPG key: {key}")
        return key

    def list_keys(self):
        keys = self.gpg.list_keys()
        logging.info(f"Loaded GPG keys: {keys}")
        return keys

    def export_key(self, key_id):
        key_data = self.gpg.export_keys(key_id)
        with open(f"{key_id}.asc", 'w') as f:
            f.write(key_data)
        logging.info(f"Exported GPG key: {key_id}")
