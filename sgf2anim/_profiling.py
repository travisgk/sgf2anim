import time

_start_time = None


def reset_time():
    global _start_time
    _start_time = time.time()


def get_elapsed_time():
    elapsed = time.time() - _start_time
    return elapsed
