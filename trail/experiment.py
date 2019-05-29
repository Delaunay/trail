from dataclasses import dataclass
from typing import List, Union
from torch.nn import Module

from argparse import ArgumentParser, Namespace

from benchutils.statstream import StatStream
from trail.utils.throttle import is_throttled, throttled
from trail.trial import Trial


@dataclass
class ExperimentData:
    name: str = None
    description: str = None
    models: List[Module] = None
    data_set: any = None
    optimizers: any = None
    hyper_parameters: List[str] = None
    parameters: List[str] = None
    trials: List[Trial] = None


class Experiment:
    """ An experiment is a set of trials. Trials are """

    def __init__(self, name: str, description: str):
        self.exp = ExperimentData(name, description)
        self.current_trial = Trial()
        self.exp.trials.append(self.current_trial)

        self.epoch_printer = None
        self.epoch_id = 0
        self.epoch_total = 0

        self.batch_printer = None
        self.batch_id = 0
        self.batch_total = 0

    def get_arguments(self, args: Union[ArgumentParser, Namespace], show=False) -> Namespace:
        """ Store the arguments that was used to run the trial.
            If an hyper parameter optimizer is used some overrides might be applied to the parameters
        """

        if isinstance(args, ArgumentParser):
            args = args.parse_args()

        args = self.apply_overrides(args)
        self.current_trial.args = args

        if show:
            print('-' * 80)
            for k, v in vars(args).items():
                print(f'{k:>30}: {v}')
            print('-' * 80)

        return args

    def apply_overrides(self, args: Namespace) -> Namespace:
        return args

    def show_epoch_eta(self, epoch_id: int, total, timer: StatStream, msg: str = '', throttle=1, every=None):
        if self.epoch_printer is None:
            self.epoch_printer = throttled(epoch_eta_print, throttle, every)

        # maybe we do not know the numbers of epochs
        self.epoch_total = max(epoch_id, total, self.epoch_total)
        self.epoch_printer(epoch_id, total, timer, msg)

    def show_batch_eta(self, batch_id, total, timer: StatStream, msg: str = '', throttle=1, every=None):
        if self.batch_printer is None:
            self.batch_printer = throttled(batch_eta_print, throttle, every)

        # maybe we do not know the numbers of batch per epoch
        self.batch_total = max(batch_id, total, self.batch_total)
        self.batch_printer(self.epoch_id, self.epoch_total, batch_id, total, timer, msg)

    def report(self):
        pass

    def log_metric(self, name: str, value: any, batch_id=None, epoch_id=None):
        pass



def default_epoch_eta_print(epoch_id: int, epoch_total: int, timer: StatStream, msg: str):
    if msg:
        msg = ' | ' + msg

    eta = _get_time(timer) * (epoch_total - (epoch_id + 1)) / 60
    print(f'[{epoch_id:3d}/{epoch_total:3d}][   /   ] | ETA: {eta:6.2f} min {msg}')


def default_batch_eta_print(epoch_id: int, epoch_total: int,
                            batch_id: int, batch_total: int, timer: StatStream, msg: str):
    if msg:
        msg = ' | ' + msg

    eta = _get_time(timer) * (batch_total - (batch_id + 1)) / 60

    print(f'[{epoch_id:3d}/{epoch_total:3d}][{batch_id:3d}/{batch_total:3d}] | ETA: {eta:6.2f} min {msg}')


epoch_eta_print = default_epoch_eta_print
batch_eta_print = default_batch_eta_print


def _get_time(time: StatStream):
    avg = time.avg
    if avg == 0:
        return time.val
    return avg

