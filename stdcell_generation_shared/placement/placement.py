logger = logging.getLogger('sivista_app')


class Base0Wrapper(BasePlacement):
    """
    This placement engine is a wrapper around the Euler Placement algorithm.
    """

    def __init__(self):
        pass

    def get_placement(self, transistors: Iterable[Transistor] ) -> Cell:
        logger.info('Euler Placer')
        std_utils.timeout = 20
        return Base0Placement().get_placement(transistors)
    

class Base1Wrapper(BasePlacement):
    """
    This placement engine is a wrapper around Base1 placer.
    
    If base1 placer faces a timeout in the first attempt, 
    a switch is made to the Euler placer with a limt of 50 euler 
    tours per even degree graph.
    
    """

    def __init__(self):
        pass
        
    def get_placement(self, transistors: Iterable[Transistor] ) -> Cell:
        logger.info('Base1 Placer')
        std_utils.timeout = 180
        placement = Base1Placement().get_placement(transistors)
        if not placement:
            logger.info('Base1 Placer timed out: Moving to Euler placer with limiter')
            std_utils.timeout = 75
            return Base0Placement().get_placement(transistors, upper_limit=20)
        
        return placement

