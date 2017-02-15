# diffios

> Compare Cisco IOS configurations against a baseline.

[![Travis](https://img.shields.io/travis/robphoenix/diffios.svg?style=flat-square)](https://travis-ci.org/robphoenix/diffios)
[![PyPI](https://img.shields.io/pypi/v/diffios.svg?style=flat-square)](https://pypi.python.org/pypi/diffios)
[![PyPI](https://img.shields.io/pypi/pyversions/diffios.svg?style=flat-square)](https://pypi.python.org/pypi/diffios)
[![PyPI](https://img.shields.io/pypi/status/diffios.svg?style=flat-square)](ttps://pypi.python.org/pypi/diffios)
[![Coveralls](https://img.shields.io/coveralls/robphoenix/diffios.svg?style=flat-square)](https://coveralls.io/github/robphoenix/diffios?branch=master)

diffios is a Python library that compares Cisco IOS configurations, outputting
the lines of configuration which are additional and which are missing. It
respects the hierarchical nature of Cisco IOS configurations, uses variables
for elements that are expected to differ per config, such as ip addresses, and
can ignore junk lines. Its goal is to make the compliance auditing of large
network estates more manageable.

## Installation

Install via pip

```sh
pip install diffios
```

## Usage examples (TODO)

```python
>>> baseline = [
... 'hostname {{ hostname }}',
... 'interface FastEthernet 0/1',
... ' ip address {{ ip_address }}',
... ' switchport mode access',
... 'ip domain-name {{ domain }}']
>>> comparison = [
... 'hostname COMPARISON',
... 'interface FastEthernet 0/1',
... ' ip address 192.168.0.1',
... ' switchport mode trunk',
... 'interface FastEthernet 0/2',
... ' ip address 192.168.0.2']
>>> diff = diffios.Compare(baseline, comparison)
>>> diff.additional()
[
    [
        'interface FastEthernet 0/1',
        ' switchport mode trunk'
    ],
    [
        'interface FastEthernet 0/2',
        ' ip address 192.168.0.2'
    ]
]
>>> diff.missing()
[
    [
        'interface FastEthernet 0/1',
        ' switchport mode access'
    ],
    [
        'ip domain-name {{ domain }}'
    ]
]
>>> print(diff.delta())
--- baseline
+++ comparison
 
-   1: interface FastEthernet 0/1
-       switchport mode access
-   2: ip domain-name {{ domain }}
 
+   1: interface FastEthernet 0/1
+       switchport mode trunk
+   2: interface FastEthernet 0/2
+       ip address 192.168.0.2
 
>>> print(diff.pprint_additional())
interface FastEthernet 0/1
 switchport mode trunk
 
interface FastEthernet 0/2
 ip address 192.168.0.2
>>> print(diff.pprint_missing())
interface FastEthernet 0/1
 switchport mode access
 
ip domain-name {{ domain }}
```

## Development setup

To run the test suite

```sh
git clone https://github.com/robphoenix/diffios
cd diffios
# Here you may want to set up a virtualenv
make init
make test
```

## Contributing (TODO)

Please read [CONTRIBUTING.md]() for details on our code of conduct, and the process for submitting pull requests to us.

## Authors

* **Rob Phoenix** - *Initial work* - [robphoenix](https://robphoenix.com)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details
