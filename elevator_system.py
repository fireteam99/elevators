import numpy as np
import matplotlib.pyplot as plt

from elevator import Elevator
from call import Call
import time
import random


class ElevatorSystem:

    def __init__(
            self,
            elevator_count=3,
            elevator_config=None,
            seed=round(time.time()),
            verbosity='low',
            call_freq=0.033,
            lobby_call_freq=0.2,
            lobby_dest_freq=0.5,
            mean=1,
            stdv=1,
            max_call_size=5,
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
                'verbosity': verbosity
            }

        self.elevator_count = elevator_count
        self.elevator_config = elevator_config
        self.elevators = [Elevator(**elevator_config) for _ in range(elevator_count)]
        self.call_freq = call_freq
        self.lobby_call_freq = lobby_call_freq
        self.lobby_dest_freq = lobby_dest_freq
        self.seed = seed
        self.verbosity = verbosity
        random.seed(seed)
        np.random.seed(seed)
        self.mean = mean
        self.stdv = stdv
        self.max_call_size = max_call_size

    def generate_calls(self, t) -> [Call]:
        min_floor = self.elevator_config['min_floor']
        max_floor = self.elevator_config['max_floor']
        lobby_floor = self.elevator_config['lobby_floor']

        calls = []

        for floor in range(min_floor, max_floor + 1):
            if floor != lobby_floor and random.random() < self.call_freq:
                calls.append(Call(
                    origin=floor,
                    destination=self.generate_call_destination(floor),
                    size=self.generate_call_size(self.mean, self.stdv),
                    init_time=t
                ))
        if random.random() < self.lobby_call_freq:
            calls.append(Call(
                origin=lobby_floor,
                destination=self.generate_call_destination(lobby_floor),
                size=self.generate_call_size(self.mean, self.stdv),
                init_time=t
            ))

        return calls

    def generate_call_destination(self, origin) -> int:
        min_floor = self.elevator_config['min_floor']
        max_floor = self.elevator_config['max_floor']
        lobby_floor = self.elevator_config['lobby_floor']
        floors = list(range(min_floor, max_floor + 1))
        skewed_floors = floors + [lobby_floor] * (len(floors) - 1)
        destination = random.choice([f for f in skewed_floors if f != origin])
        return destination

    def generate_call_size(self, mean=1, stdv=1) -> int:
        normal_std = np.sqrt(np.log(1 + (mean / stdv) ** 2))
        normal_mean = np.log(mean) - normal_std ** 2 / 2
        size, = np.random.lognormal(normal_mean, normal_std, size=1)
        rounded = round(size)

        if rounded > self.max_call_size:
            return self.max_call_size
        elif rounded < 1:
            return 1
        else:
            return rounded

    def simulate(self, duration=50) -> list:
        for x in range(duration):
            calls = self.generate_calls(x)

            if self.verbosity != 'off':
                print('Tick:', x)
                print('New Calls:', [c.to_string() for c in calls], '\n')

            for call in calls:
                lowest_cost_el = min(self.elevators, key=lambda e: e.calculate_cost(call))
                lowest_cost_el.assign_call(call)

            for i, elevator in enumerate(self.elevators):
                log = elevator.simulate_tick()
                if self.verbosity != 'off' and len(log) > 0:
                    print('Elevator:', i)
                    print('\n'.join(log), '\n')

            if self.verbosity != 'off':
                print('---------------------------------------------------')

        return [el.logs for el in self.elevators]


def demo() -> None:
    es = ElevatorSystem(seed=0, verbosity='high', elevator_count=3, elevator_config={
                'current_floor': 1,
                'lobby_floor': 1,
                'min_floor': 1,
                'max_floor': 100,
                'max_capacity': 10,
                'load_delay': 5,
                'lobby_load_delay': 30,
                'time': 0,
                'verbosity': 'high'
    })
    es.simulate(100)


def visualize_calls():
    es = ElevatorSystem(seed=2)

    calls = []
    for x in range(1000):
        calls += es.generate_calls(x)

    origins = []
    destinations = []
    sizes = []
    for call in calls:
        origins.append(call.origin)
        destinations.append(call.destination)
        sizes.append(call.size)

    plt.hist(origins, bins=range(es.elevator_config['min_floor'], es.elevator_config['max_floor']))
    plt.show()

    plt.hist(destinations, bins=range(es.elevator_config['min_floor'], es.elevator_config['max_floor']))
    plt.show()

    plt.hist(sizes, bins=range(1, es.max_call_size + 1))
    plt.xticks(range(1, es.max_call_size))
    plt.show()


if __name__ == '__main__':
    demo()
    visualize_calls()
