#!/usr/bin/env python
import os
import sys
from collections import defaultdict
from errno import ENOENT
from itertools import chain
from time import sleep
from wsgiref.simple_server import make_server

from pyroute2 import TaskStats
from pyroute2.netlink import NLM_F_REQUEST
from pyroute2.netlink.taskstats import tcmd
from pyroute2.netlink.taskstats import TASKSTATS_CMD_GET

clk_tck = os.sysconf(os.sysconf_names['SC_CLK_TCK'])
clk_tck_factor = int(1e9 / clk_tck)

pagesize = os.sysconf(os.sysconf_names['SC_PAGESIZE'])
pagesize_factor = pagesize / 1024

interesting_taskstats_keys = (
    'cpu_count',
    'cpu_delay_total',
    'blkio_count',
    'blkio_delay_total',
    'swapin_count',
    'swapin_delay_total',
    'nvcsw',
    'nivcsw',
)

interesting_procstat_fields = (
    ('utime', 14, clk_tck_factor),
    ('stime', 15, clk_tck_factor),
    ('cutime', 16, clk_tck_factor),
    ('cstime', 17, clk_tck_factor),
    ('num_threads', 20, 1),
    ('rss', 24, pagesize_factor),
)

smaps_searchstrings = ['Pss:']


def issue_request(ts, msg):
    return ts.nlm_request(msg, ts.prid, msg_flags=NLM_F_REQUEST)


def unpack_msg(msg):
    #delays = lambda a: (lambda attrs: (attrs['cpu_delay_total'], attrs['cpu_run_real_total']))(a[0]['attrs'][0][1]['attrs'][1][1])
    return msg[0]['attrs'][0][1]['attrs'][1][1]


def do_query(ts, pid):
    msg = tcmd()
    msg['cmd'] = TASKSTATS_CMD_GET
    msg['version'] = 1
    msg['attrs'].append(['TASKSTATS_CMD_ATTR_TGID', pid])
    return unpack_msg(issue_request(ts, msg))


def yield_taskstats(processes):
    ts = TaskStats()
    ts.bind()
    try:
        for name, pid in processes:
            results = do_query(ts, pid)
            for key in interesting_taskstats_keys:
                value = results[key]
                yield 'taskstat_{}{{name="{}", pid="{}"}} {}'.format(key, name, pid, value)
    finally:
        ts.close()


def yield_procstats(processes):
    for name, pid in processes:
        stat_fields = open('/proc/{}/stat'.format(pid)
                           ).readline().rstrip().split(' ')
        for field, pos, factor in interesting_procstat_fields:
            value = int(stat_fields[pos - 1]) * factor
            yield 'procstat_{}{{name="{}", pid="{}"}} {}'.format(field, name, pid, value)


def yield_mapinfo(processes):
    for name, pid in processes:
        stats = dict((i, 0) for i in smaps_searchstrings)
        for line in open('/proc/{}/smaps'.format(pid)):
            for i in smaps_searchstrings:
                if line.startswith(i):
                    value = int(line.split()[1])
                    stats[i] += value

        for i in smaps_searchstrings:
            yield 'procmaps_{}{{name="{}", pid="{}"}} {}'.format(i.lower()[:-1], name, pid, stats[i])

schedstat_fields = (
    ('oncpu', 1000),
    ('waiting', 1000),
    ('slices', 1),
)


def yield_niced_delays(processes):
    for name, pid in processes:
        delayacct_blkio_ticks = defaultdict(int)
        schedstat_dicts = [defaultdict(int) for i in schedstat_fields]
        for tid in os.listdir('/proc/{}/task'.format(pid)):
            try:
                with open('/proc/{}/stat'.format(tid)) as stat_f:
                    stat = stat_f.readline()
                split_stat = stat.split()
                nice = int(split_stat[18])
                if nice == 0:
                    continue
                delayacct_blkio_ticks[nice] += (
                    int(split_stat[41]) * clk_tck_factor
                )
                with open('/proc/{}/schedstat'.format(tid)) as schedstat_f:
                    schedstat = schedstat_f.readline()
                for d, v in zip(schedstat_dicts, schedstat.split()):
                    d[nice] += int(v)
            except IOError as e:
                if e.errno != ENOENT:
                    pass

        for nice, val in delayacct_blkio_ticks.items():
            yield 'thread_blkio_delay{{name="{}", pid="{}", nice="{}"}} {}'.format(name, pid, nice, delayacct_blkio_ticks[nice])
        for (field, factor), d in zip(schedstat_fields, schedstat_dicts):
            for nice, val in d.items():
                yield 'thread_schedstat_{}{{name="{}", pid="{}", nice="{}"}} {}'.format(field, name, pid, nice, val * factor)


def get_pids_from_file(pidfile):
    return map(int, open(pidfile, 'r'))


def get_pids(directory):
    for basename in os.listdir(directory):
        name = basename.split('.')[0]
        pidfile = os.path.join(directory, basename)
        pids = ()
        try:
            pids = get_pids_from_file(pidfile)
        except (ValueError, IOError):
            pass

        for i in pids:
            yield name, i


def handle(directory):
    processes = tuple(get_pids(directory))
    output = chain(
        yield_taskstats(processes),
        yield_procstats(processes),
        yield_mapinfo(processes),
        yield_niced_delays(processes),
    )

    for i in output:
        yield i + '\n'


def make_app(directory):
    def app(environ, start_response):
        stats = handle(directory)
        status = '200 OK'
        headers = [('Content-type', 'text/plain; charset=utf-8')]
        start_response(status, headers)
        return stats
    return app


def main():
    app = make_app(sys.argv[1])
    server = make_server('', int(sys.argv[2]), app)
    server.serve_forever()

if __name__ == '__main__':
    main()
