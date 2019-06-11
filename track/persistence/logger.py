from argparse import Namespace


class LoggerBackend:

    def log_argument(self, k, v):
        """ log a single argument value """
        raise NotImplementedError()

    def log_arguments(self, args: Namespace):
        """ log a set of arguments, args can be a dictionary or a Namespace from argparse"""
        raise NotImplementedError()

    def log_metrics(self, step=None, **kwargs):
        """ log metrics for a given step, metrics are value that should improve during the training;
                example: accuracy, loss
        """
        raise NotImplementedError()

    def log_metadata(self, **kwargs):
        """" log metadata, metadata are single values that give additional information about the given trial
                example: parameter space for HPO, system values (GPU, CPU, ..)
        """
        raise NotImplementedError()

    def log_file(self, file_name):
        """ log a file given its path"""
        raise NotImplementedError()

    def log_directory(self, file_name, recursive=False):
        """ log all the files in a given directory"""
        raise NotImplementedError()

    def set_status(self, status, error=None):
        """ Set the status of a trial (running, completed, failed...)"""
        raise NotImplementedError()

    def add_tag(self, key, value):
        """ add a tag, tags are used to lookup trials"""
        raise NotImplementedError()

    def add_tags(self, **kwargs):
        for k, v in kwargs.items():
            self.add_tag(k, v)

    def set_project(self, project):
        """ set the top level project this trial belong to"""
        raise NotImplementedError()

    def set_group(self, group):
        """ set the upper level group this trial belong to"""
        raise NotImplementedError()

    # alias
    def log_param(self, k, v):
        """ log a single parameter @see log_argument"""
        return self.log_argument(k, v)

    def log_params(self, args):
        """ log a single parameter @see log_arguments"""
        return self.log_arguments(args)


class NoLogLogger(LoggerBackend):
    def __init__(self, *args, **kwargs):
        pass

    def log_argument(self, k, v):
        pass

    def log_arguments(self, args: Namespace):
        pass

    def log_metrics(self, step=None, **kwargs):
        pass

    def set_status(self, status, error=None):
        pass

    def log_metadata(self, **kwargs):
        pass

    def set_group(self, group):
        pass

    def set_project(self, project):
        pass

    def add_tag(self, key, value):
        pass
