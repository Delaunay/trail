from typing import Dict, Set
from uuid import UUID

from track.structure import Project, TrialGroup, Trial
from track.utils.log import warning, error


class Storage:
    # Main storage
    @property
    def objects(self) -> Dict[UUID, any]:
        raise NotImplementedError()

    # Indexes
    @property
    def projects(self) -> Set[UUID]:
        raise NotImplementedError()

    @property
    def groups(self) -> Set[UUID]:
        raise NotImplementedError()

    @property
    def trials(self) -> Set[UUID]:
        raise NotImplementedError()

    @property
    def project_names(self) -> Dict[str, UUID]:
        raise NotImplementedError()

    @property
    def group_names(self) -> Dict[str, UUID]:
        raise NotImplementedError()

    def insert_project(self, project: Project):
        self.projects.add(project.uid)
        self.project_names[project.name] = project.uid
        self.objects[project.uid] = project

    def insert_trial_group(self, trial_group: TrialGroup):
        if trial_group.uid in self.objects:
            error('Trial group already exists!')
            return

        self.objects[trial_group.uid] = trial_group
        project: Project = self.objects.get(trial_group.project_id)
        assert project is not None, 'Cannot add a trial group to a project that does not exist!'
        project.groups.append(trial_group)

    def insert_trial(self, trial: Trial):
        if trial.uid in self.objects:
            max_rev = 0
            trial_hash = trial.hash

            for k in self.objects.keys():
                if k.startswith(trial_hash):
                    max_rev = max(int(k.split('_')[1]), max_rev)

            warning(f'Trial was already completed. Increasing revision number (rev={max_rev + 1})')
            trial.revision = max_rev + 1
            trial._hash = None

        self.objects[trial.uid] = trial
        project: Project = self.objects.get(trial.project_id)
        assert project is not None, 'Cannot add a trial to a project that does not exist!'
        project.trials.append(trial)

        group: TrialGroup = self.objects.get(trial.group_id)
        if group is not None:
            group.trials.append(trial.uid)

    def commit(self, commit=None):
        raise NotImplementedError()

