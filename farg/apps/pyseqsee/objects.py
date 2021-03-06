from functools import reduce

import numpy as np

from farg.apps.pyseqsee.categorization.categorizable import Categorizable
from farg.apps.pyseqsee.focusable import PSFocusable
from farg.apps.pyseqsee.relation import PSRelation
from farg.apps.pyseqsee.utils import StructureToString
from farg.core.history import History, EventType, ObjectType
from farg.core.ltm.node import VECTOR_DIM
from farg.core.ltm.storable import LTMNodeContent, LTMStorableMixin


class PlatonicObject(LTMNodeContent):
    """A stringified representation of a structure---i.e., of possibly nested tuples of integers.

    We need PlatonicObjects mainly for storing in the LTM.

    PlatonicObjects are cached, meaning that with the same constructor argument,
    we always get the same object back.
    """

    def __init__(self, *, rep, vector):
        assert (isinstance(rep, str))
        self.rep = rep

    def BriefLabel(self):
        return 'Platonic %s' % self.rep

    @classmethod
    def CreateFromStructure(cls, structure):
        """Create a PlatonicObject.

        Structure can be an integer, or a tuple of structures.

        Note that (4,) is NOT the same as (((4,),),).
        """
        return cls(rep=StructureToString(structure))


class PSObject(LTMStorableMixin, PSFocusable):
    """Represents an element or group in the workspace.

    This may be anchored or not. When anchored, it has a start and end offset.

    TODO(amahabal): Have not yet ported over the code for getting the fringe and
    strength.

    TODO(amahabal): Also not present yet is the storage of relations.
    """

    def __init__(self, *, msg='', parents=[]):
        PSFocusable.__init__(self)
        self.relations = dict()
        self._span = None
        History.AddArtefact(self, ObjectType.WS_GROUP,
                            "EltOrGp %s" % msg,
                            parents)

    def Span(self):
        return self._span

    def GetLTMStorableContent(self):
        return PlatonicObject.CreateFromStructure(self.Structure())

    def CopyByStructure(self):
        from farg.apps.pyseqsee.utils import PSObjectFromStructure
        return PSObjectFromStructure(self.Structure())

    def GetRelationTo(self, other):
        if other in self.relations:
            return self.relations[other]
        new_rel = PSRelation(first=self, second=other)
        self.relations[other] = new_rel
        return new_rel

    def CalculateFringe(self):
        """The fringe is just the structure.

        Note that the fringe also includes things added by categories.
        """
        return {self.Structure(): 1.0}

    def CalculateActions(self, controller):
        """All actions will be suggested by the categories. This is thus empty."""
        return []


class PSElement(PSObject):
    """Represents a single element in the sequence."""

    def __init__(self, *, magnitude, msg='', parents=[]):
        PSObject.__init__(self, msg=msg, parents=parents)
        self.magnitude = magnitude
        from farg.apps.pyseqsee.categorization.numeric import CategoryInteger
        self.DescribeAs(CategoryInteger())
        self.vector = np.random.uniform(-1.0, 1.0, VECTOR_DIM)

    def Structure(self):
        return self.magnitude

    def SetSpanStart(self, start):
        if self._span:
            assert (self._span == (start, start))
            return
        self._span = (start, start)

    def _CalculateSpanGivenStart(self, start):
        return ((self, (start, start)),)

    def FlattenedMagnitudes(self):
        return (self.magnitude,)

    def BriefLabel(self):
        if self.Span():
            return 'Element %d@%d' % (self.magnitude, self.Span()[0])
        return 'Element %d' % self.magnitude


class PSGroup(PSObject):
    """Represents a group, including the degenerate case of singleton or empty group.

    TODO(amahabal): Not ported over the notion of underlying relations, yet. But
    maybe what I need is slightly different anyway, since a mountain cannot be
    cleanly represented just by a single kind of underlying relationship among
    items.
    """

    def __init__(self, *, items, msg='', parents=[]):
        PSObject.__init__(self, msg=msg, parents=parents)
        self.items = items
        self.vector = np.mean([item.vector for item in items], axis=0)

    def Structure(self):
        return tuple(x.Structure() for x in self.items)

    def BriefLabel(self):
        if self._span:
            return 'Group %s@(%d, %d)' % (self.Structure(), self._span[0],
                                          self._span[1])
        return 'Group %s' % self.Structure()

    def FlattenedMagnitudes(self):
        return reduce(lambda x, y: x + y, (i.FlattenedMagnitudes()
                                           for i in self.items))

    def HypotheticallyAddComponentBefore(self, component):
        new_gp = PSGroup(items=(component,) + tuple(self.items))
        new_gp.InferSpans()
        return new_gp

    def HypotheticallyAddComponentAfter(self, component):
        new_gp = PSGroup(items=tuple(self.items) + (component,))
        new_gp.InferSpans()
        return new_gp

    def _CalculateSpanGivenStart(self, start):
        spans = []
        right_end = start - 1
        for i in self.items:
            spans.extend(i._CalculateSpanGivenStart(right_end + 1))
            right_end = spans[-1][1][1]
        spans.append((self, (start, right_end)))
        return spans

    def SetSpanStart(self, start):
        projected_spans = self._CalculateSpanGivenStart(start)

        # Let's check that these make sense...
        for item, span in projected_spans:
            if item._span:
                assert (item._span == span)

        # So all is good...
        for item, span in projected_spans:
            item._span = span

    def InferSpans(self):
        projected_relative_spans = self._CalculateSpanGivenStart(0)
        # Let's calculate deltas.
        deltas = []
        for item, span in projected_relative_spans:
            if item._span:
                deltas.append(item._span[0] - span[0])
                deltas.append(item._span[1] - span[1])
        if not deltas:
            return False
        if any(x != deltas[0] for x in deltas[1:]):
            return False
        self.SetSpanStart(deltas[0])
        return True