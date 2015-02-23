#!/usr/bin/env python
# -*- coding: utf-8 -*-

from general import x
import sys

DUPLICATE_POLICY_CHANGE_FIRST = 0
DUPLICATE_POLICY_CHANGE_LAST = 1
DUPLICATE_POLICY_REMOVE_DUPLICATES = 2


def aug_remove(path):
    return x("augtool rm \"%s\"" % path)


def aug_set(path, value):
    """
    Util function for safely set config settings using augeas. This function sets the specified value and also verifies
    that it was set successfully since augeas sometimes silently fails to :store data.

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


def aug_set_enhanced(enhanced_path, value, duplicate_policy=DUPLICATE_POLICY_REMOVE_DUPLICATES):
    """
    Wraps around aug_set adding the following features:

    Supports referencing numbered nodes by their value
    Syntax: <augeas-path>[{<node-value>}]<continued-path>

    Allows specifying a duplicate policy for what action to take if the fully resolved augeas path has several nodes

    Example referencing service[sssd] node of /etc/sssd/sssd.conf:
    /files/etc/sssd/sssd.conf/target[{sssd}]/services
    """

    resolved_path = _resolve_enhanced_path(enhanced_path)

    #Check for duplicates
    all_results = find_aug_entries(resolved_path)
    if len(all_results) <= 1:
        #No duplicates, just do a normal set
        aug_set(resolved_path, value)
    elif duplicate_policy == DUPLICATE_POLICY_CHANGE_FIRST:
        aug_set(all_results[0], value)
    elif duplicate_policy == DUPLICATE_POLICY_CHANGE_LAST:
        aug_set(all_results[len(all_results) - 1], value)
    elif duplicate_policy == DUPLICATE_POLICY_REMOVE_DUPLICATES:
        aug_set(all_results[0], value)
        #Remove remaining results, should be safest to start with the last in case indices are affected by removal
        for to_remove in reversed(all_results[1:]):
            aug_remove(to_remove)


def find_aug_entry_by_name(search_path, name):
    """

    :param searchPath: the augeas path to search for example /files/etc/nsswitch.conf/database where there are many
                       numbered database entries
    :param name:       the name of the subentry to return the path for
    :return:           the augeas path to the found entry
    """
    results = find_aug_entries(search_path, name)

    if len(results) > 0:
        return results[0]

    return None


def find_aug_entries(search_path, name=None):
    """

    :param searchPath: the augeas path to search for example /files/etc/nsswitch.conf/database where there are many
                       numbered database entries
    :param name:       the name of the subentry to return the path for, if not set all nodes matching this path are
                        returned
    :return:           list of augeas paths
    """
    lines = x("augtool match %s" % search_path).split("\n")
    result = []
    for line in lines:
        if line.strip() == "(no matches)":
            #No matches found, return the empty list
            return result
        if line.strip() == "":
            #Ignore empty lines
            continue
        split_line = line.split("=", 1)
        value = split_line[1].strip()
        if name is None or value == name:
            result.append(split_line[0].strip())

    return result


def _resolve_enhanced_path(enhanced_path):
    remainder = enhanced_path
    resolved_path = ""
    while "[{" in remainder:
        first = remainder.split("[{", 1)
        search_path = resolved_path + first[0]
        second = first[1].split("}]", 1)
        value = second[0]
        remainder = second[1]
        resolved_path = find_aug_entry_by_name(search_path, value)

    if remainder != "":
        resolved_path += remainder

    return resolved_path
