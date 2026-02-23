class TrucoState:
    NOT_CALLED = "not_called"
    TRUCO = "truco"
    RETRUCO = "retruco"
    VALE_4 = "vale_4"

TRUCO_VALUES = {
    TrucoState.NOT_CALLED: 1,
    TrucoState.TRUCO: 2,
    TrucoState.RETRUCO: 3,
    TrucoState.VALE_4: 4
}

def get_next_truco_state(current_state):
    if current_state == TrucoState.NOT_CALLED:
        return TrucoState.TRUCO
    elif current_state == TrucoState.TRUCO:
        return TrucoState.RETRUCO
    elif current_state == TrucoState.RETRUCO:
        return TrucoState.VALE_4
    return None

def get_truco_points(state):
    return TRUCO_VALUES.get(state, 1)
