# elevators

## Local Setup
1. Clone or download the zip of the repository
2. Make sure you running python 3.6 or above
3. `cd` into the repository root and run `pip install -r requirements.txt` to install dependencies
4. Play around with the demos located in `elevator_system.py` and `elevator.py` or run the tests at `test.py`

## Implementation
My solution consists of three main classes: "Call", "Elevator", and "ElevatorSystem". 

The Call class contains the necessary information about a particular call along with some utility functions. 

The Elevator class encapsulates the state of an individual elevator based on the three main states of IDLE, LOADING, and MOVING. 

The Elevator System class implements part B through generating new calls every second and assigning those calls to a particular elevator.

## Performance
Admittedly, the performance isn't optimal as I didn't spend a whole lot of time optimizing the elevator selection algorithm. The elevator system loops through the list of new calls and assigns it to the elevator that thinks it can handle it with the least cost. This `calculate_cost` function simply looks at the number of unfinished calls an elevator has, along with relationship between the call versus the elevator (distance and direction). I'm sure that with a more complex cost calculation algorithm the efficiency of the elevator system could be much improved.