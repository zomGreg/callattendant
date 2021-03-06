
# This code was inspired by and contains code snippets from Pradeep Singh:
# https://iotbytes.wordpress.com/incoming-call-details-logger-with-raspberry-pi/
# https://github.com/pradeesi/Incoming_Call_Detail_Logger
# ==============================================================================

import utils
from datetime import datetime
from pprint import pprint


class CallLogger(object):

    def log_caller(self, callerid):
        query = """INSERT INTO CallLog(
            Name,
            Number,
            Date,
            Time,
            SystemDateTime)
            VALUES(?,?,?,?,?)"""
        arguments = [callerid['NAME'],
                     callerid['NMBR'],
                     datetime.strptime(callerid['DATE'], '%m%d'). strftime('%d-%b'),
                     datetime.strptime(callerid['TIME'], '%H%M'). strftime('%I:%M %p'),
                     (datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3])]

        self.db.execute(query, arguments)
        self.db.commit()

        query = "select last_insert_rowid()"
        result = utils.query_db(self.db, query, (), True)
        call_no = result[0]

        if self.config["DEBUG"]:
            print("> New call log entry #{}".format(call_no))
            pprint(arguments)

        return call_no

    def __init__(self, db, config):
        self.db = db
        self.config = config

        if self.config["DEBUG"]:
            print("Initializing CallLogger")

        # Create the Call_History table if it does not exist
        sql = """CREATE TABLE IF NOT EXISTS CallLog (
            CallLogID INTEGER PRIMARY KEY AUTOINCREMENT,
            Name TEXT,
            Number TEXT,
            Date TEXT,
            Time TEXT,
            SystemDateTime TEXT);"""

        curs = self.db.cursor()
        curs.executescript(sql)
        curs.close()

        if self.config["DEBUG"]:
            print("CallLogger initialized")


def test(db, config):
    ''' Unit Tests '''
    print("*** Running Whitelist Unit Tests ***")

    import utils

    # Create the logger to be tested
    logger = CallLogger(db, config)

    # Caller to be added
    callerid = {"NAME": "Bruce", "NMBR": "1234567890", "DATE": "1012", "TIME": "0600"}

    print("Adding caller:")
    pprint(callerid)

    try:
        print("Assert log_caller returns #1")
        assert logger.log_caller(callerid) == 1, "call # should be 1"

        print("Assert log_caller returns #2")
        assert logger.log_caller(callerid) == 2, "call # should be 2"

        # List the records
        query = "SELECT * FROM CallLog"
        results = utils.query_db(db, query)
        print(query + " results:")
        pprint(results)

    except AssertionError as e:
        print("*** Unit Test FAILED ***")
        pprint(e)
        return 1

    print("*** Unit Tests PASSED ***")
    return 0


if __name__ == '__main__':
    '''
    Run the unit tests
    '''
    # Create the test db in RAM
    import sqlite3
    db = sqlite3.connect(":memory:")

    # Add the parent directory to the path so callattendant can be found
    import os
    import sys
    currentdir = os.path.dirname(os.path.realpath(__file__))
    parentdir = os.path.dirname(currentdir)
    sys.path.append(parentdir)

    # Create and tweak a default config suitable for unit testing
    from callattendant import make_config, print_config
    config = make_config()
    config['DEBUG'] = True
    print_config(config)

    # Run the tests
    sys.exit(test(db, config))

    print("Tests complete")
