import signal
from contextlib import contextmanager
from sudoku import Board

class TimeOutException(Exception): pass

@contextmanager
def time_limit(seconds):
    def sh(signum, frame):
        raise TimeoutException("Timed OUt!")
    signal.signal(signal.SIGALRM, sh)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)



def run_board(init):
    try:
        with time_limit(5):
            b = Board(init)
    except TimeOutException as e:
        print("Timed out!")
        assert 0
    assert b.won()


def test_b0():
    init = [
0,0,0, 8,3,5, 0,7,4,
0,0,0, 9,0,0, 0,1,0,
0,0,0, 0,2,0, 5,0,0,
3,0,7, 4,0,0, 0,5,0,
4,0,0, 0,0,0, 0,0,9,
0,6,0, 0,0,1, 7,0,8,
0,0,9, 0,1,0, 0,0,0,
0,4,0, 0,0,9, 0,0,0,
8,1,0, 2,6,3, 0,0,0]

    run_board(init)

def test_b1():
    init = [
1,0,0, 0,0,0, 0,4,0,
0,7,5, 2,0,4, 0,0,8,
2,0,8, 0,1,0, 0,0,0,
3,9,0, 0,0,2, 0,0,0,
0,0,0, 5,0,1, 0,0,0,
0,0,0, 9,0,0, 0,8,3,
0,0,0, 0,7,0, 8,0,2,
8,0,0, 6,0,3, 1,7,0,
0,1,0, 0,0,0, 0,0,9]
    run_board(init)


