
from consumer import Consumer

class Validator(Consumer):
    """
    ARIA validator.
    
    Validates the presentation.
    """

    def consume(self):
        issues = []
        self.presentation.validate(issues)
        for issue in issues:
            print '%s' % issue
        return issues
