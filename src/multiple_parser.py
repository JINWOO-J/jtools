#!/usr/bin/env python3
import re, sys
from datetime import datetime
import argparse
import subprocess
import calendar


first_line = re.compile(r'^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) \| (?P<severity>[^ ]*) \| (?P<logger>[^ ]*) \| (?P<location>[^ ]*) \|.*$')
stack_trace_end = re.compile(r'^(?P<exception>[a-zA-Z]\w*)(:.*)?$')


def parse_date(date: str):
    # return calendar.timegm(datetime.strptime(date, '%m%d %H:%M:%S,%f').timetuple())
    # date = f'2019{date}'
    return datetime.strptime(date, '%Y-%m-%d %H:%M:%S,%f')


def delete_last_lines(n=1):
    CURSOR_UP_ONE = '\x1b[1A'
    ERASE_LINE = '\x1b[2K'
    for _ in range(n):
        sys.stdout.write(CURSOR_UP_ONE)
        sys.stdout.write(ERASE_LINE)


class MultilineParser(object):
    ''' Possible parser state transitions:

    looking_for_start -> looking_for_start:
      * Line doesn't start with a timestamp
      * Line starts with a timestamp and isn't severity ERROR (emits point)

    looking_for_start -> find_stack_trace_start:
      * Line starts with a timestamp and is severity ERROR

    find_stack_trace_start -> find_stack_trace_start
      * Line doesn't start with "Traceback"
      * Line starts with a timestamp (resets state data)

    find_stack_trace_start -> find_stack_trace_end
      * Line starts with "Traceback"

    find_stack_trace_end -> find_stack_trace_start
      * Line starts with a timestamp (resets state data)

    find_stack_trace_end -> looking_for_start
      * Line looks like end of the stack trace (emits point, resets state)
    '''

    def __init__(self, *args, **kwargs):
        self.state = self.looking_for_start
        self.data = {}


    def parse_line(self, line):
        'Entry point to the log parser'
        return self.state(line)

    def looking_for_start(self, line):
        ''' Initial state of the parser. Will match lines starting with
            a timestamp. If it sees that the log message was of ERROR
            severity, transition to the `find_stack_trace_start` state,
            otherwise, return a metric point for the line.
        '''
        global first_line
        match = first_line.match(line)
        if match:
            data = match.groupdict()
            severity = data.get('severity')
            if severity == 'ERROR':
                self.data = match.groupdict()
                self.state = self.find_stack_trace_start
            elif severity is not None:
                return (
                    'logs.%s.%s' % (data.get('logger'), severity.lower()),
                    parse_date(data.get('timestamp')),
                    1,
                    {'metric_type': 'counter'}
                )

    def find_stack_trace_start(self, line):
        ''' Find the start of the stack trace. If found, transition to
            `find_stack_trace_end`. If a line beginning with a timestamp
            is found first, then reset the state machine.
        '''
        if line.startswith('Traceback'):
            self.state = self.find_stack_trace_end
        else:
            self.looking_for_start(line)

    def find_stack_trace_end(self, line):
        ''' Find the end of the stack trace. If found, return a metric point
            tagged with the type of exception and transition to the
            `looking_for_start` state again. If a line beginning with a
            timestamp is found first, then reset the state machine.
        '''
        global stack_trace_end
        match = stack_trace_end.match(line)
        if match:
            exception = match.group('exception')
            output = (
                'logs.%s.%s' % (self.data.get('logger'), self.data.get('severity').lower()),
                parse_date(self.data.get('timestamp')),
                1,
                {'metric_type': 'counter',
                 'tags': ['exception:%s' % exception]}
            )
            self.data = {}
            self.state = self.looking_for_start
            return output
        else:
            self.looking_for_start(line)


def get_parser():
    parser = argparse.ArgumentParser(description='Change peer_id to hostname in the loopchain log file')
    # positional argument for command
    parser.add_argument('command', nargs='?', help='cat, tail', default="cat")
    parser.add_argument('--logfile', metavar='logfile', help=f'log file', default="/app/prep/data/loopchain/log/loopchain.channel.icon_dex.log")
    return parser


def dump(obj, nested_level=0, output=sys.stdout):
    class bcolors:
        HEADER = '\033[95m'
        OKBLUE = '\033[94m'
        OKGREEN = '\033[92m'
        WARNING = '\033[93m'
        FAIL = '\033[91m'
        ENDC = '\033[0m'
        BOLD = '\033[1m'
        UNDERLINE = '\033[4m'

    spacing = '   '
    def_spacing = '   '
    if type(obj) == dict:
        print ('%s{' % ( def_spacing + (nested_level) * spacing ))
        for k, v in obj.items():
            if hasattr(v, '__iter__'):
                print ( bcolors.OKGREEN + '%s%s:' % (def_spacing +(nested_level + 1) * spacing, k) + bcolors.ENDC, end="")
                dump(v, nested_level + 1, output)
            else:
                print ( bcolors.OKGREEN + '%s%s:' % (def_spacing + (nested_level + 1) * spacing, k) + bcolors.WARNING + ' %s' % v + bcolors.ENDC, file=output)
        print ('%s}' % ( def_spacing + nested_level * spacing), file=output)
    elif type(obj) == list:
        print  ('%s[' % (def_spacing+ (nested_level) * spacing), file=output)
        for v in obj:
            if hasattr(v, '__iter__'):
                dump(v, nested_level + 1, output)
            else:
                print ( bcolors.WARNING + '%s%s' % ( def_spacing + (nested_level + 1) * spacing, v) + bcolors.ENDC, file=output)
        print ('%s]' % ( def_spacing + (nested_level) * spacing), file=output)
    else:
        print (bcolors.WARNING + '%s%s' %  ( def_spacing + nested_level * spacing, obj) + bcolors.ENDC)


def test():
    sample_log = """2020-12-30 00:01:57,131 588 140200854329088 hxd9e8a1 icon_dex DEBUG    [epoch.py:set_epoch_leader:86] height(743328) leader_id(hx8573a132f3df5c34a292fc16cb33737ffe10b367)
2020-12-30 00:01:57,131 588 140200854329088 hxd9e8a1 icon_dex DEBUG    [epoch.py:new_round:60] new round 0, 0

2020-12-30 00:01:09,478 588 140200862721792 hxd9e8a1 icon_dex DEBUG    [rest_client.py:call_async:146] REST call async complete method_name(node_getBlockByHeight)
2020-12-30 00:01:09,479 588 140200862721792 hxd9e8a1 icon_dex DEBUG    [block_sync.py:_request_completed:338] block_height(743175) received
2020-12-30 00:01:09,479 588 140200862721792 hxd9e8a1 icon_dex DEBUG    [block_sync.py:_citizen_request:373] request heights: odict_keys([743176]), size: 1
2020-12-30 00:01:09,479 588 140200862721792 hxd9e8a1 icon_dex DEBUG    [block_sync.py:_block_sync:477] try add block height: 743175
2020-12-30 00:01:09,479 588 140200862721792 hxd9e8a1 icon_dex DEBUG    [block_sync.py:_block_sync:484] max_height: 5910020, max_block_height: 5910020, unconfirmed_block_height: -1, confirm_info count: 22
2020-12-30 00:01:09,480 588 140200854329088 hxd9e8a1 icon_dex DEBUG    [block_sync.py:_add_block_by_sync:582] height(743175) hash(Hash32(0xfe071ecdc5ad0699f8debdf6fa13415a3334cb78bb8c2a589787309a7e90f651))
2020-12-30 00:01:09,501 588 140200854329088 hxd9e8a1 icon_dex DEBUG    [blockchain.py:prevent_next_block_mismatch:732] next_height: 743175

"""

    # first_line = re.compile(r'^(?P<timestamp>\d{2}\d{2} \d{2}:\d{2}:\d{2},\d{3}) (?P<pid>\d+) (?P<thread_id>\d+) (?P<peer_id>\w{8}) (?P<channel>\w+) (?P<level>[^ ]*) (?P<file>[^ ]*) (?P<message>.*)$')
    first_line = re.compile(r'^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) (?P<pid>\d+) (?P<thread_id>\d+) (?P<peer_id>\w{8}) '
                            # r'(?P<channel>\w+) (?P<level>[^ ]*) (?P<file>[^ ]*) (?P<message>.*)$')
                            r'(?P<channel>\w+) (?P<level>[^ ]\w+) (\s+) \[(?P<file>.*)\] (?P<message>.*)$')
    vote_line = re.compile(r'^(?P<vote>[a-zA-Z]\w*)(\s+)(:(?P<state>.*))?$')
    find_vote = {}

    for line in sample_log.split("\n"):
        match = first_line.match(line)
        if match:
            data = match.groupdict()
            if "Votes : Votes" in data.get('message'):
                find_vote = data
                print(f"\n{find_vote['timestamp']}", end=" ")
            else:
                dump(data)

        else:
            match = vote_line.match(line)
            if match:
                data = match.groupdict()
                data['timestamp'] = find_vote.get("timestamp")
                if "/" in data.get('state'):
                    vote_state = data.get('state').split("/")
                    data['vote_count'] = vote_state[0]
                    data['vote_total'] = vote_state[1]
                data['pretty_date'] = parse_date(find_vote.get("timestamp"))
                print(f"{data['vote']}: {vote_state[0]}/{vote_state[1]} ", end=", ")


if __name__ == '__main__':
    # test()
    parser = get_parser()
    args = parser.parse_args()
    result = {}
    total_count = 0
    if args.command == "cat":
        f = subprocess.Popen(['cat', args.logfile],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        first_line = re.compile(r'^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) (?P<pid>\d+) (?P<thread_id>\d+) (?P<peer_id>\w{8}) '                                
                                r'(?P<channel>\w+) (?P<level>[^ ]\w+) (\s+) \[(?P<file>.*):(?P<function>.*):(?P<line>.*)\] (?P<message>.*)$')
        for line in f.stdout:
            line = line.decode("utf-8").rstrip('\r\n')
            match = first_line.match(line)
            if match:
                data = match.groupdict()
                if "Votes : Votes" in data.get('message'):
                    find_vote = data
                    print(f"\n{find_vote['timestamp']}", end=" ")
                else:
                    # dump(data)
                    count_key = f"{data['file']}-{data['function']}-{data['line']}"
                    # count_key = f"{data['function']}"
                    if result.get(count_key) is None:
                        result[count_key] = 0
                    result[count_key] += 1
                    total_count += 1

    dump(result)
    dump(dict(sorted(result.items(), key=lambda item: item[1])))

    dump(f"total_line = {total_count}")
