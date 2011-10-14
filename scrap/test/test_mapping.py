from group import Group
from integer import Integer
from mapping import Mapping

from nose.tools import raises

class M(Mapping):
  realm = Integer
  arity = 1
  
  @staticmethod
  def fn(i):
    return Integer(i.magnitude + 1)
  
  @staticmethod
  def rev_fn(i):
    return Integer(i.magnitude - 1)
  
@raises(Exception)
def test_cannot_init():
  M()

def test_arity():
  assert M.arity == 1

@raises(Exception)
def test_wrong_realm():
  M.Apply(Group.QuickCreate(3, 4))

@raises(Exception)
def test_wrong_arity():
  M.Apply(Integer(2), Integer(4))

def test_apply():
  assert 6 == M.Apply(Integer(5)).magnitude
  
def test_inverse_mapping():
  m2 = M.Inverse()
  m3 = M.Inverse()
  assert m2 == m3
  assert 6 == m2.Apply(Integer(7)).magnitude
  assert m2.Inverse() == M
  
class M_no_inv(Mapping):
  realm = Integer
  arity = 1
  
  @staticmethod
  def fn(i):
    return Integer(i.magnitude + 1)

@raises(Exception)
def test_inverting_non_invertible():
  M_no_inv.Inverse()
  
def test_is_reversible():
  assert M.IsReversible()
  assert not M_no_inv.IsReversible()
  
class M_Fib(Mapping):
  realm = Integer
  arity = 2
  
  @staticmethod
  def fn(i, j):
    return Integer(i.magnitude + j.magnitude)
  
  @staticmethod
  def rev_fn(i, j):
    return Integer(j.magnitude - i.magnitude)

@raises(Exception)
def test_wrong_arity2():
  M_Fib.Apply(Integer(2))

def test_apply2():
  assert 6 == M_Fib.Apply(Integer(2), Integer(4)).magnitude

def test_reverse_multiarity():
  assert 2 == M_Fib.Inverse().Apply(Integer(2), Integer(4)).magnitude