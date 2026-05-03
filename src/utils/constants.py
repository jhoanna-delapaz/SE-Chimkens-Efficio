# ISO 25010 Portability: Centralized constants for theme and metadata
# This allows the UI to be adapted without modifying logic files.

ACTIVE_THEME_MAP = {
    "#6579BE": "#EAB099",
    "#E9DFD8": "#FF7F50",
    "#F54800": "#AFAFDA",
    "#FDF1F5": "#EE8E46",
    "#8A6729": "#EBC8B3",
    "#ECE7E2": "#4A7766",
    "#19485F": "#D9E0A4",
    "#285B23": "#F2CFF1",
    "#92736C": "#FDF1F5",
    "#000000": "#FFFFFF",
    "#FFFFFF": "#000000",
    "#FFFFFE": "#DDDDDD",
    "#DDDDDD": "#FFFFFF",
    "#FFFFFD": "#0000FF",
    "#000001": "#FF0000",
    "#000002": "#00FF00",
}

PRIORITY_MAP = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}


class UIConstants:
    """
    Centralized UI Measurements and Timing.
    ISO 25010: Improves Modifiability and Adaptability.
    """

    SIDEBAR_COLLAPSED_WIDTH = 60
    SIDEBAR_EXPANDED_WIDTH = 150
    SIDEBAR_ICON_SIZE = 40

    KANBAN_LANE_MIN_WIDTH = 280
    KANBAN_CARD_MIN_WIDTH = 200

    TREE_COL_DATE_WIDTH = 200
    TREE_COL_PRIO_WIDTH = 90

    ROUND_RADIUS_LARGE = 20
    ROUND_RADIUS_MEDIUM = 12
    ROUND_RADIUS_SMALL = 8
