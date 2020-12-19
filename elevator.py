import json


class Elevator:
    def __init__(
            self,
            current_floor=0,
            min_floor=1,
            max_floor=100,
            max_capacity=10,
            load_delay=5,
            lobby_load_delay=30,
            time=0
    ) -> None:
        self.max_capacity = max_capacity
        self.state = 'IDLE'
        self.calls = []
        self.current_floor = current_floor
        self.min_floor = min_floor
        self.max_floor = max_floor
        self.current_call = None
        self.time_last_state_changed = 0
        self.load_delay = load_delay
        self.lobby_load_delay = lobby_load_delay
        self.time = time
        self.direction = 0

    def simulate_tick(self, new_calls) -> None:
        self.calls += new_calls

        # log the internal state
        print('time:', self.time)
        print('state:', self.state)
        print('current floor:', self.current_floor)
        print('current call:')
        if self.current_call:
            print('\torigin:', self.current_call.origin)
            print('\tdestination:', self.current_call.destination)
            print('\tsize:', self.current_call.size)
            print('\tinitialization time:', self.current_call.init_time)
        else:
            print('\tno current call')
        print('seconds since state changed:', self.seconds_since_state_changed())
        print()

        if self.state == 'IDLE':
            assert len([call for call in self.calls if call.state == 'BOARDED']) == 0
            assert self.current_call is None

            open_calls = [call for call in self.calls if call.state == 'OPEN']

            if len(open_calls) > 0:
                closest_open_call = sorted(self.calls, key=lambda call: abs(self.current_floor - call.origin))[0]
                if closest_open_call.origin == self.current_floor:
                    self.state = 'LOADING'
                    self.time_last_state_changed = self.time
                    closest_open_call.board(self.time)
                    self.current_call = closest_open_call
                else:
                    self.state = 'MOVING'
                    self.time_last_state_changed = self.time
                    self.current_call = Call(
                        self.current_floor, closest_open_call.origin, 0, self.time, state="BOARDED"
                    )
                    self.direction = 1 if self.current_call.destination > self.current_floor else -1

        elif self.state == 'MOVING':
            calls_at_floor = sorted(
                [call for call in self.calls if call.origin == self.current_floor], key=lambda c: c.size
            )
            calls_at_floor_same_dir = [call for call in calls_at_floor if call.is_going_up()] if self.is_moving_up() \
                else [call for call in calls_at_floor if call.is_going_down()]

            exiting_calls = [call for call in self.boarded_calls() if call.destination == self.current_floor]

            # decide whether or not to stop and open doors
            if (self.current_floor == self.current_call.destination
                    or (len(calls_at_floor_same_dir) > 0 and calls_at_floor_same_dir[0].size < self.current_capacity())
            ):
                self.state = 'LOADING'
                self.time_last_state_changed = self.time

                # off-load exiting calls
                for call in exiting_calls:
                    call.arrive(self.time)

                self.load_available_calls()
                self.update_current_call()

        elif self.state == 'LOADING':
            calls_at_floor = [call for call in self.calls if call.origin == self.current_floor]

            # keep doors open, and load any passengers
            if self.seconds_since_state_changed() < self.load_delay \
                    or (self.current_floor == 1 and self.seconds_since_state_changed() < self.lobby_load_delay):
                self.load_available_calls()
                self.update_current_call()

            else:  # close doors
                if len(calls_at_floor) > 0 or self.current_call:
                    self.state = 'MOVING'
                    self.update_current_call()
                else:
                    self.state = 'IDLE'
                self.time_last_state_changed = self.time

        # move elevator if necessary
        if self.state == 'MOVING':
            if self.is_moving_up():
                assert self.current_floor < self.max_floor
                self.current_floor += 1
            elif self.is_moving_down():
                assert self.current_floor > self.min_floor
                self.current_floor -= 1

        # update time
        self.time += 1

    def is_moving_up(self) -> bool:
        return self.state == 'MOVING' and self.direction == 1

    def is_moving_down(self) -> bool:
        return self.state == 'MOVING' and self.direction == -1

    def current_capacity(self) -> int:
        return sum([call.size for call in self.calls if call.state == 'BOARDED'])

    def boarded_calls(self):
        return [call for call in self.calls if call.state == 'BOARDED']

    def call_going_same_direction(self, call) -> bool:
        assert self.state == 'MOVING' or self.state == 'LOADING'
        if self.is_moving_up():
            return call.destination > self.current_floor
        else:
            return call.destination < self.current_floor

    def seconds_since_state_changed(self) -> int:
        return self.time - self.time_last_state_changed

    def load_available_calls(self):
        assert self.state == 'LOADING'

        calls_at_floor = sorted(
            [call for call in self.calls if call.origin == self.current_floor], key=lambda c: c.size
        )
        calls_at_floor_same_dir = [call for call in calls_at_floor if call.is_going_up()] if self.is_moving_up() \
            else [call for call in calls_at_floor if call.is_going_down()]

        # load as many calls as possible
        for call in calls_at_floor_same_dir:
            if call.size + self.current_capacity() <= self.max_capacity:
                call.board(self.time)
            else:
                break

    def update_current_call(self):
        boarded_calls = [call for call in self.calls if call.state == 'BOARDED']
        boarded_calls_same_dir = [call for call in boarded_calls if self.call_going_same_direction(call)]

        if len(boarded_calls_same_dir) > 0:
            # find closest boarded call dest matching direction
            closest = sorted(boarded_calls_same_dir, key=lambda c: abs(self.current_floor - c.origin))[0]
            self.current_call = closest
        else:
            self.current_call = None

    def stats(self):
        arrived_calls = [call for call in self.calls if call.state == 'ARRIVED']
        # get time waiting for elevator
        average_wait_time = sum([call.board_time - call.init_time for call in arrived_calls]) / len(arrived_calls)
        # average time in elevator
        average_elevator_time = sum([call.arrival_time - call.board_time for call in arrived_calls]) / len(arrived_calls)
        return average_wait_time, average_elevator_time


class Call:
    def __init__(self, origin: int, destination: int, size: int, init_time: int, state='OPEN') -> None:
        self.origin = origin
        self.destination = destination
        self.size = size
        self.init_time = init_time
        self.board_time = None
        self.arrival_time = None
        self.state = state

    def is_going_up(self) -> bool:
        return self.destination > self.origin

    def is_going_down(self) -> bool:
        return self.origin > self.destination

    def board(self, time) -> None:
        self.state = 'BOARDED'
        self.board_time = time

    def arrive(self, time) -> None:
        self.state = 'ARRIVED'
        self.arrival_time = time

    def from_json(self, j: str):
        pass

    def to_json(self) -> str:
        pass


def simulate(time_series):
    elevator = Elevator()

    for calls in time_series:
        elevator.simulate_tick(calls)

    return elevator.stats()


def main():
    time_series = [[] for _ in range(15)]
    time_series[0] = [Call(origin=0, destination=5, size=1, init_time=0)]
    print(simulate(time_series))


if __name__ == '__main__':
    main()
