from track.persistence.protocol import Protocol
from track.persistence.utils import parse_uri
from track.aggregators.aggregator import Aggregator, StatAggregator
from track.structure import Trial, TrialGroup, Project
from track.serialization import to_json, from_json
import json

import psycopg2
from typing import Callable


class Cockroach(Protocol):
    def __init__(self, uri):
        uri = parse_uri(uri)

        self.con = psycopg2.connect(
            database='track',
            user=uri.get('username', 'track_client'),
            password=uri.get('password', 'track_password'),
            #sslmode='require',
            #sslrootcert='certs/ca.crt',
            #sslkey='certs/client.maxroach.key',
            #sslcert='certs/client.maxroach.crt',
            port=uri['port'],
            host=uri['address']
        )
        self.con.set_session(autocommit=True)
        self.cursor = self.con.cursor()

    def serialize(self, obj):
        return json.dumps(to_json(obj))

    def deserialize(self, obj):
        return from_json(obj)

    def log_trial_start(self, trial):
        pass

    def log_trial_finish(self, trial, exc_type, exc_val, exc_tb):
        raise NotImplementedError()

    def log_trial_chrono_start(self, trial, name: str, aggregator: Callable[[], Aggregator] = StatAggregator.lazy(1),
                               start_callback=None,
                               end_callback=None):
        raise NotImplementedError()

    def log_trial_chrono_finish(self, trial, name, exc_type, exc_val, exc_tb):
        raise NotImplementedError()

    def log_trial_arguments(self, trial: Trial, **kwargs):
        raise NotImplementedError()

    def log_trial_metadata(self, trial: Trial, aggregator: Callable[[], Aggregator] = None, **kwargs):
        raise NotImplementedError()

    def log_trial_metrics(self, trial: Trial, step: any = None, aggregator: Callable[[], Aggregator] = None, **kwargs):
        raise NotImplementedError()

    def set_trial_status(self, trial: Trial, status, error=None):
        raise NotImplementedError()

    def add_trial_tags(self, trial, **kwargs):
        raise NotImplementedError()

    # Object Creation
    def get_project(self, project: Project):
        self.cursor.execute("""
                SELECT 
                    project
                FROM 
                    track.projects
                WHERE
                    project->>'uid' = %s
                """, (project.uid,))

        return self.deserialize(self.cursor.fetchone()[0])

    def new_project(self, project: Project):
        self.cursor.execute("""
                INSERT INTO 
                    track.projects (project) 
                VALUES 
                    (%s);
                """, (self.serialize(project),))

    def get_trial_group(self, group: TrialGroup):
        self.cursor.execute("""
                SELECT 
                    trial_group
                FROM 
                    track.trial_groups
                WHERE
                    trial_group->>'uid' = %s
                """, (group.uid,))

        return self.deserialize(self.cursor.fetchone()[0])

    def new_trial_group(self, group: TrialGroup):
        raise NotImplementedError()

    def add_project_trial(self, project: Project, trial: Trial):
        raise NotImplementedError()

    def add_group_trial(self, group: TrialGroup, trial: Trial):
        raise NotImplementedError()

    def commit(self, **kwargs):
        raise NotImplementedError()

    def get_trial(self, trial: Trial):
        self.cursor.execute("""
            SELECT 
                trial
            FROM 
                track.trials
            WHERE
                trial->>'uid' = %s AND
                trial->>'project_id' = %s
            """, (trial.uid, trial.project_id))

        return self.deserialize(self.cursor.fetchone()[0])

    def new_trial(self, trial: Trial):
        raise NotImplementedError()


if __name__ == '__main__':

    from track.distributed.cockroachdb import CockRoachDB

    db = CockRoachDB(location='/tmp/cockroach', addrs='localhost:8123')
    db.start(wait=True)

    for k, v in db.properties.items():
        print(k, v)

    proto = Cockroach('cockroach://localhost:8123')

    proto.new_project(Project(name='test'))
    p = proto.get_project(Project(name='test'))

    print(p)
    print('--')
    db.stop()
