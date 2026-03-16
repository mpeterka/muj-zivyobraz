from datetime import datetime


def get_popelnice_value():
    """
    Returns the popelnice value based on the current day.

    Returns:
        str: "trash3-fill" if it's Monday, "dot" otherwise
    """
    # Monday is 0, Tuesday is 1, ... Sunday is 6
    current_day = datetime.now().weekday()

    if current_day == 0:  # Monday
        return "trash3-fill"
    else:
        return "dot"
