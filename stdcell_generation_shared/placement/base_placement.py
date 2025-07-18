logger = logging.getLogger('sivista_app')

class BasePlacement:
    """
    Interface definition of a transistor placement algorithm.
    """

    def get_placement(self, transistors: Iterable[Transistor]) -> Cell:
        pass



