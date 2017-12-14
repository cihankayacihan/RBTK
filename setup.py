import sys
import tkinter
import os
import re

assert tkinter.TkVersion >= 8.5, "RBTK requires Tk 8.5 or newer" 

from setuptools import setup, find_packages

def get_requirements():
	with open('requirements.txt', 'r') as file:
		for line in map(str.strip, file):
			if (not line.startswith('#')) and line:
				yield line

def find_metadata():
    with open(os.path.join('rbtk', '__init__.py')) as file:
        content = file.read()

    result = dict(re.findall(
        r'''^__(author|copyright|license)__ = ['"](.*)['"]$''',
        content, re.MULTILINE))
#    assert result.keys() == {'author', 'copyright', 'license'}, result

    # version is defined like this: __version__ = '%d.%d.%d' % version_info
    version_info = re.search(r'^version_info = \((\d+), (\d+), (\d+)\)',
                             content, re.MULTILINE).groups()
    result['version'] = '%s.%s.%s' % version_info

    return result

setup(
    name='RBTK',
    description="An editor to program BioNetGen",
    keywords='editor tkinter rule bionetgen',
    url='https://github.com/cihankayacihan/RBTK',
    install_requires=list(get_requirements()),
    packages=find_packages(),
    package_data={
        '': ['*.txt', '*.gif', '*.sh', '*.ini'],
        'rbtk': ['images/*'],
    },
    entry_points={
        'gui_scripts': ['rbtk = rbtk.__main__:main'],
    },
    zip_safe=False,
    **find_metadata()       # must not end with , before python 3.5
)

