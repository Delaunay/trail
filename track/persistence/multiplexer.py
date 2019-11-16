import traceback
from track.utils.log import error


class ProtocolMultiplexer:

    def __init__(self, *backends):
        self.protos = backends

    def log_trial_start(self, *args, **kwargs):
        return self.__execute('log_trial_start', *args, **kwargs)

    def log_trial_finish(self, *args, **kwargs):
        return self.__execute('log_trial_finish', *args, **kwargs)

    def log_trial_chrono_start(self, *args, **kwargs):
        return self.__execute('log_trial_chrono_start', *args, **kwargs)

    def log_trial_chrono_finish(self, *args, **kwargs):
        return self.__execute('log_trial_chrono_finish', *args, **kwargs)

    def log_trial_arguments(self, *args, **kwargs):
        return self.__execute('log_trial_arguments', *args, **kwargs)

    def log_trial_metadata(self, *args, **kwargs):
        return self.__execute('log_trial_metadata', *args, **kwargs)

    def log_trial_metrics(self, *args, **kwargs):
        return self.__execute('log_trial_metrics', *args, **kwargs)

    def set_trial_status(self, *args, **kwargs):
        return self.__execute('set_trial_status', *args, **kwargs)

    def add_trial_tags(self, *args, **kwargs):
        return self.__execute('add_trial_tags', *args, **kwargs)

    # Object Creation
    def get_project(self, *args, **kwargs):
        return self.__execute('get_project', *args, **kwargs)

    def new_project(self, *args, **kwargs):
        return self.__execute('new_project', *args, **kwargs)

    def get_trial_group(self, *args, **kwargs):
        return self.__execute('get_trial_group', *args, **kwargs)

    def new_trial_group(self, *args, **kwargs):
        return self.__execute('new_trial_group', *args, **kwargs)

    def add_project_trial(self, *args, **kwargs):
        return self.__execute('add_project_trial', *args, **kwargs)

    def add_group_trial(self, *args, **kwargs):
        return self.__execute('add_group_trial', *args, **kwargs)

    def commit(self, *args, **kwargs):
        return self.__execute('commit', *args, **kwargs)

    def get_trial(self, *args, **kwargs):
        return self.__execute('get_trial', *args, **kwargs)

    def new_trial(self, *args, **kwargs):
        return self.__execute('new_trial', *args, **kwargs)

    def fetch_trials(self, *args, **kwargs):
        return self.__execute('fetch_trials', *args, **kwargs)

    def fetch_groups(self, *args, **kwargs):
        return self.__execute('fetch_groups', *args, **kwargs)

    def fetch_projects(self, *args, **kwargs):
        return self.__execute('fetch_projects', *args, **kwargs)

    def __execute(self, fun, *args, **kwargs):
        for p in self.protos[:-1]:
            try:
                getattr(p, fun)(*args, **kwargs)
            except Exception as e:
                error(traceback.format_exc())

        return getattr(self.protos[-1], fun)(*args, **kwargs)
