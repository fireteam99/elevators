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
        assert self.state == 'OPEN'
        self.state = 'BOARDED'
        self.board_time = time

    def arrive(self, time) -> None:
        assert self.state == 'BOARDED'
        self.state = 'ARRIVED'
        self.arrival_time = time

    def from_json(self, j: str):
        pass

    def to_json(self) -> str:
        pass

    def to_string(self) -> str:
        return f'init time: {self.init_time}, origin: {self.origin}, dest: {self.destination}, size: {self.size}'
