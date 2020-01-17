#!/usr/bin/env python3
import re, sys
from datetime import datetime
import calendar


first_line = re.compile(r'^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) \| (?P<severity>[^ ]*) \| (?P<logger>[^ ]*) \| (?P<location>[^ ]*) \|.*$')
stack_trace_end = re.compile(r'^(?P<exception>[a-zA-Z]\w*)(:.*)?$')

def parse_date(date):
    # return calendar.timegm(datetime.strptime(date, '%m%d %H:%M:%S,%f').timetuple())
    date = f'2019{date}'
    return datetime.strptime(date, '%Y%m%d %H:%M:%S,%f')

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
    sample_log = """1204 16:47:31,038 1109 140603764938496 hxf5ef15 icon_dex SPAM slot_timer.py(67) call slot(1) delayed(False)
1204 16:47:31,038 1109 140603764938496 hxf5ef15 icon_dex SPAM timer_service.py(78) reset_timer: TIMER_KEY_BLOCK_GENERATE
1204 16:47:31,038 1109 140603764938496 hxf5ef15 icon_dex DEBUG consensus_siever.py(126) -------------------consensus-------------------
1204 16:47:31,038 1109 140603764938496 hxf5ef15 icon_dex INFO consensus_siever.py(257) Votes : Votes
True      : 6/6
Empty     : 0/6
Result    : True
--
1204 16:47:31,057 1109 140603764938496 hxf5ef15 icon_dex DEBUG timer_service.py(86) TIMER IS ON (TIMER_KEY_BROADCAST_SEND_UNCONFIRMED_BLOCK)
1204 16:47:31,057 1109 140603764938496 hxf5ef15 icon_dex DEBUG block_manager.py(915) block_manager:vote_unconfirmed_block (icon_dex/True)
1204 16:47:31,057 1109 140603764938496 hxf5ef15 icon_dex DEBUG broadcast_scheduler.py(436) broadcast method_name(VoteUnconfirmedBlock)
1204 16:47:31,058 1109 140603764938496 hxf5ef15 icon_dex INFO consensus_siever.py(257) Votes : Votes
True      : 1/6
Empty     : 5/6
Result    : None
--
1204 16:47:31,105 1109 140604438918912 hxf5ef15 icon_dex DEBUG channel_inner_service.py(795) Peer vote to : 303974(0) Hash32(0x55ec6128316fabf0fac6e2d0b9fe7c318793047a3f3e2ea27e1ce49e25d18254) from hx3e1227d9c46298325a7845d3d5198270bf6f70bc
1204 16:47:31,114 1109 140604438918912 hxf5ef15 icon_dex DEBUG channel_inner_service.py(795) Peer vote to : 303974(0) Hash32(0x55ec6128316fabf0fac6e2d0b9fe7c318793047a3f3e2ea27e1ce49e25d18254) from hx2e3ad976ef8dddc579d5e24d23a130e975652240
1204 16:47:31,120 1109 140604438918912 hxf5ef15 icon_dex DEBUG channel_inner_service.py(795) Peer vote to : 303974(0) Hash32(0x55ec6128316fabf0fac6e2d0b9fe7c318793047a3f3e2ea27e1ce49e25d18254) from hx62101ec10da3e68c9947ddd30c9c9df30e2deacd
1204 16:47:31,259 1109 140603764938496 hxf5ef15 icon_dex INFO consensus_siever.py(257) Votes : Votes
True      : 6/6
Empty     : 0/6
Result    : True
--
1204 16:47:33,040 1109 140603764938496 hxf5ef15 icon_dex SPAM slot_timer.py(67) call slot(1) delayed(False)
1204 16:47:33,040 1109 140603764938496 hxf5ef15 icon_dex SPAM timer_service.py(78) reset_timer: TIMER_KEY_BLOCK_GENERATE
1204 16:47:33,040 1109 140603764938496 hxf5ef15 icon_dex DEBUG consensus_siever.py(126) -------------------consensus-------------------
1204 16:47:33,040 1109 140603764938496 hxf5ef15 icon_dex INFO consensus_siever.py(257) Votes : Votes
True      : 6/6
Empty     : 0/6
Result    : True
--
1204 16:47:33,066 1109 140603764938496 hxf5ef15 icon_dex DEBUG timer_service.py(86) TIMER IS ON (TIMER_KEY_BROADCAST_SEND_UNCONFIRMED_BLOCK)
1204 16:47:33,066 1109 140603764938496 hxf5ef15 icon_dex DEBUG block_manager.py(915) block_manager:vote_unconfirmed_block (icon_dex/True)
1204 16:47:33,066 1109 140603764938496 hxf5ef15 icon_dex DEBUG broadcast_scheduler.py(436) broadcast method_name(VoteUnconfirmedBlock)
1204 16:47:33,067 1109 140603764938496 hxf5ef15 icon_dex INFO consensus_siever.py(257) Votes : Votes
True      : 1/6
Empty     : 5/6
Result    : None
1204 17:50:49,872 1109 140603764938496 hxf5ef15 icon_dex DEBUG timer_service.py(86) TIMER IS ON (TIMER_KEY_BROADCAST_SEND_UNCONFIRMED_BLOCK)
1204 17:50:49,872 1109 140603764938496 hxf5ef15 icon_dex DEBUG block_manager.py(915) block_manager:vote_unconfirmed_block (icon_dex/True)
1204 17:50:49,873 1109 140603764938496 hxf5ef15 icon_dex DEBUG broadcast_scheduler.py(436) broadcast method_name(VoteUnconfirmedBlock)
1204 17:50:49,873 1109 140603764938496 hxf5ef15 icon_dex INFO consensus_siever.py(257) Votes : Votes
True      : 1/6
Empty     : 5/6
Result    : None    

"""
    first_line = re.compile(r'^(?P<timestamp>\d{2}\d{2} \d{2}:\d{2}:\d{2},\d{3}) (?P<pid>\d+) (?P<thread_id>\d+) (?P<peer_id>\w{8}) (?P<channel>\w+) (?P<level>[^ ]*) (?P<file>[^ ]*) (?P<message>.*)$')
    vote_line = re.compile(r'^(?P<vote>[a-zA-Z]\w*)(\s+)(:(?P<state>.*))?$')
    find_vote = {}

    for line in sample_log.split("\n"):
        match = first_line.match(line)
        if match:
            data = match.groupdict()
            if "Votes : Votes" in data.get('message'):
                find_vote = data
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
                dump(data)






if __name__ == '__main__':
    test()