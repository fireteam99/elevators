import sys
import unittest
from elevator import Elevator
from call import Call


class TestCallMethods(unittest.TestCase):
    def test_is_going_up(self):
        call = Call(origin=1, destination=5, size=1, init_time=1)
        self.assertTrue(call.is_going_up())

    def test_is_going_down(self):
        call = Call(origin=10, destination=5, size=1, init_time=1)
        self.assertTrue(call.is_going_down())

    def test_direction(self):
        upcall = Call(origin=1, destination=5, size=1, init_time=1)
        self.assertEqual(upcall.direction(), 1)

        downcall = Call(origin=10, destination=5, size=1, init_time=1)
        self.assertEqual(downcall.direction(), -1)

    def test_board(self):
        call = Call(origin=1, destination=5, size=1, init_time=1)
        call.board(5)
        self.assertEqual(call.state, 'BOARDED')
        self.assertEqual(call.board_time, 5)

    def test_arrive(self):
        call = Call(origin=1, destination=5, size=1, init_time=1)
        call.board(5)
        call.arrive(10)
        self.assertEqual(call.state, 'ARRIVED')
        self.assertEqual(call.arrival_time, 10)

    def test_to_string(self):
        call = Call(origin=1, destination=5, size=1, init_time=1)
        self.assertEqual(call.to_string(), 'init time: 1, origin: 1, dest: 5, size: 1')


class TestElevatorMethods(unittest.TestCase):

    def test_idle_to_loading(self):
        elevator = Elevator(verbosity="off")
        elevator.simulate_tick([Call(origin=1, destination=2, size=1, init_time=1)])
        self.assertEqual(elevator.state, 'LOADING')

    def test_idle_to_moving(self):
        elevator = Elevator(verbosity="off")
        elevator.simulate_tick([Call(origin=2, destination=1, size=1, init_time=1)])
        self.assertEqual(elevator.state, 'MOVING')

    def test_moving_to_loading(self):
        elevator = Elevator(lobby_load_delay=1, load_delay=1, verbosity="off")
        elevator.simulate_tick([Call(origin=2, destination=1, size=1, init_time=1)])
        self.assertEqual(elevator.state, 'MOVING')
        elevator.simulate_tick([])
        self.assertEqual(elevator.state, 'LOADING')

    def test_loading_to_moving(self):
        elevator = Elevator(lobby_load_delay=1, load_delay=1, verbosity="off")
        elevator.simulate_tick([Call(origin=1, destination=2, size=1, init_time=1)])
        self.assertEqual(elevator.state, 'LOADING')
        elevator.simulate_tick([])
        elevator.simulate_tick([])
        self.assertEqual(elevator.state, 'MOVING')

    def test_loading_to_idle(self):
        elevator = Elevator(lobby_load_delay=1, load_delay=1, verbosity="off")
        elevator.simulate_tick([Call(origin=1, destination=2, size=1, init_time=1)])
        self.assertEqual(elevator.state, 'LOADING')
        elevator.simulate_tick([])
        elevator.simulate_tick([])
        self.assertEqual(elevator.state, 'MOVING')
        elevator.simulate_tick([])
        self.assertEqual(elevator.state, 'LOADING')
        elevator.simulate_tick([])
        elevator.simulate_tick([])
        self.assertEqual(elevator.state, 'IDLE')

    def test_capacity(self):
        elevator = Elevator(max_capacity=10, lobby_load_delay=1, load_delay=1, verbosity="off")
        elevator.simulate_tick([
            Call(origin=1, destination=2, size=9, init_time=1),
            Call(origin=1, destination=2, size=2, init_time=1),
        ])
        self.assertEqual(elevator.state, 'LOADING')
        elevator.simulate_tick([])
        self.assertEqual(elevator.state, 'LOADING')
        elevator.simulate_tick([])
        self.assertEqual(elevator.state, 'MOVING')
        self.assertTrue(elevator.passenger_count() <= elevator.max_capacity)
        elevator.simulate_tick([])
        self.assertEqual(elevator.state, 'LOADING')
        elevator.simulate_tick([])
        self.assertEqual(elevator.state, 'LOADING')
        elevator.simulate_tick([])
        self.assertEqual(elevator.state, 'IDLE')
        self.assertEqual(elevator.passenger_count(), 0)
        elevator.simulate_tick([])
        self.assertEqual(elevator.state, 'MOVING')
        elevator.simulate_tick([])
        self.assertEqual(elevator.state, 'LOADING')


if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    unittest.TextTestRunner(verbosity=3).run(suite)
