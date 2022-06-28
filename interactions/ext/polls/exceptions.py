class NotEnoughChoices(Exception):
    """Exception raised when trying to show a poll that has less than 2 choices"""


class TooManyChoices(Exception):
    """Exception raised when trying to add too many choices"""
