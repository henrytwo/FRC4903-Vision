import time
from networktables import NetworkTables

# To see messages from networktables, you must setup logging
import logging

def changeListener(key, value, isNew):

    #print(key, value, isNew)

    if key == '/Vision/getTime':
        table.putNumber('time', time.time())

logging.basicConfig(level=logging.DEBUG)

NetworkTables.initialize()
NetworkTables.addEntryListener(changeListener)

table = NetworkTables.getTable("Vision")

smell = False

while True:

    if smell:
        command = 'sniff'
    else:
        command = input('Enter command> ')

    if command == 'scanon':
        table.putNumber('enabled', 1)
    elif command == 'scanoff':
        table.putNumber('enabled', 0)
    elif command == 'sniff':
        print('\n\nEnabled: %s\nLast updated: %s\nHeading: %s\nLocked: %s\nLatency: %fms\nDeviation: %i\nTime diff: %fms\n\n' % ('TRUE' if table.getNumber('enabled', 0) else 'FALSE',table.getNumber('lastUpdated', 'N/A'), str(int(table.getNumber('heading', 9000))) if table.getNumber('heading', 9000) != 9000 else 'N/A', 'TRUE' if table.getNumber('locked', 0) else 'FALSE', 1000 * table.getNumber('offset', 0), table.getNumber('deviation', -1), 1000 * (time.time() - table.getNumber('lastUpdated', 999999))))
    elif command == 'smell':
        smell = True
    else:
        print('Invalid instruction')