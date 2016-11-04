from distutils.core import setup

setup(
    name='taskstats_exporter',
    version='0.0.1',
    packages=['taskstats_exporter'],
    entry_points = dict(
        console_scripts=['taskstats_exporter=taskstats_exporter:main'],
    ),
    install_requires = [
        'pyroute2>=0.4.10',
    ]
)
