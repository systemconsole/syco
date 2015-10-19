#!/usr/bin/env python
"""
Main file for executing syco commands.

syco is a command line shell, used to execute customized installation scripts
for linux services and softwares.

Examples:
syco install-syco

"""

__author__ = "daniel.lindh@cybercow.se"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["Mattias Hemmingsson"]
__license__ = "???"
__version__ = "0.1"
__status__ = "Production"

import sys
import os
from optparse import OptionParser

#
# Adding file directories for inclusions.
#

# Common classes/functions that are used by the project.
sys.path.insert(0, sys.path[0] + "/common/")

import app
import version
import general
general.require_linux_user("root")

# Files published to public repos.
sys.path.append(app.SYCO_PUBLIC_PATH)

#  Import all py files including syco commands.
command_dir = os.listdir(app.SYCO_PUBLIC_PATH)

# Files only available in private user repos.
for plugin_path in app.get_syco_plugin_paths("/bin/"):
    sys.path.append(plugin_path)
    if os.path.isdir(plugin_path):
        command_dir += os.listdir(plugin_path)

for module in command_dir:
    if (module == '__init__.py' or
            module[-4:] == '.pyc' or
            module[-3:] == '.sh' or
            module[-3:] == 'led'):
        continue
    module = module.replace('.py', '')
    py_command = module + "=__import__(\"" + module + "\", locals(), globals())"
    exec py_command


class Commands:
    """
    Control which command line commands that can be executed.

    """

    class CommandList:
        """
        Stores added commands for a specific type [public|private}

        """
        name_list = {}
        func_list = {}
        arguments_list = {}
        help_list = {}
        password_list = {}

        def __init__(self):
            self.name_list = {}
            self.func_list = {}
            self.arguments_list = {}
            self.help_list = {}
            self.password_list = {}

    # Lists of all public and private commands
    commands = {"public": CommandList(), "private": CommandList}

    # The command type add() will add to.
    current_type = "public"

    # The maximum char length of name + argument
    name_length = 0

    def add(self, name, func, arguments="", help="", password_list=[]):
        """
        Add a command that are able to be executed from the syco command line.

        This is a callback function used by the modules.

        """
        self.commands[self.current_type].name_list[name] = name.lower()
        self.commands[self.current_type].func_list[name] = func
        self.commands[self.current_type].arguments_list[name] = arguments.strip("[]")
        self.commands[self.current_type].password_list[name] = password_list
        if self.commands[self.current_type].arguments_list[name]:
            self.commands[self.current_type].arguments_list[name] = "{" + \
                self.commands[self.current_type].arguments_list[name] + "}"

        self.commands[self.current_type].help_list[name] = help.rstrip(".") + "."

        self.name_length = max(self.name_length, len(name))

    def execute(self, args):
        """
        Execute a command in a module.

        """
        command = args[0].lower()

        if command in self.commands["public"].name_list:
            self.commands["public"].func_list[command](args)
        elif command in self.commands["private"].name_list:
            self.commands["private"].func_list[command](args)
        else:
            app.parser.error('Unknown command %s' % command)

    def get_command_passwords(self, command):
        """
        Get a list of all passwords registered with this command
        """
        if command in self.commands["public"].name_list:
            return self.commands["public"].password_list[command]
        elif command in self.commands["private"].name_list:
            return self.commands["private"].password_list[command]
        else:
            app.parser.error('Unknown command %s' % command)

    def get_help(self):
        """
        Get the full help text for all commands.

        """
        help = ""
        help += "Public commands\n"
        help += self._get_help_for_command_type("public")
        help += "\nUser commands:\n"
        help += self._get_help_for_command_type("private")
        return help

    def _get_help_for_command_type(self, type):
        """
        Build help string for one command type (public or private)

        """
        help = ""
        name_list = sorted(self.commands[type].name_list)
        for name in name_list:
            help += self.commands[type].name_list[name].ljust(self.name_length) + " - "
            help += self.commands[type].help_list[name] + " " + self.commands[type].arguments_list[name] + "\n"

        return help

    def __init__(self):
        """
        Read command directories (public and private) and add commands.

        """

        self.current_type = "public"
        for obj in self._get_modules(app.SYCO_PUBLIC_PATH):
            try:
                obj.build_commands(self)
            except AttributeError, e:
                app.print_error("   Problem with obj, error:: " + repr(e.args))
            except NameError, e:
                app.print_error("   Problem with " + repr(obj) + ", error: " + repr(e.args))

        self.current_type = "private"
        for plugin_path in app.get_syco_plugin_paths("/bin/"):
            for obj in self._get_modules(plugin_path):
                try:
                    obj.build_commands(self)
                except AttributeError, e:
                    app.print_error("   Problem with obj, error:: " + repr(e.args))
                except NameError, e:
                    app.print_error("   Problem with " + repr(obj) + ", error: " + repr(e.args))

    def _get_modules(self, commands_path):
        """
        Return a list of objects representing all available syco modules in specified folder.

        """
        modules = []
        if os.path.isdir(commands_path):
            for module in os.listdir(commands_path):
                if (module == '__init__.py' or
                        module[-4:] == '.pyc' or
                        module[-3:] == '.sh' or
                        module[-3:] == 'led'):
                    continue
                module = module.replace('.py', '')
                obj = getattr(sys.modules[__name__], module)
                modules.append(obj)

        return modules


def main():
    """
    Used to control the command line options, and the execution of the script.

    First function called when using the script.

    """
    # Module variables
    cmd_list = Commands()

    usage = "usage: %prog [options] command\n\n"
    usage += "Commands:\n"
    usage += cmd_list.get_help()

    app.parser = OptionParser(usage=usage, version="System Console " + app.version, add_help_option=True)
    app.parser.add_option("-v", "--verbose", action="store_const", const=2, dest="verbose", default=1,
                          help="Show more output.")
    app.parser.add_option("-q", "--quiet",   action="store_const", const=0, dest="verbose", help="Show no output.")
    app.parser.add_option("-f", "--force",   action="store_const", const=1, dest="force", default=0,
                          help="Ignore version.cfg.")

    (app.options, args) = app.parser.parse_args()

    app.print_verbose(app.parser.get_version())

    if len(args) < 1 and 2 > len(args):
        app.parser.print_help()
    else:
        try:
            cmd_list.execute(args)
        except version.VersionException, e:
            app.print_error(repr(e.args))

if __name__ == "__main__":
    main()
