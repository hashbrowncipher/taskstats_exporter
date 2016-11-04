taskstats_exporter: A Prometheus exporter for Linux process statistics
======================================================================

This is a Prometheus exporter for information about Linux tasks. The following
information is collected:
 * task accounting statistics from netlink for the task itself and all of its
   threads
 * basic process statistics from /proc/<pid>/stat
 * proportional set size
 * block I/O delays and scheduler statistics for niced threads

Installation and usage
----------------------

The taskstats exporter is installable as a Python egg. It expects to read named
pidfiles from a directory. The directory is automatically scanned on each
prometheus scrape: there is no need to restart the exporter when the directory
contents change.

Usage:
::
  $ taskstats_exporter <pidfiles_dir> <listen_port>

Example:
::
  $ mkdir exporter_pidfiles
  $ ln -s /run/cassandra/cassandra.pid exporter_pidfiles/cassandra
  $ taskstats_exporter exporter_pidfiles 8080
  $ curl 127.0.0.1:8080
  taskstat_cpu_count{name="cassandra", pid="16923"} 8365887
  taskstat_cpu_delay_total{name="cassandra", pid="16923"} 659867655322
  taskstat_blkio_count{name="cassandra", pid="16923"} 477
  taskstat_blkio_delay_total{name="cassandra", pid="16923"} 2508392517
  taskstat_swapin_count{name="cassandra", pid="16923"} 41
  taskstat_swapin_delay_total{name="cassandra", pid="16923"} 164895486
  taskstat_nvcsw{name="cassandra", pid="16923"} 8049063
  taskstat_nivcsw{name="cassandra", pid="16923"} 267691
  procstat_utime{name="cassandra", pid="16923"} 323090000000
  procstat_stime{name="cassandra", pid="16923"} 76490000000
  procstat_cutime{name="cassandra", pid="16923"} 140000000
  procstat_cstime{name="cassandra", pid="16923"} 160000000
  procstat_num_threads{name="cassandra", pid="16923"} 81
  procstat_rss{name="cassandra", pid="16923"} 414740
  procmaps_pss{name="cassandra", pid="16923"} 416220
  thread_blkio_delay{name="cassandra", pid="16923", nice="3"} 0
  thread_blkio_delay{name="cassandra", pid="16923", nice="4"} 0
  thread_schedstat_oncpu{name="cassandra", pid="16923", nice="3"} 4000000000
  thread_schedstat_oncpu{name="cassandra", pid="16923", nice="4"} 6055831288000
  thread_schedstat_waiting{name="cassandra", pid="16923", nice="3"} 28283162000
  thread_schedstat_waiting{name="cassandra", pid="16923", nice="4"} 11788537641000
  thread_schedstat_slices{name="cassandra", pid="16923", nice="3"} 35
  thread_schedstat_slices{name="cassandra", pid="16923", nice="4"} 101519
