from typing import Dict, List
from trail.struct import Status


class RemoteTrial:

    @property
    def system_metrics(self) -> Dict[str, any]:
        raise NotImplementedError()

    @property
    def graph_definition(self) -> str:
        raise NotImplementedError()

    @property
    def args(self) -> Dict[str, any]:
        raise NotImplementedError()

    @property
    def name(self) -> str:
        raise NotImplementedError()

    @property
    def version(self) -> str:
        raise NotImplementedError()

    @property
    def trial_uid(self) -> str:
        raise NotImplementedError()

    @property
    def code(self) -> str:
        raise NotImplementedError()

    @property
    def source_file(self) -> str:
        raise NotImplementedError()

    @property
    def status(self) -> Status:
        raise NotImplementedError()

    @property
    def errors(self) -> List[any]:
        raise NotImplementedError()

    @property
    def chronos(self) -> Dict[str, any]:
        raise NotImplementedError()

    @property
    def metrics(self) -> Dict[any, Dict[any, any]]:
        raise NotImplementedError()

    @property
    def others(self) -> Dict[any, Dict[any, any]]:
        raise NotImplementedError()


class RemoteExperiment:
    @property
    def name(self) -> str:
        raise NotImplementedError()

    @property
    def description(self) -> str:
        raise NotImplementedError()

    @property
    def models(self) -> List[any]:
        raise NotImplementedError()

    @property
    def data_set(self) -> any:
        raise NotImplementedError()

    @property
    def optimizers(self) -> any:
        raise NotImplementedError()

    @property
    def hyper_parameters(self) -> List[str]:
        raise NotImplementedError()

    @property
    def parameters(self) -> List[str]:
        raise NotImplementedError()

    @property
    def trials(self) -> List[RemoteTrial]:
        raise NotImplementedError()



