"""This module contains Helper functions"""


def levels_to_int(row_flight_levels):
    meter = 1
    feet = 3.281 * meter
    if row_flight_levels[0] in ('S', 'M'):
        return int(row_flight_levels[1:]) * feet
    return int(row_flight_levels[1:])
