import numpy as np

def generate_failure_times(lambda_rate, simulation_time):
    """
    Генерирует временные точки отказов как пуассоновский поток.
    """
    failures = []
    current_time = 0
    while current_time < simulation_time:
        interval = np.random.exponential(1 / lambda_rate)
        current_time += interval
        if current_time < simulation_time:
            failures.append(round(current_time, 2))
    return failures
