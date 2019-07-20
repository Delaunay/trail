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

Overview
--------

```
# define a project and groups for easier query
# --------------------------------------------
log = TrackClient(backend='file://my_paper.json')
log.set_project(
    name='my_paper', 
    description='Trail test example'
)

log.set_group(
    name='baseline',
    description='SOTA @ 2019'
)

log.new_trial()
# ---

# Save arguments
args = log.log_arguments(args, show=True)


# start training
with log:
    ...

    log.log_metrics(step=epoch, epoch_loss=loss)
    
    # compute elapsed time 
    with trial.chrono('time_this'):
        sleep(1)

    ...


log.report()
log.save()    
```


