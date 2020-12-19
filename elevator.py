import json


class Elevator:
    def __init__(
            self,
            current_floor=1,
            min_floor=1,
            max_floor=100,
            max_capacity=10,
            load_delay=5,
            lobby_load_delay=30,
            time=0
    ) -> None:
        assert min_floor <= current_floor <= max_floor
        self.max_capacity = max_capacity
        self.state = 'IDLE'
        self.calls = []
        self.current_floor = current_floor
        self.min_floor = min_floor
        self.max_floor = max_floor
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
        print('seconds since state changed:', self.seconds_since_state_changed())
        print()

        if self.state == 'IDLE':
            assert len([call for call in self.calls if call.state == 'BOARDED']) == 0
            open_calls = [call for call in self.calls if call.state == 'OPEN']

            if len(open_calls) > 0:
                closest_open_call = min(self.calls, key=lambda call: abs(self.current_floor - call.origin))
                if closest_open_call.origin == self.current_floor:  # change state to loading
                    self.state = 'LOADING'
                    self.time_last_state_changed = self.time
                else:  # head towards the closest open call
                    self.state = 'MOVING'
                    self.time_last_state_changed = self.time
                    self.direction = 1 if closest_open_call.origin > self.current_floor else -1
            else:
                self.direction = 0

        elif self.state == 'MOVING':
            calls_at_floor = sorted(
                [call for call in self.calls if call.origin == self.current_floor], key=lambda c: c.size
            )
            calls_at_floor_same_dir = [call for call in calls_at_floor if call.is_going_up()] if self.is_moving_up() \
                else [call for call in calls_at_floor if call.is_going_down()]

            # transition into loading if any boarded calls need to exit, or any calls at floor need to board
            if (any(c.destination == self.current_floor for c in self.boarded_calls()) > 0
                    or (len(calls_at_floor_same_dir) > 0 and calls_at_floor_same_dir[
                        0].size < self.current_capacity())):
                self.state = 'LOADING'
                self.time_last_state_changed = self.time

        elif self.state == 'LOADING':
            calls_at_floor = sorted(self.calls_at_floor(self.calls, self.current_floor), key=lambda c: c.size)
            arrived_calls = [call for call in self.boarded_calls() if call.destination == self.current_floor]

            # if time is not up, keep doors open, and load/off-load any passengers
            if (self.current_floor != 1 and self.seconds_since_state_changed() < self.load_delay) \
                    or (self.current_floor == 1 and self.seconds_since_state_changed() < self.lobby_load_delay):

                # off-load arrived calls
                for call in arrived_calls:
                    call.arrive(self.time)

                # try to update direction if there no calls on board and calls at floor
                if len(calls_at_floor) > 0 and len(self.boarded_calls()) == 0:
                    # find the direction of the oldest call at the floor
                    oldest_call = max(calls_at_floor, key=lambda c: self.time - c.init_time)
                    self.direction = oldest_call.direction()

                # find any calls at floor that are traveling the same direction as the elevator
                calls_at_floor_same_dir = [call for call in calls_at_floor if call.direction() == self.direction]

                # load as many same direction calls as possible
                for call in calls_at_floor_same_dir:
                    if call.size + self.current_capacity() <= self.max_capacity:
                        call.board(self.time)
                    else:
                        break

            else:  # if time is up close doors and transition to moving or idle
                if len(self.boarded_calls()) > 0:  # if there are people on board continue moving
                    self.state = 'MOVING'
                else:  # otherwise switch into idle state
                    self.state = 'IDLE'
                    self.direction = 0
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

    def calls_at_floor(self, calls, floor):
        assert self.min_floor <= floor <= self.max_floor
        return [call for call in calls if call.origin == floor]

    def call_going_in_direction(self, calls, direction):
        assert -1 <= direction <= 1
        return [call for call in calls if call.direction == direction]

    def stats(self):
        arrived_calls = [call for call in self.calls if call.state == 'ARRIVED']

        if len(arrived_calls) > 0:
            # get time waiting for elevator
            average_wait_time = sum([call.board_time - call.init_time for call in arrived_calls]) / len(arrived_calls)
            # average time in elevator
            average_ride_time = sum([call.arrival_time - call.board_time for call in arrived_calls]) / len(
                arrived_calls)
            return average_wait_time, average_ride_time
        else:
            return 'No arrived calls'


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

    def direction(self) -> int:
        return 1 if self.is_going_up() else -1

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
    elevator = Elevator(lobby_load_delay=5)

    for calls in time_series:
        elevator.simulate_tick(calls)

    return elevator.stats()


def main():
    time_series = [[] for _ in range(20)]
    time_series[0] = [Call(origin=1, destination=5, size=1, init_time=0)]
    print(simulate(time_series))


if __name__ == '__main__':
    main()
