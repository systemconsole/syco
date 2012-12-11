import ConfigParser
import os
import re
import subprocess

from constant import BOLD, RESET
import app
import config


#
# Globals/Module variables
#

# The default status that will be set if a tests succeeds. OR or WARNING
test_default_status = None

# The status of a completed section, ERROR, WARNING or OK. If all test succeeds
# this will be set to the same value as test_default_status.
test_status = None

#
# Helper functions
#

def x(command, output = False):
    if output:
        print(BOLD + "Command: " + RESET + command)

    p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (stdout, stderr) = p.communicate()
    result = "%s%s" % (stdout, stderr)

    if output:
        print result

    if result:
        return result.strip().split("\n")
    else:
        return ['']


def _get_verbose():
    return app.options.verbose


def _set_status(status = None):
    global test_default_status, test_status
    if status:
        test_status = status
    else:
        test_status = test_default_status

def _is_status(status):
    global test_status
    return status == test_status


def _set_default_status(default_status):
    global test_default_status
    test_default_status = default_status

#
# Print methods
#


def print_header(txt):
    print_status()
    _set_default_status('OK')

    sections = txt.partition(" ")
    if sections[2]:
        section_number = sections[0]
        section_txt = sections[2]

    print(section_number.ljust(7, " ")),
    print(section_txt.ljust(80, " ")),


total_status = {}
def print_status():
    global test_status, total_status
    if test_status:
        print(test_status)

        if test_status not in total_status:
            total_status[test_status] = 1
        else:
            total_status[test_status] += 1

        test_status = None
    else:
        print


def print_total_status():
    print_status()
    global total_status
    total = 0
    print
    print "="*100
    for test_status, number in total_status.iteritems():
        print "{0:<8} {1}".format(test_status, number)
        total += number
    print "{0:<8} {1}".format("TOTAL", total)


def print_message(txt, prefix):
    if _get_verbose() <= 1:
        return

    print_status()

    import textwrap
    txt_list = textwrap.wrap("%s" % txt, 70)
    print "      %s - %s" % (prefix, txt_list[0])
    for row in txt_list[1:]:
        print ("             %s".ljust(len(prefix), " ")) % row


def print_info(txt):
    '''
    Prints an in info message related to a check.

    The method call must be executed after all checks.

    '''
    print_message(txt, "INFO")


def print_warning(txt):
    _set_default_status('WARNING')
    _set_status()
    print_message(txt, "WARNING")


def view_output(cmd):
    _set_status()
    if _get_verbose() <= 1:
        return
    print_status()
    print "%s%s%s" % (BOLD, cmd, RESET)
    print
    print "="*80
    print "\n".join(x(cmd))
    print "="*80
    print


#
# Private comparsion functions
#

def assert_true(should_be_true):
    if should_be_true:
        _set_status()
    else:
        _set_status('ERROR')


def assert_contains(haystack, needle):
    if haystack:
        if needle not in haystack:
            _set_status('ERROR')

    _set_status()


def assert_contains_re(haystack, needle):
    prog = re.compile(needle)
    if not prog.search(haystack):
        _set_status('ERROR')
    else:
        _set_status()


#
# Check methods
#

def check_equal(cmd, expected):
    for row in x(cmd):
        assert_contains(row, expected)


def check_equals(cmd, expected):
    result = x(cmd)
    assert_true(len(result) == len(expected))
    if not _is_status('ERROR'):
        for row in range(0, len(result)):
            if expected[row]:
                assert_contains(result[row], expected[row])


def check_equal_re(cmd, expected):
    for row in x(cmd):
        assert_contains_re(row, expected)


def check_empty(cmd):
    _set_status('ERROR')
    for row in x(cmd):
        if len(row.strip()) == 0:
            _set_status()


def check_not_empty(cmd):
    _set_status('ERROR')
    for row in x(cmd):
        if len(row.strip()) > 0:
            _set_status()


def check_return_code(cmd, expected):
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert_true(p.wait() == expected)
