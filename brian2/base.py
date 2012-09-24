'''
All Brian objects should derive from :class:`BrianObject`.
'''

from weakref import ref
import clocks

__all__ = ['BrianObject', 'get_instances', 'InstanceTracker']


class WeakSet(set):
    """A set of extended references
    
    Removes references from the set when they are destroyed."""
    def add(self, value):
        wr = ref(value, self.remove)
        set.add(self, wr)

    def get(self):
        return [x() for x in self]


class InstanceFollower(object):
    """Keep track of all instances of classes derived from InstanceTracker
    
    The variable __instancesets__ is a dictionary with keys which are class
    objects, and values which are WeakSets, so __instanceset__[cls] is a
    weak set tracking all of the instances of class cls (or a subclass).
    """
    __instancesets__ = {}
    def add(self, value):
        for cls in value.__class__.__mro__: # MRO is the Method Resolution Order which contains all the superclasses of a class
            if cls not in self.__instancesets__:
                self.__instancesets__[cls] = WeakSet()
            self.__instancesets__[cls].add(value)

    def get(self, cls):
        if not cls in self.__instancesets__: return []
        return self.__instancesets__[cls].get()


class InstanceTracker(object):
    """Base class for all classes whose instances are to be tracked
    
    Derive your class from this one to automagically keep track of instances of
    it. If you want a subclass of a tracked class not to be tracked, define the
    attribute ``_track_instances=False``.
    """
    __instancefollower__ = InstanceFollower() # static property of all objects of class derived from InstanceTracker
    _track_instances = True

    def __new__(cls, *args, **kw):
        obj = object.__new__(cls)
        if obj._track_instances:
            obj.__instancefollower__.add(obj)
        return obj


def get_instances(instancetype):
    '''
    Return all instances of a given InstanceTracker derived class.
    '''
    try:
        follower = instancetype.__instancefollower__
    except AttributeError:
        raise TypeError('Cannot track instances of class '+str(instancetype.__name__))
    return follower.get(instancetype)

    
class BrianObject(InstanceTracker):
    '''
    All Brian objects derive from this class, defines magic tracking and update.
    
    Each Brian object that is called as part of :meth:`Network.run` should be
    derived from this class. Each such object should define a method
    :meth:`~BrianObject.update` which is called each time step. Initialised with
    arguments ``when``, which sets the ``when`` attribute and defines at which
    stage in the run loop the object is called, and ``clock`` the update
    :class:`Clock` (set to ``None`` to use the default clock).
    
    The list of all instances of a particular class and its derived classes
    can be returned using the :func:`get_instances` function.    
    '''
    
    def __init__(self, when='start', clock=None):
        if not isinstance(when, str):
            raise TypeError("when attribute should be a string, was "+repr(when))
        if clock is None:
            clock = clocks.defaultclock
        if not isinstance(clock, clock.Clock):
            raise TypeError("clock should have type Clock, was "+clock.__class__.__name__)
     
        #: The ID string determining when the object should be updated in :meth:`Network.run`.   
        self.when = when
        
        #: The Clock determining when the object should be updated.'
        self.clock = clock
        
    def update(self):
        '''
        All BrianObjects should define an update() method which is called every time step.
        '''
        raise NotImplementedError
