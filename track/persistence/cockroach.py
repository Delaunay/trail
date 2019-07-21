from track.persistence.protocol import Protocol
from track.persistence.utils import parse_uri
from track.aggregators.aggregator import Aggregator, StatAggregator
from track.structure import Trial, TrialGroup, Project, Status, CustomStatus, _STATUS_STR
from track.serialization import to_json, from_json
from track.utils.log import info, debug

import json
import time

import psycopg2
from typing import Callable


def make_status(status):
    if status is None:
        return None

    if status['name'] in _STATUS_STR:
        return Status(status['value'])
    return CustomStatus(name=status['name'], value=status['value'])


class Cockroach(Protocol):
    def __init__(self, uri):
        uri = parse_uri(uri)
        debug('connecting to server')
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

        debug('get connection cursor')
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
        if step is None:
            pass

        for k, v in kwargs.items():
            exists = trial.metrics.get(k) is not None
            if step is not None:
                v = [[step, v]]
            else:
                v = [v]

            self.cursor.execute(f"""
                UPDATE track.trials
                SET
                    metrics = (
                        CASE
                            WHEN metrics->'{k}' IS NULL
                            THEN 
                                metrics || %s
                            ELSE
                                jsonb_set(
                                    metrics::jsonb,
                                    array['{k}'],
                                    (metrics->'{k}')::jsonb || to_jsonb(%s)
                                )
                        END
                    )
                WHERE
                    uid = %s
            """, (
                self.serialize({k: v}),
                v,
                self.encode_uid(trial.uid)
            ))

    def check_result(self):
        # print(self.cursor.statusmessage)
        return True

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
        return self.check_result()

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
                uid, name, description, metadata, trial_groups, trials
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
            metadata=self.deserialize(r[3]),
            groups=set(self.process_uuid_array(r[4])),
            trials=set(self.process_uuid_array(r[5]))
        )

    def new_project(self, project: Project):
        try:
            self.cursor.execute("""
                INSERT INTO
                    track.projects (uid, name, description, metadata)
                VALUES
                    (%s, %s, %s, %s);
                """, (
                project.uid,
                project.name,
                project.description,
                self.serialize(project.metadata),
            ))
            return project
        except psycopg2.errors.UniqueViolation:
            return self.get_project(project)

    def get_trial_group(self, group: TrialGroup):
        self.cursor.execute("""
            SELECT
                uid, name, description, metadata, trials, project_id
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
            metadata=self.deserialize(r[3]),
            trials=set(self.process_uuid_array(r[4])),
            project_id=self.decode_uid(r[5]))

    def new_trial_group(self, group: TrialGroup):
        try:
            self.cursor.execute("""
                INSERT INTO
                    track.trial_groups (uid, name, description, metadata, project_id)
                VALUES
                    (%s, %s, %s, %s, %s);
                """, (
                group.uid.encode('utf8'),
                group.name,
                group.description,
                self.serialize(group.metadata),
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

    def decode_metrics(self, metrics):
        new_metrics = {}

        for k, values in metrics.items():
            if values:
                if isinstance(values[0], list):
                    new_metrics[k] = {t: v for t, v in values}
                else:
                    new_metrics[k] = values

        return new_metrics

    def get_trial(self, trial: Trial):
        self.cursor.execute("""
            SELECT
                hash, revision, name, description, tags, metadata, metrics, version, group_id, project_id, parameters, status, errors
            FROM
                track.trials
            WHERE
                hash = %s AND
                revision = %s
            """, (self.encode_uid(trial.hash), trial.revision))

        results = self.cursor.fetchall()
        if results is None:
            return []

        trials = []
        for r in results:
            t = Trial(
                _hash=self.decode_uid(r[0]),
                revision=r[1],
                name=r[2],
                description=r[3],
                tags=self.deserialize(r[4]),
                metadata=self.deserialize(r[5]),
                metrics=self.decode_metrics(self.deserialize(r[6])),
                version=r[7],
                group_id=self.decode_uid(r[8]),
                project_id=self.decode_uid(r[9]),
                parameters=r[10],
                status=make_status(r[11]),
                errors=r[12])
            trials.append(t)
        return trials

    def new_trial(self, trial: Trial):
        try:
            self.cursor.execute("""
                INSERT INTO
                    track.trials (uid, hash, revision, name, description,
                    tags, metadata, metrics, version, project_id, group_id, parameters, status)
                VALUES
                    (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                """, (
                trial.uid,
                trial.hash,
                trial.revision,
                trial.name,
                trial.description,
                self.serialize(trial.tags),
                self.serialize(trial.metadata),
                self.serialize(trial.metrics),
                trial.version,
                self.encode_uid(trial.project_id),
                self.encode_uid(trial.group_id),
                self.serialize(trial.parameters),
                self.serialize(trial.status)
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

    def fetch_groups(self, query):
        self.cursor.execute("""
            SELECT
                uid, name, description, metadata, trials, project_id
            FROM
                track.trial_groups
            WHERE
                name = %s AND
                metadata->>'user' = %s
            """, (
            query['name'], query['metadata.user']
        ))

        r = self.cursor.fetchone()
        if r is None:
            return None

        group = TrialGroup(
            _uid=r[0],
            name=r[1],
            description=r[2],
            metadata=self.deserialize(r[3]),
            trials=set(self.process_uuid_array(r[4])),
            project_id=r[5]
        )
        return group

    def fetch_projects(self, query):
        raise RuntimeError()

    def fetch_trials(self, query):
        status = query.get('status')
        heartbeat = query.get('metadata.heartbeat')
        uid = query.get('uid')

        print('----')
        print(query)

        if heartbeat is not None:
            self.cursor.execute("""
                    SELECT
                        hash, revision, name, description, tags, metadata, metrics, version, group_id, project_id, parameters, status, errors
                    FROM
                        track.trials
                    WHERE
                        group_id = %s AND
                        status->>'name' = %s AND
                        CAST (metadata->>'heartbeat' AS DECIMAL) <= %s
                """, (self.encode_uid(query['group_id']), status.name, heartbeat['$lte'])
            )

        elif isinstance(status, dict):
            self.cursor.execute("""
                SELECT
                    hash, revision, name, description, tags, metadata, metrics, version, group_id, project_id, parameters, status, errors
                FROM
                    track.trials
                WHERE
                    group_id = %s AND
                    status->>'name' IN %s
                """, (self.encode_uid(query['group_id']), tuple(status['$in']))
            )

        elif status is not None:
            self.cursor.execute("""
                SELECT
                    hash, revision, name, description, tags, metadata, metrics, version, group_id, project_id, parameters, status, errors
                FROM
                    track.trials
                WHERE
                    group_id = %s AND
                    status->>'name' = %s AND
                    CAST (status->>'value' AS INTEGER) = %s
                """, (self.encode_uid(query['group_id']), status.name, status.value)
            )
        elif uid is not None:
            self.cursor.execute("""
                SELECT
                    hash, revision, name, description, tags, metadata, metrics, version, group_id, project_id, parameters, status, errors
                FROM
                    track.trials
                WHERE
                    uid = %s AND
                    group_id = %s
                """, (
                self.encode_uid(uid),
                self.encode_uid(query['group_id']),)
            )
        else:
            self.cursor.execute("""
                SELECT
                    hash, revision, name, description, tags, metadata, metrics, version, group_id, project_id, parameters, status, errors
                FROM
                    track.trials
                WHERE
                    group_id = %s
                """, (self.encode_uid(query['group_id']),)
            )

        results = self.cursor.fetchall()
        if results is None:
            return []

        trials = []
        for r in results:
            t = Trial(
                _hash=self.decode_uid(r[0]),
                revision=r[1],
                name=r[2],
                description=r[3],
                tags=self.deserialize(r[4]),
                metadata=self.deserialize(r[5]),
                metrics=self.decode_metrics(self.deserialize(r[6])),
                version=r[7],
                group_id=self.decode_uid(r[8]),
                project_id=self.decode_uid(r[9]),
                parameters=r[10],
                status=make_status(r[11]),
                errors=r[12]
            )
            trials.append(t)

        return trials
