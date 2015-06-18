
import pyomo.environ as po
import components as cp

# create energy system components
bus1 = cp.Bus(uid="b1", type="coal")
bus2 = cp.Bus(uid="b2", type="elec")
bus3  = cp.Bus(uid="b3", type="th")
t1 = cp.Transformer(uid="t1",inputs=[bus1], outputs=[bus2])
t2 = cp.Transformer(uid="t2",inputs=[bus1], outputs=[bus2])
t3 = cp.Transformer(uid="t3",inputs=[bus1], outputs=[bus2,bus3])
t4 = cp.Transformer(uid="t4",inputs=[bus1], outputs=[bus2,bus3])

busses = [bus1, bus2, bus3]
all_trans = [t1, t2, t3]
s_transformers = [t1,t2]
s_chps = [t3,t4]

# should be calculated automatically of course
edges = [('b1','t1'),('b1','t2'),('b1','t3'),
      ('t1','b2'),('t2','b2'),('t3','b2'),
      ('t3','b3'),('b2','s1'),('b1','t4'),('t4','b2'),('t4','b3')]

# create pyomo model instance
m = po.ConcreteModel()

# create pyomo sets
m.busses = po.Set(initialize=[b.uid for b in busses])
m.s_transformers = po.Set(initialize=[t.uid for t in s_transformers])
m.s_chps = po.Set(initialize=[t.uid for t in s_chps])
m.edges = po.Set(dimen=2, initialize=edges)

# create variable for edges
m.w = po.Var(m.edges)

## bus balance forall b in busses
def bus_rule(m, e):
  expr = 0
  expr += -sum(m.w[(i,j)] for (i,j) in m.edges if i==e)
  expr += +sum(m.w[(i,j)] for (i,j) in m.edges if j==e)
  return(expr, 0)
m.bus_constr = po.Constraint(m.busses, rule=bus_rule)


# simple transformer model containing the constraints for simple transformers
def simple_transformer_model(m):
  """
  :param m: pyomo model instance
  """
  # temp set with input uids for every simple chp e in s_transformers
  # (does not need to be a pyomo object of class Set(), but can be a dict m.I
  # as attribute of m as well. Depends of how it is used again. Same for m.O)
  m.I = po.Set(m.s_transformers,
                initialize=[t.inputs[0].uid for t in s_transformers])
  # set with output uids for every simple transformer e in s_transformers
  m.O = po.Set(m.s_transformers,
                initialize=[t.outputs[0].uid for t in s_transformers])

  def eta_rule(m, e):
    expr = 0
    expr += m.w[m.I[e], e] * 0.9
    expr += - m.w[e, m.O[e]]
    return(expr,0)
  m.s_transformer_eta_constr = po.Constraint(m.s_transformers, rule=eta_rule)

  # to avoid pyomo warnings if m.I is already defined for other components
  del m.I, m.O

# simple chp model containing the constraints for simple chps
def simple_chp_model(m):
  """
  """
  # temp set with input uids for every simple chp e in s_chps
  m.I = po.Set(m.s_chps,
                initialize=[t.inputs[0].uid for t in s_chps])
  # set with output uids for every simple chp e in s_chps
  m.O = po.Set(m.s_chps, ordered=True,
                initialize=[t.outputs[i].uid for t in s_chps
                                             for i in range(len(t.outputs))])
  # constraint for transformer energy balance
  def eta_rule(m, e):
    expr = 0
    expr += m.w[m.I[e], e]
    expr += -sum(m.w[e, o] for o in m.O[e]) / 0.8
    return(expr,0)
  m.s_chp_eta_constr = po.Constraint(m.s_chps, rule=eta_rule)

  # additional constraint for power to heat ratio of simple chp components
  def power_to_heat_rule(m, e):
    expr = 0
    expr += m.w[e, m.O[e][0]]
    expr += -m.w[e, m.O[e][1]] * 0.6
    return(expr,0)
  m.s_chp_pth_constr = po.Constraint(m.s_chps, rule=power_to_heat_rule)

  # to avoid pyomo warnings if m.I is already defined for other components
  del m.I, m.O

# "call" the models to add the constraints to opt-problem
simple_chp_model(m)
simple_transformer_model(m)

m.pprint()