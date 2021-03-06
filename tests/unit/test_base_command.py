import logging
import os
import time

from pip._internal.cli.base_command import Command


class FakeCommand(Command):
    name = 'fake'
    summary = name

    def __init__(self, error=False):
        self.error = error
        super(FakeCommand, self).__init__()

    def main(self, args):
        args.append("--disable-pip-version-check")
        return super(FakeCommand, self).main(args)

    def run(self, options, args):
        logging.getLogger("pip.tests").info("fake")
        if self.error:
            raise SystemExit(1)


class FakeCommandWithUnicode(FakeCommand):
    name = 'fake_unicode'
    summary = name

    def run(self, options, args):
        logging.getLogger("pip.tests").info(b"bytes here \xE9")
        logging.getLogger("pip.tests").info(
            b"unicode here \xC3\xA9".decode("utf-8")
        )


class Test_base_command_logging(object):
    """
    Test `pip.base_command.Command` setting up logging consumers based on
    options
    """

    def setup(self):
        self.old_time = time.time
        time.time = lambda: 1547704837.4
        # Robustify the tests below to the ambient timezone by setting it
        # explicitly here.
        self.old_tz = getattr(os.environ, 'TZ', None)
        os.environ['TZ'] = 'UTC'
        # time.tzset() is not implemented on some platforms (notably, Windows).
        if hasattr(time, 'tzset'):
            time.tzset()

    def teardown(self):
        if self.old_tz:
            os.environ['TZ'] = self.old_tz
        else:
            del os.environ['TZ']
        if 'tzset' in dir(time):
            time.tzset()
        time.time = self.old_time

    def test_log_command_success(self, tmpdir):
        """
        Test the --log option logs when command succeeds
        """
        cmd = FakeCommand()
        log_path = tmpdir.join('log')
        cmd.main(['fake', '--log', log_path])
        with open(log_path) as f:
            assert f.read().rstrip() == '2019-01-17T06:00:37 fake'

    def test_log_command_error(self, tmpdir):
        """
        Test the --log option logs when command fails
        """
        cmd = FakeCommand(error=True)
        log_path = tmpdir.join('log')
        cmd.main(['fake', '--log', log_path])
        with open(log_path) as f:
            assert f.read().startswith('2019-01-17T06:00:37 fake')

    def test_log_file_command_error(self, tmpdir):
        """
        Test the --log-file option logs (when there's an error).
        """
        cmd = FakeCommand(error=True)
        log_file_path = tmpdir.join('log_file')
        cmd.main(['fake', '--log-file', log_file_path])
        with open(log_file_path) as f:
            assert f.read().startswith('2019-01-17T06:00:37 fake')

    def test_unicode_messages(self, tmpdir):
        """
        Tests that logging bytestrings and unicode objects don't break logging
        """
        cmd = FakeCommandWithUnicode()
        log_path = tmpdir.join('log')
        cmd.main(['fake_unicode', '--log', log_path])
