from track.persistence.protocol import Protocol
from track.persistence.utils import parse_uri
from track.aggregators.aggregator import Aggregator, StatAggregator
from track.structure import Trial, TrialGroup, Project
from track.serialization import to_json, from_json
from track.utils.log import info

import json
import time

import psycopg2
from typing import Callable


class Cockroach(Protocol):
    def __init__(self, uri):
        uri = parse_uri(uri)

        self.con = psycopg2.connect(
            database='track',
            user=uri.get('username', 'track_client'),
            password=uri.get('password', 'track_password'),
            # sslmode='require',
            # sslrootcert='certs/ca.crt',
            # sslkey='certs/client.maxroach.key',
            # sslcert='certs/client.maxroach.crt',
            port=uri['port'],
            host=uri['address']
        )
        self.con.set_session(autocommit=True)
        self.cursor = self.con.cursor()
        self.chrono = {}

    def log_trial_start(self, trial):
        self.cursor.execute("""
            UPDATE track.trials
            SET
                metadata = metadata || '{"trial_start": %s}'
            WHERE
                uid = %s
            """, (
            time.time(), self.encode_uid(trial.uid)
        ))

    def log_trial_finish(self, trial, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            return

        self.cursor.execute("""
            UPDATE track.trials
            SET
                metadata = metadata || '{"trial_end": %s}'
            WHERE
                uid = %s
            """, (
            time.time(), self.encode_uid(trial.uid)
        ))

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

        self.cursor.execute("""
            UPDATE track.trials
            SET
                chronos = chronos || jsonb_build_object(%s, %s)
            WHERE
                uid = %s
            """, (
            name, elapsed, self.encode_uid(trial.uid)
        ))

    def log_trial_arguments(self, trial: Trial, **kwargs):
        self.cursor.execute("""
            UPDATE track.trials
            SET
                parameters = parameters || %s
            WHERE
                uid = %s
            """, (
            self.serialize(kwargs), self.encode_uid(trial.uid)
        ))

    def log_trial_metadata(self, trial: Trial, aggregator: Callable[[], Aggregator] = None, **kwargs):
        self.cursor.execute("""
            UPDATE track.trials
            SET
                metadata = metadata || %s
            WHERE
                uid = %s
            """, (
            self.serialize(kwargs), self.encode_uid(trial.uid)
        ))

    def log_trial_metrics(self, trial: Trial, step: any = None, aggregator: Callable[[], Aggregator] = None, **kwargs):
        self.cursor.execute("""
            UPDATE track.trials
            SET
                metrics = metrics || %s
            WHERE
                uid = %s
            """, (
            self.serialize(kwargs), self.encode_uid(trial.uid)
        ))

    def set_trial_status(self, trial: Trial, status, error=None):
        self.cursor.execute("""
            UPDATE track.trials
            SET
                status = %s
            WHERE
                uid = %s
            """, (
            self.serialize(status), self.encode_uid(trial.uid)
        ))

    def add_trial_tags(self, trial, **kwargs):
        self.cursor.execute("""
            UPDATE track.trials
            SET
                tags = tags || %s 
            WHERE
                uid = %s
            """, (
            self.serialize(trial.tags), self.encode_uid(trial.uid)
        ))

    @staticmethod
    def process_uuid_array(value, default=lambda: list()):
        if value is None:
            return default()
        return [Cockroach.decode_uid(t) for t in value]

    # Object Creation
    def get_project(self, project: Project):
        self.cursor.execute("""
            SELECT 
                uid, name, description, tags, trial_groups, trials
            FROM 
                track.projects
            WHERE
                uid = %s
            """, (project.uid,))

        r = self.cursor.fetchone()
        if r is None:
            return r

        return Project(
            _uid=self.decode_uid(r[0]),
            name=r[1],
            description=r[2],
            tags=self.deserialize(r[3]),
            groups=self.process_uuid_array(r[4]),
            trials=self.process_uuid_array(r[5])
        )

    def new_project(self, project: Project):
        try:
            self.cursor.execute("""
                INSERT INTO 
                    track.projects (uid, name, description, tags) 
                VALUES 
                    (%s, %s, %s, %s);
                """, (
                project.uid,
                project.name,
                project.description,
                self.serialize(project.tags),
            ))
            return project
        except psycopg2.errors.UniqueViolation:
            return self.get_project(project)

    def get_trial_group(self, group: TrialGroup):
        self.cursor.execute("""
            SELECT 
                uid, name, description, tags, trials, project_id
            FROM 
                track.trial_groups
            WHERE
                uid = %s
            """, (group.uid,))

        r = self.cursor.fetchone()
        if r is None:
            return r

        return TrialGroup(
            _uid=self.decode_uid(r[0]),
            name=r[1],
            description=r[2],
            tags=self.deserialize(r[3]),
            trials=self.process_uuid_array(r[4]),
            project_id=self.decode_uid(r[5]))

    def new_trial_group(self, group: TrialGroup):
        try:
            self.cursor.execute("""
                INSERT INTO 
                    track.trial_groups (uid, name, description, tags, project_id) 
                VALUES 
                    (%s, %s, %s, %s, %s);
                """, (
                group.uid.encode('utf8'),
                group.name,
                group.description,
                self.serialize(group.tags),
                group.project_id.encode('utf8')
            ))
            return group
        except psycopg2.errors.UniqueViolation:
            return self.get_trial_group(group)

    def add_project_trial(self, project: Project, trial: Trial):
        self.cursor.execute("""
            UPDATE track.projects
            SET 
                trials = array_append(trials, %s)
            WHERE
                uid = %s
            """, (
            self.encode_uid(trial.uid),
            self.encode_uid(project.uid)
        ))
        self.cursor.execute("""
            UPDATE track.trials
            SET 
                project_id = %s
            WHERE
                uid = %s
            """, (
            self.encode_uid(project.uid),
            self.encode_uid(trial.uid)
        ))

    def add_group_trial(self, group: TrialGroup, trial: Trial):
        self.cursor.execute("""
            UPDATE track.trial_groups
            SET 
                trials = array_append(trials, %s)
            WHERE
                uid = %s
            """, (
            self.encode_uid(trial.uid),
            self.encode_uid(group.uid)
        ))
        self.cursor.execute("""
            UPDATE track.trials
            SET 
                group_id = %s
            WHERE
                uid = %s
            """, (
            self.encode_uid(group.uid),
            self.encode_uid(trial.uid)
        ))

    def commit(self, **kwargs):
        pass

    def get_trial(self, trial: Trial):
        self.cursor.execute("""
            SELECT 
                hash, revision, name, description, tags, version, group_id, project_id, parameters, status, errors
            FROM 
                track.trials
            WHERE
                hash = %s AND
                revision = %s
            """, (self.encode_uid(trial.uid), trial.revision))

        r = self.cursor.fetchone()
        if r is None:
            return r

        return Trial(
            _hash=self.decode_uid(r[0]),
            revision=r[1],
            name=r[2],
            description=r[3],
            tags=self.deserialize(r[4]),
            version=r[5],
            group_id=self.decode_uid(r[6]),
            project_id=self.decode_uid(r[7]),
            parameters=r[8],
            status=r[9],
            errors=r[10])

    def new_trial(self, trial: Trial):
        try:
            self.cursor.execute("""
                INSERT INTO 
                    track.trials (uid, hash, revision, name, description, 
                    tags, version, project_id, group_id, parameters) 
                VALUES 
                    (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                """, (
                trial.uid,
                trial.hash,
                trial.revision,
                trial.name,
                trial.description,
                self.serialize(trial.tags),
                trial.version,
                self.encode_uid(trial.project_id),
                self.encode_uid(trial.group_id),
                self.serialize(trial.parameters)
            ))
            return trial

        except psycopg2.errors.UniqueViolation:
            trial.revision += 1
            info(f'Trial already exist increasing revision (rev: {trial.revision})')
            return self.new_trial(trial)

    @staticmethod
    def encode_uid(uid):
        if uid is None:
            return None
        return uid.encode('utf8')

    @staticmethod
    def decode_uid(uid):
        if uid is None:
            return None
        return uid.tobytes().decode('utf8')

    @staticmethod
    def serialize(obj):
        return json.dumps(to_json(obj))

    @staticmethod
    def deserialize(obj):
        return from_json(obj)

