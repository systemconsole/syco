#!/usr/bin/env python
# -*- coding: utf-8 -*-

from general import x
import sys


def aug_set(path, value):
    """
    Util function for safely set config settings using augeas. This function sets the specified value and also verifies
    that it was set successfully since augeas sometimes silently fails to store data.

    Alternative to current algorithm: script augeas interactive mode since failure to save with one-liners seems to
     work when in interactive mode and followed by the "save" command explicitly.

    :param path: the augeas path to the setting to set
    :param value: the value to set
    :return: the result from the sudo() invocation
    """
    result = x("augtool set \"%s\" \"%s\"" % (path, value))

    match_result = str(x("augtool match \"%s\"" % path))
    match_value = match_result.split("=", 1)[1].strip()

    if str(match_value) != value:
        print("Augeas error: detected value \"%s\"differed from that which was set \"%s\"" % (match_value, value))
        sys.exit(0)

    return result


def aug_set_enhanced(enhanced_path, value):
    """
    Wraps around aug_set adding the following features:

    Supports referencing numbered nodes by their value
    Syntax: <augeas-path>[{<node-value>}]<continued-path>

    Example referencing service[sssd] node of /etc/sssd/sssd.conf:
    /files/etc/sssd/sssd.conf/target[{sssd}]/services
    """
    return aug_set(_resolve_enhanced_path(enhanced_path), value)

def find_aug_entry_by_name(search_path, name):
    """

    :param searchPath: the augeas path to search for example /files/etc/nsswitch.conf/database where there are many
                       numbered database entries
    :param name:       the name of the subentry to return the path for
    :return:           the augeas path to the found entry
    """
    lines = x("augtool match %s" % search_path).split("\n")
    for line in lines:
        split_line = line.split("=")
        value = split_line[1].strip()
        if value == name:
            return split_line[0].strip()


def _resolve_enhanced_path(enhanced_path):
    remainder = enhanced_path
    resolved_path = ""
    while "{[" in remainder:
        first = remainder.split("[{", 1)
        search_path = resolved_path + first[0]
        second = first[1].split("}]", 1)
        value = second[0]
        remainder = second[1]
        resolved_path = find_aug_entry_by_name(search_path, value)

    if remainder != "":
        resolved_path += remainder

    return resolved_path
