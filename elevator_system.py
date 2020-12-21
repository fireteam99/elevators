import numpy as np

from elevator import Elevator
from call import Call
from datetime import datetime
import random


class ElevatorSystem:

    def __init__(
            self,
            elevator_config=None,
            seed=datetime.now(),
            call_freq=0.33,
            lobby_call_freq=0.2,
            lobby_dest_freq=0.5,
    ) -> None:
        assert 0 <= call_freq <= 1
        assert 0 <= lobby_call_freq <= 1
        assert 0 <= lobby_dest_freq <= 1

        if elevator_config is None:
            elevator_config = {
                'current_floor': 1,
                'lobby_floor': 1,
                'min_floor': 1,
                'max_floor': 100,
                'max_capacity': 10,
                'load_delay': 5,
                'lobby_load_delay': 30,
                'time': 0,
                'verbosity': 'low'
            }

        self.elevator_config = elevator_config
        self.elevators = [Elevator(*ec) for ec in elevator_config]
        self.call_freq = call_freq,
        self.lobby_call_freq = lobby_call_freq,
        self.lobby_dest_freq = lobby_dest_freq,
        self.random = random.seed(seed)

    def generate_calls(self, time) -> [Call]:
        min_floor = self.elevator_config['min_floor']
        max_floor = self.elevator_config['max_floor']
        lobby_floor = self.elevator_config['lobby_floor']

        calls = []

        for floor in range(min_floor, max_floor + 1):
            if floor != lobby_floor and self.random.random() < self.call_freq:
                calls.append(Call(
                    origin=floor,
                    destination=self.generate_call_destination(floor),
                    size=self.generate_call_size(),
                    init_time=time
                ))
        if self.random.random() < self.lobby_call_freq:
            calls.append(Call(
                origin=lobby_floor,
                destination=self.generate_call_destination(floor),
                size=self.generate_call_size(),
                init_time=time
            ))

        return calls

    def generate_call_destination(self, origin) -> int:
        min_floor = self.elevator_config['min_floor']
        max_floor = self.elevator_config['max_floor']
        lobby_floor = self.elevator_config['lobby_floor']
        floors = list(range(min_floor, max_floor + 1))
        skewed_floors = floors + [lobby_floor * (len(floors) - 1)]

        destination = random.choice([f for f in skewed_floors if f != origin])
        return destination

    def generate_call_size(self) -> int:
        mean = 1
        stdv = 1
        normal_std = np.sqrt(np.log(1 + (mean / stdv) ** 2))
        normal_mean = np.log(mean) - normal_std ** 2 / 2
        size, = np.random.lognormal(normal_mean, normal_std, size=1)
        rounded = round(size)

        if rounded > 5:
            return 5
        elif rounded < 1:
            return 1
        else:
            return rounded

    def simulate(self, duration=50) -> (float, float, float):
        pass
