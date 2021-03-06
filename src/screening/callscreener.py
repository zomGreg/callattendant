#!/usr/bin/python
# -*- coding: UTF-8 -*-
#
#  callscreener.py
#
#  Copyright 2018  <pi@rhombus1>
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.


from blacklist import Blacklist
from whitelist import Whitelist
from nomorobo import NomoroboService
from pprint import pprint
import re
import sys
import os


class CallScreener(object):
    '''The CallScreener provides provides blacklist and whitelist checks'''

    def is_whitelisted(self, callerid):
        '''Returns true if the number is on a whitelist'''
        return self._whitelist.check_number(callerid['NMBR'])

    def is_blacklisted(self, callerid):
        '''Returns true if the number is on a blacklist'''
        number = callerid['NMBR']
        name = callerid["NAME"]
        block = self.config.get_namespace("BLOCK_")
        try:
            if self._blacklist.check_number(number):
                print("Caller is blacklisted")
                return True
            else:
                print("Checking blocked CID patterns...")
                for key in block["name_patterns"].keys():
                    match = re.search(key, name)
                    if match:
                        print("CID blocked name pattern detected")
                        reason = block["name_patterns"][key]
                        return True
                for key in block["number_patterns"].keys():
                    match = re.search(key, number)
                    if match:
                        print("CID blocked number pattern detected")
                        reason = block["number_patterns"][key]
                        return True
                print("Checking nomorobo...")
                result = self._nomorobo.lookup_number(number)
                if result["spam"]:
                    print("Caller is robocaller")
                    self.blacklist_caller(callerid, "{} with score {}".format(result["reason"], result["score"]))
                    return True
                print("Caller has been screened")
                return False
        finally:
            sys.stdout.flush()

    def whitelist_caller(self, callerid, reason):
        self._whitelist.add_caller(callerid, reason)

    def blacklist_caller(self, callerid, reason):
        self._blacklist.add_caller(callerid, reason)

    def __init__(self, db, config):
        self._db = db
        self.config = config
        if self.config["DEBUG"]:
            print("Initializing CallScreener")

        self._blacklist = Blacklist(db, config)
        self._whitelist = Whitelist(db, config)
        self._nomorobo = NomoroboService()

        if self.config["DEBUG"]:
            print("CallScreener initialized")


def test(db, config):
    """ Unit Tests """

    print("*** Running CallScreener Unit Tests ***")

    # Create the screener to be tested
    screener = CallScreener(db, config)

    # Add a record to the blacklist
    caller1 = {"NAME": "caller1", "NMBR": "1234567890", "DATE": "1012", "TIME": "0600"}
    screener._blacklist.add_caller(caller1)
    # Add a record to the whitelist
    caller2 = {"NAME": "caller2", "NMBR": "1111111111", "DATE": "1012", "TIME": "0600", "REASON": "Test"}
    screener._whitelist.add_caller(caller2)
    # Create a V123456789012345 Telemarketer caller
    caller3 = {"NAME": "V123456789012345", "NMBR": "80512345678", "DATE": "1012", "TIME": "0600"}
    # Create a robocaller
    caller4 = {"NAME": "caller4", "NMBR": "3105241189", "DATE": "1012", "TIME": "0600"}
    # Create a Private Number
    caller5 = {"NAME": "caller5", "NMBR": "P", "DATE": "1012", "TIME": "0600"}

    # Perform tests
    try:
        print("Assert is blacklisted: " + caller1['NMBR'])
        assert screener.is_blacklisted(caller1), "caller1 should be blocked"

        print("Assert not is whitelisted: " + caller1['NMBR'])
        assert not screener.is_whitelisted(caller1), "caller1 should not be permitted"

        print("Assert not is blacklisted: " + caller2['NMBR'])
        assert not screener.is_blacklisted(caller2), "caller2 should not be blocked"

        print("Assert is whitelisted: " + caller2['NMBR'])
        assert screener.is_whitelisted(caller2), "caller2 should be permitted"

        print("Assert a blocked name pattern: " + caller3['NAME'])
        assert screener.is_blacklisted(caller3), "caller3 should be blocked by name pattern"

        print("Assert is blacklisted by nomorobo: " + caller4['NMBR'])
        assert screener.is_blacklisted(caller4), "caller4 should be blocked by nomorobo"

        print("Assert a blocked number pattern: " + caller5['NMBR'])
        assert screener.is_blacklisted(caller5), "caller1 should be blocked by number pattern"


    except AssertionError as e:

        print("*** Unit test FAILED ***")
        pprint(e)
        return 1

    print("*** Unit tests PASSED ***")
    return 0


if __name__ == '__main__':
    """ Run Unit Tests """

    # Add the parent directory to the path so callattendant can be found
    import os
    import sys
    currentdir = os.path.dirname(os.path.realpath(__file__))
    parentdir = os.path.dirname(currentdir)
    sys.path.append(parentdir)

    # Load and tweak the default config
    from callattendant import make_config, print_config
    config = make_config()
    config['DEBUG'] = True
    config['BLOCK_NAME_PATTERNS'] = {
        "V[0-9]{15}": "Telemarketer Caller ID",
    }
    config['BLOCK_NUMBER_PATTERNS'] = {
        "P": "Private number",
    }
    print_config(config)

    # Create the test db in RAM
    import sqlite3
    db = sqlite3.connect(":memory:")

    sys.exit(test(db, config))
    print("Done")
