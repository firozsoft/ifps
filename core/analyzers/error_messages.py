PATH_NOT_FOUND = "No path found between {0} and {1} through {2}."  # start_point, end_point, route
EET_NOT_FOUND = "ITEM18 EET/ is not found."
FIR_NOT_FOUND_IN_EET = "The EET/ doesn't mention {0}."  # fir_indicator
POINT_DOES_NOT_EXISTS = "Point {0} does not exist."  # point_name
ROUTE_DOES_NOT_EXISTS = "Route {0} does not exist."  # route_name
BOUNDARY_DETERMINATION_ERROR_NO_ADJACENT_FIRS = "Unable to determine the {0} point for {1}. No adjacent FIRs were found from EET."  # entry_or_exit, our_fir
BOUNDARY_DETERMINATION_ERROR_NONADJACENT_FIR_OR_NO_BOUNDARY = (
    "Either {0} is nonadjacent to {1} or boundary points cannot be determined."  # neighbor_fir, our_fir
)
BOUNDARY_DETERMINATION_ERROR = "{0} point of {1} can not be determined."  # entry_or_exit, our_fir
BOUNDARY_DETERMINATION_ERROR_FROM_TO_FIR_ON_ROUTE = "Unable to determine {0} point {1} {2} on {3}."  # entry_or_exit, to_or_from, neighbor_fir, boundary_route_indicator
FIR_IS_NOT_ACTIVE = "FIR {} is not active."  # fir
ROUTE_PORTION_DETERMINATION_ERROR = "Unable to determine route portion within {}."  # our_fir
