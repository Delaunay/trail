from typing import Dict, List, Optional
from track.struct import Status


# pylint: disable=too-many-public-methods
class RemoteTrial:
    @property
    def trial_hash(self) -> str:
        raise NotImplementedError()

    @property
    def revision(self) -> int:
        raise NotImplementedError()

    @property
    def name(self) -> Optional[str]:
        raise NotImplementedError()

    @property
    def description(self) -> Optional[str]:
        raise NotImplementedError()
    @property
    def tags(self) -> Dict[str, any]:
        raise NotImplementedError()

    @property
    def version(self) -> Optional[str]:
        raise NotImplementedError()
    @property
    def group_id(self) -> Optional[int]:
        raise NotImplementedError()

    @property
    def project_id(self) -> Optional[int]:
        raise NotImplementedError()

    @property
    def parameters(self) -> Dict[str, any]:
        raise NotImplementedError()

    @property
    def metadata(self) -> Dict[str, any]:
        raise NotImplementedError()

    @property
    def metrics(self) -> Dict[str, any]:
        raise NotImplementedError()

    @property
    def chronos(self) -> Dict[str, any]:
        raise NotImplementedError()

    @property
    def status(self) -> Optional[Status]:
        raise NotImplementedError()

    @property
    def errors(self) -> List[str]:
        raise NotImplementedError()


# pylint: disable=too-many-public-methods
class RemoteTrialGroup:
    @property
    def uid(self) -> Optional[str]:
        raise NotImplementedError()

    @property
    def name(self) ->  Optional[str]:
        raise NotImplementedError()

    @property
    def description(self) ->  Optional[str]:
        raise NotImplementedError()

    @property
    def tags(self) ->  List[str]:
        raise NotImplementedError()

    @property
    def trials(self) -> List[RemoteTrial]:
        raise NotImplementedError()

    @property
    def project_id(self) ->  Optional[int]:
        raise NotImplementedError()


# pylint: disable=too-many-public-methods
class RemoteProject:
    @property
    def uid(self) -> Optional[str]:
        raise NotImplementedError()

    @property
    def name(self) -> Optional[str]:
        raise NotImplementedError()

    @property
    def description(self) -> Optional[str]:
        raise NotImplementedError()

    @property
    def tags(self) -> List[str]:
        raise NotImplementedError()

    @property
    def groups(self) -> List[RemoteTrialGroup]:
        raise NotImplementedError()

    @property
    def trials(self) -> List[RemoteTrial]:
        raise NotImplementedError()



