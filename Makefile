task_collector.pex:
	pex -v --python=python2.7 -o $@ pyroute2 . -e prometheus_taskstats_collector:main
