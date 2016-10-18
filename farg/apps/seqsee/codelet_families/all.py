# Copyright (C) 2011, 2012  Abhijit Mahabal
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with this
# program.  If not, see <http://www.gnu.org/licenses/>

from farg.apps.seqsee.anchored import SAnchored
from farg.apps.seqsee.exceptions import ConflictingGroupException
from farg.apps.seqsee.subspaces.deal_with_conflicting_groups import SubspaceDealWithConflictingGroups
from farg.core.codelet import CodeletFamily
from farg.core.exceptions import AnswerFoundException
from farg.apps.seqsee.subspaces.are_we_done import SubspaceAreWeDone
from farg.apps.seqsee.subspaces.is_this_interlaced import SubspaceIsThisInterlaced

class CF_FocusOn(CodeletFamily):
  """Causes the required focusable to be added to the stream."""
  @classmethod
  def Run(cls, controller, focusable):
    controller.stream.FocusOn(focusable)

class CF_GroupFromRelation(CodeletFamily):
  """Causes the required relations' ends to create a group."""
  @classmethod
  def Run(cls, controller, relation):
    # If there is a group spanning the proposed group, perish the thought.
    left, right = relation.first.start_pos, relation.second.end_pos
    from farg.apps.seqsee.util import GreaterThanEq, LessThanEq
    if tuple(controller.workspace.GetGroupsWithSpan(LessThanEq(left), GreaterThanEq(right))):
      return
    anchored = SAnchored.Create((relation.first, relation.second),
                                underlying_mapping_set=relation.mapping_set)
    try:
      controller.workspace.InsertGroup(anchored)
    except ConflictingGroupException as e:
      SubspaceDealWithConflictingGroups(
          controller,
          workspace_arguments=dict(new_group=anchored,
                                   incumbents=e.conflicting_groups)).Run()

class CF_DescribeAs(CodeletFamily):
  """Attempt to describe item as belonging to category."""
  @classmethod
  def Run(cls, controller, item, category):
    if not item.IsKnownAsInstanceOf(category):
      item.DescribeAs(category)

class CF_AreWeDone(CodeletFamily):
  """Check using a subspace if we are done. If yes, quit."""
  @classmethod
  def Run(cls, controller):
    answer = SubspaceAreWeDone(controller).Run()
    if answer:
      controller.ui.DisplayMessage("In its current nascent stage, Seqsee decides that it "
                                   "has found the solution as soon as it has added 10 new "
                                   "terms. This is something that needs fixing. Quitting.")
      raise AnswerFoundException("AnswerFound", codelet_count=controller.steps_taken)


class CF_IsThisInterlaced(CodeletFamily):
  """Check using a subspace if we may be looking at an interlaced sequence."""
  @classmethod
  def Run(cls, controller, distance):
    SubspaceIsThisInterlaced(controller,
                             nsteps=20,
                             workspace_arguments=dict(distance=distance)).Run()


class CF_RemoveSpuriousRelations(CodeletFamily):
  """Removes relations between all pairs (A, B) where both belong to supuergroups but their
     supergroups don't overlap.
  """
  @classmethod
  def Run(cls, controller):
    workspace = controller.workspace
    supergroups_map = workspace.CalculateSupergroupMap()
    for element in workspace.elements:
      supergps = supergroups_map[element]
      if not supergps:
        continue
      relations_to_remove = []
      for relation in element.relations:
        if relation.first == element:
          other_end = relation.second
        else:
          other_end = relation.first
        other_supergps = supergroups_map[other_end]
        if not other_supergps:
          continue
        if supergps.intersection(other_supergps):
          continue
        other_end.relations.discard(relation)
        relations_to_remove.append(relation)
      for relation in relations_to_remove:
        element.relations.discard(relation)