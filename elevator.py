import json
from call import Call


class Elevator:
    def __init__(
            self,
            current_floor=1,
            lobby_floor=1,
            min_floor=1,
            max_floor=100,
            max_capacity=10,
            load_delay=5,
            lobby_load_delay=30,
            time=0,
            verbosity='low'
    ) -> None:
        assert min_floor <= current_floor <= max_floor
        assert min_floor <= lobby_floor <= max_floor
        self.max_capacity = max_capacity
        self.state = 'IDLE'
        self.calls = []
        self.current_floor = current_floor
        self.lobby_floor = lobby_floor
        self.min_floor = min_floor
        self.max_floor = max_floor
        self.time_last_state_changed = 0
        self.load_delay = load_delay
        self.lobby_load_delay = lobby_load_delay
        self.time = time
        self.direction = 0
        self.verbosity = verbosity

    def simulate_tick(self, new_calls, verbosity=None) -> None:
        """
        Simulates elevator state transitions for one tick
        :param new_calls: a list of new Call objects received
        :param verbosity: the level of logging ('off', 'low', 'high')
        :return: None
        """

        if verbosity is None:
            verbosity = self.verbosity

        self.calls += new_calls

        # log the internal state
        if verbosity == 'high':
            print(f'time: {self.time}')
            print(f'new calls: {[call.to_string() for call in new_calls]}')
            print(f'state: {self.state}')
            print(f'current floor: {self.current_floor}')
            print(f'seconds since state changed: {self.seconds_since_state_changed()}')
            print(f'passengers: {self.passenger_count()}')
            print(f'direction: {self.direction}')

        if self.state == 'IDLE':
            assert len([call for call in self.calls if call.state == 'BOARDED']) == 0
            open_calls = [call for call in self.calls if call.state == 'OPEN']

            if len(open_calls) > 0:
                oldest_closest_open_call = min(
                    self.calls,
                    key=lambda c: (self.time - c.init_time, abs(self.current_floor - c.origin))
                )
                if oldest_closest_open_call.origin == self.current_floor:  # change state to loading
                    self.transition_loading(verbosity)
                else:  # head towards the oldest closest open call
                    self.transition_moving(verbosity)
                    verbosity != 'off' and print(f'heading towards floor {oldest_closest_open_call.origin}')
                    self.direction = 1 if oldest_closest_open_call.origin > self.current_floor else -1
            else:
                self.direction = 0

        elif self.state == 'MOVING':
            calls_at_floor = sorted(
                [call for call in self.calls if call.origin == self.current_floor], key=lambda c: c.size
            )

            # if the elevator is empty treat all calls as going in the same direction
            calls_at_floor_same_dir = calls_at_floor
            if len(self.boarded_calls()) > 0:
                calls_at_floor_same_dir = [call for call in calls_at_floor if call.direction() == self.direction]

            # transition into loading if any boarded calls need to exit, or any calls at floor need to board
            if (any(c.destination == self.current_floor for c in self.boarded_calls()) > 0
                    or (len(calls_at_floor_same_dir) > 0 and calls_at_floor_same_dir[
                        0].size < self.current_capacity())):
                self.transition_loading(verbosity)

        elif self.state == 'LOADING':
            calls_at_floor = sorted(self.calls_at_floor(self.calls, self.current_floor), key=lambda c: c.size)
            arrived_calls = [call for call in self.boarded_calls() if call.destination == self.current_floor]

            # if time is not up, keep doors open, and load/off-load any passengers
            if (self.current_floor != self.lobby_floor and self.seconds_since_state_changed() <= self.load_delay) \
                    or (self.current_floor == self.lobby_floor and self.seconds_since_state_changed() <= self.lobby_load_delay):

                # off-load arrived calls
                for call in arrived_calls:
                    call.arrive(self.time)
                    verbosity != 'off' and print(f'off-loading call: {call.to_string()} ')

                #  update direction if there no calls on board and there are calls at floor
                if len(calls_at_floor) > 0 and len(self.boarded_calls()) == 0:
                    # find the direction of the oldest call at the floor
                    oldest_call = max(calls_at_floor, key=lambda c: self.time - c.init_time)
                    self.direction = oldest_call.direction()
                    verbosity != 'off' and print(f'updating direction to: {self.direction}')

                # if the elevator is empty treat all calls as going in the same direction
                calls_at_floor_same_dir = calls_at_floor if len(self.boarded_calls()) == 0 \
                    else [call for call in calls_at_floor if call.direction() == self.direction]

                # filter the calls by size, then sort by size (increasing to decreasing) - to maximize people loaded
                calls_at_floor_same_dir = [call for call in calls_at_floor_same_dir if self.passenger_count() + call.size <= self.max_capacity]
                calls_at_floor_same_dir.sort(key=lambda c: c.size,reverse=True)

                # load as many same direction calls as possible
                for call in calls_at_floor_same_dir:
                    if call.size + self.passenger_count() <= self.max_capacity:
                        call.board(self.time)
                        verbosity != 'off' and print('loading call:', call.to_string())
                    else:
                        break

            else:  # if time is up close doors and transition to moving or idle
                if len(self.boarded_calls()) > 0:  # if there are people on board continue moving
                    self.transition_moving(verbosity)
                else:  # otherwise switch into idle state
                    self.transition_idle(verbosity)
                    self.direction = 0

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
        verbosity != 'off' and print()

    def transition_loading(self, verbosity):
        self.state = 'LOADING'
        self.time_last_state_changed = self.time
        verbosity != 'off' and print('transitioning to loading')

    def transition_moving(self, verbosity):
        self.state = 'MOVING'
        self.time_last_state_changed = self.time
        verbosity != 'off' and print('transitioning to moving')

    def transition_idle(self, verbosity):
        self.state = 'IDLE'
        self.time_last_state_changed = self.time
        verbosity != 'off' and print('transitioning to idle')

    def is_moving_up(self) -> bool:
        return self.state == 'MOVING' and self.direction == 1

    def is_moving_down(self) -> bool:
        return self.state == 'MOVING' and self.direction == -1

    def passenger_count(self) -> int:
        return sum([call.size for call in self.calls if call.state == 'BOARDED'])

    def current_capacity(self) -> int:
        return self.max_capacity - self.passenger_count()

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

    # returns open calls at a particular floor
    def calls_at_floor(self, calls, floor):
        assert self.min_floor <= floor <= self.max_floor
        return [call for call in calls if call.origin == floor and call.state == 'OPEN']

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
            return None, None


def simulate(time_series):
    elevator = Elevator(lobby_load_delay=5)

    for calls in time_series:
        elevator.simulate_tick(calls)

    return elevator.stats()


def demos():
    # going up
    # time_series = [[] for _ in range(20)]
    # time_series[0].append(Call(origin=1, destination=2, size=1, init_time=0))
    # print(simulate(time_series), '\n')

    # time_series = [[] for _ in range(20)]
    # time_series[0].append(Call(origin=1, destination=2, size=1, init_time=0))
    # time_series[0].append(Call(origin=2, destination=3, size=1, init_time=0))
    # print(simulate(time_series), '\n')

    # time_series = [[] for _ in range(20)]
    # time_series[0].append(Call(origin=1, destination=2, size=1, init_time=0))
    # time_series[1].append(Call(origin=1, destination=3, size=1, init_time=0))
    # print(simulate(time_series), '\n')

    # time_series = [[] for _ in range(21)]
    # time_series[0].append(Call(origin=1, destination=3, size=1, init_time=0))
    # time_series[2].append(Call(origin=2, destination=4, size=1, init_time=0))
    # print(simulate(time_series), '\n')

    # going down
    time_series = [[] for _ in range(20)]
    time_series[0].append(Call(origin=2, destination=1, size=1, init_time=0))
    print(simulate(time_series), '\n')


def main():
    demos()


if __name__ == '__main__':
    main()
