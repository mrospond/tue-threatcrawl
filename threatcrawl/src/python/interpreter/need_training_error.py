"""Error for when the trainer needs more training to determine a page type."""


class NeedTrainingError(Exception):
    def __init__(self, message: str = "The interpreter needs more training before a page type can be determined"):
        super().__init__(message)
