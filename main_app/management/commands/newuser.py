"""
Management utility to create user.
"""
from __future__ import unicode_literals

import getpass
import sys

from django.conf import settings
from django.contrib.auth.management import get_default_username
from django.core import exceptions
from django.core.management.base import BaseCommand, CommandError
from django.utils.encoding import force_str
from django.utils.six.moves import input
from django.utils.text import capfirst


class NotRunningInTTYException(Exception):
    pass


class UserCreationFailed(Exception):
    pass


class Command(BaseCommand):
    help = 'Used to create a user.'
    requires_migrations_checks = False

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        self.User = settings.USER_CLASS
        self.username = "username"
        self.username_field = self.User.Meta.username

    def add_arguments(self, parser):
        parser.add_argument(
            '--%s' % self.username,
            dest=self.username, default=None,
            help='Specifies the login for the user.',
        )
        parser.add_argument(
            '--noinput', '--no-input',
            action='store_false', dest='interactive', default=True,
            help=(
                'Tells Django to NOT prompt the user for input of any kind. '
                'You must use --%s with --noinput, along with an option for '
                'any other required field. Users created with --noinput will '
                'not be able to log in until they\'re given a valid password.' %
                self.username
            ),
        )

    def execute(self, *args, **options):
        self.stdin = options.get('stdin', sys.stdin)  # Used for testing
        return super(Command, self).execute(*args, **options)

    def handle(self, *args, **options):
        username = options[self.username]
        password = None
        user_data = {}
        # Do quick and dirty validation if --noinput
        if not options['interactive']:
            if not username:
                raise CommandError("You must use --%s with --noinput." % self.username)
        else:
            # Prompt for username and password
            # Enclose this whole thing in a try/except to catch
            # KeyboardInterrupt and exit gracefully.
            default_username = get_default_username()
            try:

                if hasattr(self.stdin, 'isatty') and not self.stdin.isatty():
                    raise NotRunningInTTYException("Not running in a TTY")

                # Get a username
                verbose_field_name = "Username: "
                while username is None:
                    input_msg = capfirst(verbose_field_name)
                    if default_username:
                        input_msg += " (leave blank to use '%s')" % default_username
                    username = self.get_input_data(self.username_field, input_msg, default_username)
                    self.User = settings.USER_CLASS(username)
                    if not username:
                        continue
                    self.User.username = username
                    if self.User and self.User.is_valid():
                        self.stderr.write("Error: That %s is already taken." % verbose_field_name)
                        username = None

                # Get a password
                while password is None:
                    password = getpass.getpass()
                    password2 = getpass.getpass(force_str('Password (again): '))
                    if password != password2:
                        self.stderr.write("Error: Your passwords didn't match.")
                        password = None
                        # Don't validate passwords that don't match.
                        continue

                    if password.strip() == '':
                        self.stderr.write("Error: Blank passwords aren't allowed.")
                        password = None
                        # Don't validate blank passwords.
                        continue

            except KeyboardInterrupt:
                self.stderr.write("\nOperation cancelled.")
                sys.exit(1)

            except NotRunningInTTYException:
                self.stdout.write(
                    "User creation skipped due to not running in a TTY. "
                    "You can run `manage.py createuser` in your project "
                    "to create one manually."
                )

        if username:
            self.User = settings.USER_CLASS(username)
            user_data['password'] = password
            if not self.User.create(**user_data):
                raise UserCreationFailed("User creation failed....")
            if options['verbosity'] >= 1:
                self.stdout.write("User created successfully.")

    def get_input_data(self, field, message, default=None):
        """
        Override this method if you want to customize data inputs or
        validation exceptions.
        """
        raw_value = input(message)
        if default and raw_value == '':
            raw_value = default
        try:
            val = field.clean(raw_value)
        except exceptions.ValidationError as e:
            self.stderr.write("Error: %s" % '; '.join(e.messages))
            val = None

        return val
