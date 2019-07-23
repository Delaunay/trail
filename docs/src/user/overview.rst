********
Overview
********

Track as 3 kind of objects, Project, Trial Group and Trial.

* **Project** is a top level object that holds all of its trials and groups
* **TrialGroup** is a set of trials. They are used to order trials together. trials can belong to multiple groups
* **Trial** is the object holding all the information about a given training session. the trial object is the backbone of track and it is the object you will have to deal with the most often


Overview
--------

.. code:: python

    from track import TrackClient

    client = TrackClient('file://client_test.json')

    project = client.set_project(name='paper_78997')
    group = client.set_group(name='idea_4573')

    trial = client.new_trial(name='final_trial_2', description='almost graduating')
    trial.log_arguments(batch_size=256, lr=0.01,momentum=0.99)
    trial.log_metadata(gpu='V100')

    # start the trial explicitly
    with trial:

        for e in range(epochs):

            for batch in dataset:

                # trial helper that compute elapsed time inside a block
                with trial.chrono('batch_time'):
                    ...
                    loss += ...

            trial.log_metrics(step=e, epoch_loss=loss)

        trial.log_metrics(accuracy=0.98)

    client.report()

You can find the sample of a report below

.. code-block:: javascript

    {
      "revision": 1,
      "name": "final_trial_2",
      "description": "almost graduating",
      "version": "a8c3",
      "tags": {
        "workers": 8,
        "hpo": "byopt"
      },
      "parameters": {
        "batch_size": 32,
        "cuda": true,
        "workers": 0,
        "seed": 0,
        "epochs": 2,
        "arch": "convnet",
        "lr": 0.1,
        "momentum": 0.9,
        "opt_level": "O0",
        "break_after": null,
        "data": "mnist",
        "backend": null
      },
      "metadata": {},
      "metrics": {
        "epoch_loss": {
          "0": 2.306920262972514,
          "1": 2.307889754740397
        }
      },
      "chronos": {
        "runtime": 3142.5199086666107,
        "batch_time": {
          "avg": 0.6737696465350126,
          "min": 0.019209623336791992,
          "max": 445.9658739566803,
          "sd": 12.500646799505962,
          "count": 3751,
          "unit": "s"
        }
      },
      "errors": [],
      "status": {
        "value": 302,
        "name": "Completed"
      }
    }


Log Metrics
-----------

User can log metrics with a step or without. `step` is used as key in a dictionary and should be unique

.. code:: python

    trial.log_metrics(step=e, epoch_loss=loss, metric2=value)

    trial.log_metrics(cost=val)

Time things
-----------

You can easily time things with `chrono`. Do not forget if you are measuring GPU compute time should should
synchronize to make sure the computation are done before computing the elapsed time.

.. code:: python

    with trial.chrono('long_compute'):
        sleep(100)


Save arbitrary data
-------------------

You can use metadata to save information on a specific trial that might not be reflected by its parameters

.. code:: python

    trial.log_metadata(had_short_hair_when_running_this_trial=False)


Experiment Report
-----------------

Get a quick overview of all the data that was saved up during training

.. code:: python

    trial.report()

