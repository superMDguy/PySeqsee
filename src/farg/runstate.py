from farg.codelet import Codelet

class RunState(object):
  """Maintains the state of the current run.
  What is known, what we have asked the user, how many steps have we taken and
  so forth.
  
  Attributes of runstate:
  
  * most_recent_codelet
  """

  def AddCodelet(self, family, urgency, **arguments):
    codelet = Codelet(family, self, urgency, **arguments)
    self.coderack.AddCodelet(codelet)