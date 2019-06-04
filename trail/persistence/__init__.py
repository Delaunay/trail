from .logger import NoLogLogger


def build_logger(backend_name, **kwargs):
    # import inside the if so users do not have to install useless packages
    if backend_name == 'comet_ml':
        from .cometml import CMLLogger

        return CMLLogger(**kwargs)

    return NoLogLogger()


def query(backend_name, **kwargs):
    from trail.experiment import get_current_experiment

    """

    :param backend_name:
        -  comet_ml

    :param kwargs:
        - for comet_ml: workspace, project

    :return:
        - RemoteExperiment()
    """

    if backend_name == 'comet_ml':
        from .cometml import CMLExperiment
        return CMLExperiment(**kwargs)

    return get_current_experiment()
