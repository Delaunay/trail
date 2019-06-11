from dataclasses import dataclass, field
from typing import Dict, Set
from uuid import UUID


@dataclass
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

