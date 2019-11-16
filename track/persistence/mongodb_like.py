from track.persistence.protocol import Protocol
from track.aggregators.aggregator import Aggregator, StatAggregator
from track.structure import Trial, TrialGroup, Project, Status, CustomStatus, _STATUS_STR
from track.serialization import to_json, from_json
from track.utils.log import info, debug

import time

import pymongo
from pymongo.errors import DuplicateKeyError
from typing import Callable


def make_status(status):
    if status is None:
        return None

    if status['name'] in _STATUS_STR:
        return Status(status['value'])
    return CustomStatus(name=status['name'], value=status['value'])


class MongoDBLike(Protocol):
    def __init__(self, uri, client_factory=pymongo.MongoClient):
        self.chrono = {}
        debug('connecting to server')
        self.client = client_factory(uri)

    def log_trial_start(self, trial):
        self.client.write('trials',
                          query={'uid': trial.uid},
                          data={'$set': {
                              'metadata.trial_start': time.time()}})

    def log_trial_finish(self, trial, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            return

        self.client.write('trials',
                          query={'uid': trial.uid},
                          data={'$set': {
                              'metadata.trial_end': time.time()}})

    def log_trial_chrono_start(self, trial, name: str, aggregator: Callable[[], Aggregator] = StatAggregator.lazy(1),
                               start_callback=None,
                               end_callback=None):
        if start_callback is not None:
            start_callback()

        self.chrono[name] = {
            'start': time.time(),
            'cb': end_callback
        }

    def log_trial_chrono_finish(self, trial, name, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            raise exc_type

        data = self.chrono.get(name)
        if data is None:
            return

        cb = data.get('cb')
        if cb is not None:
            cb()

        data['end'] = time.time()
        elapsed = data['end'] - data['start']

        self.client.write('trials',
                          query={'uid': trial.uid},
                          data={'$set': {
                              'chronos': {name: elapsed}}})

    def log_trial_arguments(self, trial: Trial, **kwargs):
        self.client.write('trials',
                          query={'uid': trial.uid},
                          data={'$set': {
                              'parameters': kwargs}})

    def log_trial_metadata(self, trial: Trial, aggregator: Callable[[], Aggregator] = None, **kwargs):
        self.client.write('trials',
                          query={'uid': trial.uid},
                          data={'$set': {
                              'metadata': kwargs}})

    def log_trial_metrics(self, trial: Trial, step: any = None, aggregator: Callable[[], Aggregator] = None, **kwargs):
        if step is None:
            pass

        for k, v in kwargs.items():
            if step is not None:
                v = [[step, v]]
            else:
                v = [v]

            self.client.write('trials',
                              query={'uid': trial.uid},
                              data={'$set': {
                                  f'metrics.{k}': v}})

    def check_result(self):
        # print(self.cursor.statusmessage)
        return True

    def set_trial_status(self, trial: Trial, status, error=None):
        self.client.write('trials',
                          query={'uid': trial.uid},
                          data={'$set': {
                              'status': to_json(status)}})
        return self.check_result()

    def add_trial_tags(self, trial, **kwargs):
        self.client.write('trials',
                          query={'uid': trial.uid},
                          data={'$set': {
                              'metadata': kwargs}})

    # Object Creation
    def get_project(self, project: Project):
        jproject = self.client.read('project', {'uid': project.uid})

        if not jproject:
            return None

        project = from_json(jproject[0])
        return project

    def new_project(self, project: Project):
        try:
            project_id = self.client.write('projects',
                                           to_json(project)
                                           )

            return project
        except DuplicateKeyError:
            return self.get_project(project)

    def get_trial_group(self, group: TrialGroup):
        jgroup = self.client.read('groups', {'uid': group.uid})

        if not jgroup:
            return None

        return from_json(jgroup[0])

    def new_trial_group(self, group: TrialGroup):
        try:
            group_id = self.client.write('groups',
                                         to_json(group)
                                         )

            return group

        except DuplicateKeyError:
            return self.get_trial_group(group)

    def add_project_trial(self, project: Project, trial: Trial):
        self.client.write('trials',
                          query={'uid': trial.uid},
                          data={'$set': {
                              'project_id': project.uid}})

    def add_group_trial(self, group: TrialGroup, trial: Trial):
        self.client.write('trials',
                          query={'uid': trial.uid},
                          data={'$set': {
                              'group_id': group.uid}})

        self.client.write('groups',
                          query={'uid': group.uid},
                          data={'$addToSet': trial.uid}
                          )

    def commit(self, **kwargs):
        pass

    def get_trial(self, trial: Trial):
        trial = self.client.read('trials', {'uid': trial.uid})

        if not trial:
            return None

        return [from_json(trial[0])]

    def new_trial(self, trial: Trial, auto_increment=None):
        try:
            trial_id = self.client.write('trials', to_json(trial))
            return trial

        except DuplicateKeyError:
            trial.revision += 1
            info(f'Trial already exist increasing revision (rev: {trial.revision})')
            return self.new_trial(trial)

    def fetch_groups(self, query):
        return self.client.read('groups', query)

    def fetch_projects(self, query):
        return self.client.read('projects', query)

    def fetch_trials(self, query):
        return self.client.read('trials', query)
