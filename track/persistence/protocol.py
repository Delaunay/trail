from track.structure import Project, TrialGroup, Trial
from track.aggregators.aggregator import Aggregator
from track.aggregators.aggregator import StatAggregator
from track.aggregators.aggregator import ValueAggregator
from typing import Callable, Optional, List

value_aggregator = ValueAggregator.lazy()


class Protocol:
    def log_trial_start(self, trial):
        """Send the trial start signal

        Parameters
        ----------
        trial: Trial
            reference to the trial being started
        """
        raise NotImplementedError()

    def log_trial_finish(self, trial, exc_type, exc_val, exc_tb):
        """Send the trial end signal

        Parameters
        ----------
        trial: Trial
            reference to the trial that finished
        """
        raise NotImplementedError()

    def log_trial_chrono_start(self, trial, name: str, aggregator: Callable[[], Aggregator] = StatAggregator.lazy(1),
                               start_callback=None,
                               end_callback=None):
        """Send the start signal for an event

        Parameters
        ----------
        trial: Trial
            trial sending the event

        name: str
            name of the event

        aggregator: Aggregator
            container used to accumulate elapsed time

        start_callback: Callable
            function called at start time

        end_callback: Callable
            function called at the end
        """
        raise NotImplementedError()

    def log_trial_chrono_finish(self, trial, name, exc_type, exc_val, exc_tb):
        """Send the end signal for an event

        Parameters
        ----------
        trial: Trial
            trial sending the event

        name: str
            name of the event

        exc_type:
            Exception object

        exec_val
            Exception value

        exc_tb:
            Traceback
        """
        raise NotImplementedError()

    def log_trial_arguments(self, trial: Trial, **kwargs):
        """Save the arguments a trail

        Parameters
        ----------
        trial: Trial
            trial for which the arguments are for

        kwargs:
            key value pair of arguments
        """
        raise NotImplementedError()

    def log_trial_metadata(self, trial: Trial, aggregator: Callable[[], Aggregator] = value_aggregator, **kwargs):
        """Save metadata for a given trials

        Parameters
        ----------
        trial: Trial
            trial reference

        kwargs:
            key value pair of the data to save
        """
        raise NotImplementedError()

    def log_trial_metrics(self, trial: Trial, step: any = None, aggregator: Callable[[], Aggregator] = None, **kwargs):
        """Save metrics for a given trials

        Parameters
        ----------
        trial: Trial
            trial reference

        kwargs:
            key value pair of the data to save
        """
        raise NotImplementedError()

    def set_trial_status(self, trial: Trial, status, error=None):
        """Change trial status

        Parameters
        ----------
        trial: Trial
            trial reference

        status:
            new status to update the trial too

        error:
            in case the user is changing to a state representing an error it can also
            provide an error identification string
        """
        raise NotImplementedError()

    def add_trial_tags(self, trial, **kwargs):
        """Add tags to a trial

        Parameters
        ----------
        trial: Trial
            trial reference

        kwargs:
            key value pair of the data to save
        """
        raise NotImplementedError()

    # Object Creation
    def get_project(self, project: Project) -> Optional[Project]:
        """Fetch a project according to the given definition

        Parameters
        ----------
        project: Project
            project definition used for the lookup

        Returns
        -------
        returns a project object or None
        """
        raise NotImplementedError()

    def new_project(self, project: Project):
        """Insert a new project

        Parameters
        ----------
        project: Project
            project definition used for the insert
        """
        raise NotImplementedError()

    def get_trial_group(self, group: TrialGroup) -> Optional[TrialGroup]:
        """Fetch a group according to a given definition

        Parameters
        ----------
        group: TrialGroup
            group definition used for the lookup

        Returns
        -------
        returns a grouo
        """
        raise NotImplementedError()

    def new_trial_group(self, group: TrialGroup):
        """Create a new group

        Parameters
        ----------
        group: TrialGroup
            group definition used for the insert
        """
        raise NotImplementedError()

    def add_project_trial(self, project: Project, trial: Trial):
        """Add a trial to a project"""
        raise NotImplementedError()

    def add_group_trial(self, group: TrialGroup, trial: Trial):
        """Add a trial to a group"""
        raise NotImplementedError()

    def commit(self, **kwargs):
        """Forces to persist the change"""
        raise NotImplementedError()

    def get_trial(self, trial: Trial) -> List[Trial]:
        """Fetch trials according to a given definition

        Parameters
        ----------
        trial: Trial
            trial definition used for the lookup
        """
        raise NotImplementedError()

    def new_trial(self, trial: Trial):
        """Insert a new trial

        Parameters
        ----------
        trial: Trial
            trial definition used for the insert
        """
        raise NotImplementedError()

    def fetch_trials(self, query) -> List[Trial]:
        """Fetch trials according to a given query"""
        raise NotImplementedError()

    def fetch_groups(self, query):
        """Fetch groups according to a given query"""
        raise NotImplementedError()

    def fetch_projects(self, query):
        """Fetch projects according to a given query"""
        raise NotImplementedError()
