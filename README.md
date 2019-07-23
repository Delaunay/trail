Track
=====

| CI | Coverage |
|----|----------|
| [![Build Status](https://travis-ci.org/Delaunay/track.svg?branch=master)](https://travis-ci.org/Delaunay/track) | [![codecov](https://codecov.io/gh/Delaunay/track/branch/master/graph/badge.svg)](https://codecov.io/gh/Delaunay/track) |


Installation
------------

```
pip install -r requirements
python setup.py install
```

Documentation
-------------

`sphinx-build -W --color -c docs/src/ -b html docs/src/ docs/build/html`

Overview
--------


```python
from track import TrackClient

client = TrackClient('file://client_test.json')
client.set_project(name='test_client')

trial = client.new_trial()
trial.log_arguments(batch_size=256)

with trial:
    trial.log_metrics(step=1, epoch_loss=1)
    trial.log_metrics(accuracy=0.98)

client.save()
client.report()
```


