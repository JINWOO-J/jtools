#!/usr/bin/env python3
import re, sys
from datetime import datetime
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
    sample_log = """ 2020-02-22 04:03:29,566 639 140034105820928 hx863e16 icon_dex DEBUG candidate_blocks.py(63) set block(086368b4685afe9ecda2b057a42d175fe22b652ca26b4ef7de8ef40e458e51cc) in CandidateBlock
2020-02-22 04:03:29,566 639 140034105820928 hx863e16 icon_dex DEBUG timer_service.py(86) TIMER IS ON (TIMER_KEY_BROADCAST_SEND_UNCONFIRMED_BLOCK)
2020-02-22 04:03:29,566 639 140034105820928 hx863e16 icon_dex DEBUG block_manager.py(898) vote_unconfirmed_block() (15239812/Hash32(0x086368b4685afe9ecda2b057a42d175fe22b652ca26b4ef7de8ef40e458e51cc)/True)
2020-02-22 04:03:29,567 639 140034105820928 hx863e16 icon_dex DEBUG broadcast_scheduler.py(399) broadcast method_name(VoteUnconfirmedBlock)
2020-02-22 04:03:29,567 639 140034105820928 hx863e16 icon_dex INFO consensus_siever.py(255) Votes : Votes
True      : 1/22
Empty     : 21/22
Result    : None
Quorum    : 15
block height(15239812)
--
2020-02-22 07:59:37,504 640 139819749623552 hx863e16 icon_dex DEBUG block_manager.py(495) __add_block_by_sync :: height(15245556) hash(Hash32(0x22a3354dcea056bfa3da84f587544196fd464b69d122a7338e1c361c5963273e))
2020-02-22 07:59:37,512 640 139819749623552 hx863e16 icon_dex WARNING block_manager.py(613) fail block height sync: (<class 'loopchain.jsonrpc.exception.GenericJsonRpcServerError'>, GenericJsonRpcServerError(None))
2020-02-22 07:59:37,512 640 139819749623552 hx863e16 icon_dex WARNING block_manager.py(681) exception during block_height_sync :: <class 'loopchain.jsonrpc.exception.GenericJsonRpcServerError'>, None
--
2020-02-22 04:03:29,749 639 140034616854272 hx863e16 icon_dex DEBUG channel_inner_service.py(776) Peer vote to: 15239812(0) Hash32(0x086368b4685afe9ecda2b057a42d175fe22b652ca26b4ef7de8ef40e458e51cc) from hxdc35f82a3a943e040ae2b9ab2baa2118781b2bc9
2020-02-22 04:03:29,760 639 140034616854272 hx863e16 icon_dex DEBUG channel_inner_service.py(776) Peer vote to: 15239812(0) Hash32(0x086368b4685afe9ecda2b057a42d175fe22b652ca26b4ef7de8ef40e458e51cc) from hx3aa778e1f00c77d3490e9e625f1f83ed26f90133
2020-02-22 04:03:29,762 639 140034616854272 hx863e16 icon_dex DEBUG channel_inner_service.py(776) Peer vote to: 15239812(0) Hash32(0x086368b4685afe9ecda2b057a42d175fe22b652ca26b4ef7de8ef40e458e51cc) from hxfc56203484921c3b7a4dee9579d8614d8c8daaf5
2020-02-22 04:03:29,764 639 140034616854272 hx863e16 icon_dex DEBUG channel_inner_service.py(776) Peer vote to: 15239812(0) Hash32(0x086368b4685afe9ecda2b057a42d175fe22b652ca26b4ef7de8ef40e458e51cc) from hx54d6f19c3d16b2ef23c09c885ca1ba776aaa80e2
2020-02-22 04:03:29,765 639 140034616854272 hx863e16 icon_dex DEBUG channel_inner_service.py(776) Peer vote to: 15239812(0) Hash32(0x086368b4685afe9ecda2b057a42d175fe22b652ca26b4ef7de8ef40e458e51cc) from hx4a43790d44b07909d20fbcc233548fc80f7a4067
2020-02-22 04:03:29,768 639 140034105820928 hx863e16 icon_dex INFO consensus_siever.py(255) Votes : Votes
True      : 9/22
Empty     : 13/22
Result    : None
Quorum    : 15
block height(15239812)
--
--
2020-02-22 04:03:29,889 639 140034616854272 hx863e16 icon_dex DEBUG channel_inner_service.py(776) Peer vote to: 15239812(0) Hash32(0x086368b4685afe9ecda2b057a42d175fe22b652ca26b4ef7de8ef40e458e51cc) from hxfba37e91ccc13ec1dab115811f73e429cde44d48
2020-02-22 04:03:29,896 639 140034616854272 hx863e16 icon_dex DEBUG channel_inner_service.py(776) Peer vote to: 15239812(0) Hash32(0x086368b4685afe9ecda2b057a42d175fe22b652ca26b4ef7de8ef40e458e51cc) from hxd0d9b0fee857de26fd1e8b15209ca15b14b851b2
2020-02-22 04:03:29,911 639 140034616854272 hx863e16 icon_dex DEBUG channel_inner_service.py(776) Peer vote to: 15239812(0) Hash32(0x086368b4685afe9ecda2b057a42d175fe22b652ca26b4ef7de8ef40e458e51cc) from hx0b047c751658f7ce1b2595da34d57a0e7dad357d
2020-02-22 04:03:29,924 639 140034616854272 hx863e16 icon_dex DEBUG channel_inner_service.py(776) Peer vote to: 15239812(0) Hash32(0x086368b4685afe9ecda2b057a42d175fe22b652ca26b4ef7de8ef40e458e51cc) from hxf75bfd0df8d96ee0963965135af2485cee6d5000
2020-02-22 04:03:29,927 639 140034616854272 hx863e16 icon_dex DEBUG channel_inner_service.py(776) Peer vote to: 15239812(0) Hash32(0x086368b4685afe9ecda2b057a42d175fe22b652ca26b4ef7de8ef40e458e51cc) from hxc93a0be07e8a74d9a86d8b12e569b91154681bc8
2020-02-22 04:03:29,969 639 140034105820928 hx863e16 icon_dex INFO consensus_siever.py(255) Votes : Votes
True      : 22/22
Empty     : 0/22
Result    : True
Quorum    : 15
block height(15239812)
2020-02-22 04:03:29,889 639 140034616854272 hx863e16 icon_dex DEBUG channel_inner_service.py(776) Peer vote to: 15239812(0) Hash32(0x086368b4685afe9ecda2b057a42d175fe22b652ca26b4ef7de8ef40e458e51cc) from hxfba37e91ccc13ec1dab115811f73e429cde44d48
2020-02-22 04:03:29,896 639 140034616854272 hx863e16 icon_dex DEBUG channel_inner_service.py(776) Peer vote to: 15239812(0) Hash32(0x086368b4685afe9ecda2b057a42d175fe22b652ca26b4ef7de8ef40e458e51cc) from hxd0d9b0fee857de26fd1e8b15209ca15b14b851b2
2020-02-22 04:03:29,911 639 140034616854272 hx863e16 icon_dex DEBUG channel_inner_service.py(776) Peer vote to: 15239812(0) Hash32(0x086368b4685afe9ecda2b057a42d175fe22b652ca26b4ef7de8ef40e458e51cc) from hx0b047c751658f7ce1b2595da34d57a0e7dad357d
2020-02-22 04:03:29,924 639 140034616854272 hx863e16 icon_dex DEBUG channel_inner_service.py(776) Peer vote to: 15239812(0) Hash32(0x086368b4685afe9ecda2b057a42d175fe22b652ca26b4ef7de8ef40e458e51cc) from hxf75bfd0df8d96ee0963965135af2485cee6d5000
2020-02-22 04:03:29,927 639 140034616854272 hx863e16 icon_dex DEBUG channel_inner_service.py(776) Peer vote to: 15239812(0) Hash32(0x086368b4685afe9ecda2b057a42d175fe22b652ca26b4ef7de8ef40e458e51cc) from hxc93a0be07e8a74d9a86d8b12e569b91154681bc8
2020-02-22 04:03:29,969 639 140034105820928 hx863e16 icon_dex INFO consensus_siever.py(255) Votes : Votes
True      : 22/22
Empty     : 0/22
Result    : True
Quorum    : 15
block height(15239812)
2020-02-22 04:03:29,889 639 140034616854272 hx863e16 icon_dex DEBUG channel_inner_service.py(776) Peer vote to: 15239812(0) Hash32(0x086368b4685afe9ecda2b057a42d175fe22b652ca26b4ef7de8ef40e458e51cc) from hxfba37e91ccc13ec1dab115811f73e429cde44d48
2020-02-22 04:03:29,896 639 140034616854272 hx863e16 icon_dex DEBUG channel_inner_service.py(776) Peer vote to: 15239812(0) Hash32(0x086368b4685afe9ecda2b057a42d175fe22b652ca26b4ef7de8ef40e458e51cc) from hxd0d9b0fee857de26fd1e8b15209ca15b14b851b2
2020-02-22 04:03:29,911 639 140034616854272 hx863e16 icon_dex DEBUG channel_inner_service.py(776) Peer vote to: 15239812(0) Hash32(0x086368b4685afe9ecda2b057a42d175fe22b652ca26b4ef7de8ef40e458e51cc) from hx0b047c751658f7ce1b2595da34d57a0e7dad357d
2020-02-22 04:03:29,924 639 140034616854272 hx863e16 icon_dex DEBUG channel_inner_service.py(776) Peer vote to: 15239812(0) Hash32(0x086368b4685afe9ecda2b057a42d175fe22b652ca26b4ef7de8ef40e458e51cc) from hxf75bfd0df8d96ee0963965135af2485cee6d5000
2020-02-22 04:03:29,927 639 140034616854272 hx863e16 icon_dex DEBUG channel_inner_service.py(776) Peer vote to: 15239812(0) Hash32(0x086368b4685afe9ecda2b057a42d175fe22b652ca26b4ef7de8ef40e458e51cc) from hxc93a0be07e8a74d9a86d8b12e569b91154681bc8
2020-02-22 04:03:29,969 639 140034105820928 hx863e16 icon_dex INFO consensus_siever.py(255) Votes : Votes
True      : 22/22
Empty     : 0/22
Result    : True
Quorum    : 15
block height(15239812)

"""

    # first_line = re.compile(r'^(?P<timestamp>\d{2}\d{2} \d{2}:\d{2}:\d{2},\d{3}) (?P<pid>\d+) (?P<thread_id>\d+) (?P<peer_id>\w{8}) (?P<channel>\w+) (?P<level>[^ ]*) (?P<file>[^ ]*) (?P<message>.*)$')
    first_line = re.compile(r'^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) (?P<pid>\d+) (?P<thread_id>\d+) (?P<peer_id>\w{8}) (?P<channel>\w+) (?P<level>[^ ]*) (?P<file>[^ ]*) (?P<message>.*)$')
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
    test()