#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

DUPLICATE_POLICY_CHANGE_FIRST = 0
DUPLICATE_POLICY_CHANGE_LAST = 1
DUPLICATE_POLICY_REMOVE_DUPLICATES = 2


class Augeas:

    execute_function = None

    def __init__(self, execute_function):
        self.execute_function = execute_function

    def has_value(self, path, expected_value):
        values = self.find_values(path)
        for value in values:
            if value == expected_value:
                return True
        return False

    def ins(self, path):
        return self._execute("augtool ins %s" % path)

    def remove(self, path):

        entries = self.find_entries(path)
        if len(entries) == 0:
            print "Could not find node: %s, cancelling rm action" % path
            return None

        return self._execute("augtool rm \"%s\"" % path)

    def set(self, path, value):
        """
        Util function for safely set config settings using augeas. This function sets the specified value and also verifies
        that it was set successfully since augeas sometimes silently fails to :store data.

        Alternative to current algorithm: script augeas interactive mode since failure to save with one-liners seems to
         work when in interactive mode and followed by the "save" command explicitly.

        :param path: the augeas path to the setting to set
        :param value: the value to set
        :return: the result from the sudo() invocation
        """
        result = self._execute("augtool set \"%s\" \"%s\"" % (path, value))

        match_result = str(self._execute("augtool match \"%s\"" % path))
        match_value = match_result.split("=", 1)[1].strip()

        if str(match_value) != value:
            print("Augeas error: detected value \"%s\"differed from that which was set \"%s\"" % (match_value, value))
            sys.exit(0)

        return result

    def set_enhanced(self, path, value, duplicate_policy=DUPLICATE_POLICY_REMOVE_DUPLICATES):
        """
        Wraps around aug_set adding the following features:

        Supports referencing numbered nodes by their value
        Syntax: <augeas-path>[{<node-value>}]<continued-path>

        Allows specifying a duplicate policy for what action to take if the fully resolved augeas path has several nodes

        Example referencing service[sssd] node of /etc/sssd/sssd.conf:
        /files/etc/sssd/sssd.conf/target[{sssd}]/services
        """

        #Check for duplicates
        all_results = self.find_entries(path)
        if len(all_results) <= 1:
            #No duplicates, just do a normal set
            self.set(path, value)
        elif duplicate_policy == DUPLICATE_POLICY_CHANGE_FIRST:
            self.set(all_results[0], value)
        elif duplicate_policy == DUPLICATE_POLICY_CHANGE_LAST:
            self.set(all_results[len(all_results) - 1], value)
        elif duplicate_policy == DUPLICATE_POLICY_REMOVE_DUPLICATES:
            self.set(all_results[0], value)
            #Remove remaining results, should be safest to start with the last in case indices are affected by removal
            for to_remove in reversed(all_results[1:]):
                self.remove(to_remove)

    def find_entry(self, search_path):
        """

        :param search_path: the augeas path to search for example /files/etc/nsswitch.conf/database where there are many
                           numbered database entries
        :return:           the augeas path to the found entry
        """
        results = self.find_entries(search_path)

        if len(results) > 0:
            return results[0]

        return None

    def find_entries(self, search_path):
        """

        :param search_path: the augeas path to search for example /files/etc/nsswitch.conf/database where there are many
                           numbered database entries
        :return:           list of augeas paths
        """

        lines = self._search(search_path)

        result = []
        for line in lines:
            result.append(line.split("=", 1)[0].strip())

        return result

    def find_values(self, search_path):
        """

        :param search_path: the augeas path to search for example /files/etc/nsswitch.conf/database where there are many
                           numbered database entries
        :return:           list of augeas values matching the search path
        """
        lines = self._search(search_path)

        result = []
        for line in lines:
            print line
            result.append(line.split("=", 1)[1].strip())

        return result

    def _execute(self, cmd):
        return self.execute_function(cmd)

    def _search(self, path):

        lines = self._execute("augtool match \"%s\"" % path).split("\n")
        result = []

        for line in lines:
            print line
            if line.strip() == "(no matches)":
                #No matches found, return the empty list
                return result
            if line.strip() == "":
                #Ignore empty lines
                continue
            if "=" not in line:
                #Ignore any random output that is not augeas output of format <path> = <value>
                continue

            result.append(line)

        return result