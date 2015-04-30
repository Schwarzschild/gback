#from distutils.core import setup
from setuptools import setup

with open('README.rst', 'r') as fh:  txt = fh.read()
with open('LICENSE.txt', 'r') as fh:  lic = fh.read()
script = "s = '''\n" + txt + '\n' + lic + "\n'''\n\ndef readme(): return s"
with open('gback/readme.py', 'w') as fh: fh.write(script)

setup(
  name='gback',
  install_requires=['python-dateutil>=2.4.0', 'httplib2>=0.8',
                    'urllib3>=1.7.1', 'google-api-python-client>=1.4.0',
                    'python-gflags>=2.0', 'icalendar>=3.9.0'],
  version='0.5',
  author='Marc Schwarzschild',
  author_email='ms@TheBrookhavenGroup.com',
  url='http://github.com/Schwarzschild/gback',
  license='MIT',
  description='Google Calendar Backup utility.',
  keywords=['google', 'calendar'],
  packages=['gback',],
)
