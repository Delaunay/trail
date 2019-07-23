**************
Simple example
**************

Installation and setup
======================

In this tutorial you will run a very simple MNIST example in pytorch using Track.
First, install Oríon following :doc:`/install/core`.
Then install ``pytorch``, ``torchvision`` and clone the
PyTorch `examples repository`_:

.. code-block:: bash

    $ pip3 install torch torchvision
    $ git clone git@github.com:pytorch/examples.git


.. _examples repository: https://github.com/pytorch/examples

Adapting the code of MNIST example
==================================
After cloning pytorch examples repository, cd to mnist folder:


.. code-block:: bash

    $ cd examples/mnist


In main, just after parsing the arguments, you can initialize the track client and create a trial.
The client specifies how will the data be saved on your computer, different methods are supported.
Once the client is initialized, you can create a new trial.

A trial is a set of data retrieved for a set of arguments.

.. code-block:: bash

    $ ....
    $ args = parser.parse_args()
    $ client = TrackClient('file:mnist_excample.py')
    $ trial = client.new_trial(arguments=args)


Then you can store any kind of data that you think will be useful.
In our example we decided to save the error rate on the test set

.. code-block:: bash

    $ def test(args, model, device, test_loader, trial):
    $      ...
    $     trial.log_metrics(error_rate=1 - (correct / len(test_loader.dataset)))
