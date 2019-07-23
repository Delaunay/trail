Track
=====

|rtfd| |codecov| |travis|

.. |codecov| image:: https://codecov.io/gh/Delaunay/track/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/Delaunay/track
    :alt: Codecov Report

.. |travis| image:: https://travis-ci.org/Delaunay/track.svg?branch=master
    :target: https://travis-ci.org/Delaunay/track
    :alt: Travis tests

.. |rtfd| image:: https://readthedocs.org/projects/track/badge/?version=latest
    :target: https://track.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status


Installation
------------

.. code:: bash

    pip install -r requirements
    python setup.py install


Documentation
-------------

.. code:: bash

    sphinx-build -W --color -c docs/src/ -b html docs/src/ docs/build/html
    (cd docs/build/html && python -m http.server 8000 --bind 127.0.0.1)

Overview
--------


.. code:: python

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



