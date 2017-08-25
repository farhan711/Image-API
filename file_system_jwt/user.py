import hashlib
import os
from django.conf import settings
from django.contrib.auth.validators import ASCIIUsernameValidator
from django.forms import Field


class User:
    class Meta:
        username = Field(label="username", validators=(ASCIIUsernameValidator,))

    def __init__(self, username):
        self.username = username
        self.user_folder = os.path.join(settings.BASE_DIR, 'files', self.username)
        self.image_folder = os.path.join(self.user_folder, 'images')

    def is_valid(self):
        """find user folder and return True/False along"""
        if os.path.isdir(self.user_folder):
            return True
        return False

    def create(self, **credentials):
        """setup user folder and write password to <user_folder>/.user"""
        if 'password' not in credentials:
            return False
        try:
            if not os.path.isdir(self.user_folder):
                os.mkdir(self.user_folder)
            if not os.path.isdir(self.image_folder):
                os.mkdir(self.image_folder)
            return self.set_password(credentials['password'])
        except FileNotFoundError:
            "failed to create a folder for user"
            return False

    def authenticate(self, password):
        if not self.is_valid():
            return False
        password_hash = hashlib.sha224(password.encode()).hexdigest()
        with open(os.path.join(self.user_folder, ".user"), 'rb') as config:
            if password_hash.encode() == config.read():
                return True
            return False

    def set_password(self, password):
        """write password to <user_folder>/.user"""
        if self.is_valid():
            password_hash = hashlib.sha224(password.encode()).hexdigest()
            with open(os.path.join(self.user_folder, ".user"), 'wb') as config:
                config.write(password_hash.encode())
                return True
        return False


def get_user(username):
    user = User(username)
    if user.is_valid():
        return user
    return None

def authenticate(**credentials):
    if not('username' in credentials and 'password' in credentials):
        return None
    user = get_user(credentials['username'])
    if user.is_valid() and  user.authenticate(credentials['password']):
        return user
    return None