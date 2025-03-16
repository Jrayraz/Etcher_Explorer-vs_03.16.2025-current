import keyring
import logging

class KeyringManager:
    def save_password(self, service, username, password):
        keyring.set_password(service, username, password)
        logging.info(f"Saved password to keyring for service: {service}, username: {username}")

    def get_password(self, service, username):
        password = keyring.get_password(service, username)
        logging.info(f"Retrieved password from keyring for service: {service}, username: {username}")
        return password

    def get_services(self):
        services = set()
        for backend in keyring.backend.get_all_keyring():
            try:
                services.update(backend.get_services())
            except AttributeError:
                pass
        return list(services)

    def get_usernames(self, service):
        usernames = set()
        for backend in keyring.backend.get_all_keyring():
            try:
                usernames.update(backend.get_usernames(service))
            except AttributeError:
                pass
        return list(usernames)
