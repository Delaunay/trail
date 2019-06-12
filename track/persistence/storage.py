from typing import Dict, Set
from uuid import UUID
from track.struct import Project, TrialGroup, Trial


class Storage:
    # Main storage
    @property
    def objects(self) -> Dict[UUID, any]:
        raise NotImplementedError()

    # Indexes
    @property
    def projects(self) -> Set[UUID]:
        raise NotImplementedError

    @property
    def groups(self) -> Set[UUID]:
        raise NotImplementedError

    @property
    def trials(self) -> Set[UUID]:
        raise NotImplementedError

    @property
    def project_names(self) -> Dict[str, UUID]:
        raise NotImplementedError

    @property
    def group_names(self) -> Dict[str, UUID]:
        raise NotImplementedError

    def insert_project(self, project: Project):
        self.projects.add(project)
        self.project_names[project.name] = project.uid
        self.objects[project.uid] = project

    def insert_trial_group(self, trial_group: TrialGroup):
        project: Project = self.objects.get(trial_group.project_id)
        assert project is not None, 'Cannot add a trial group to a project that does not exist!'
        project.groups.append(trial_group)

    def insert_trial(self, trial: Trial):
        project: Project = self.objects.get(trial.project_id)
        assert project is not None, 'Cannot add a trial to a project that does not exist!'
        project.trials.append(trial)

        group: TrialGroup = self.objects.get(trial.group_id)
        if group is not None:
            group.trials.append(trial.uid)


