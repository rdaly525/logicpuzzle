import timeit

import hwtypes as ht
import pysmt.shortcuts as smt
import typing as tp
import z3
from hwtypes import smt_utils as fc
import itertools as it

_cache = {}

def _to_int(val):
    if isinstance(val, z3.BoolRef):
        return bool(val)
    elif isinstance(val, z3.BitVecRef):
        return int(val.as_long())
    else:
        try:
            return int(val.constant_value())
        except Exception as e:
            print(f"Error converting {val} of type {type(val)}: {e}")
            raise


class SMTConstraintProblem:
    def __init__(self, default_bvlen: int = 32, z3_solver=False, timeout=15000, logic=None, solver_name='z3', verbose=False):
        self.default_bvlen = default_bvlen
        self.isZ3 = z3_solver
        self.BitVector = ht.z3BitVector if self.isZ3 else ht.SMTBitVector
        self.BV = self.BitVector[self.default_bvlen]
        self.Bit = ht.z3Bit if self.isZ3 else ht.SMTBit
        self.fc_constraints = []
        self._unique_vars = []
        self._free_vars = []
        self.verbose = verbose
        self.solver_info = {
            'z3_solver': z3_solver,
            'timeout': timeout,
            'logic': logic,
            'solver_name': solver_name,
        }
        # Hack to fix the smt_utils typing
        if self.isZ3:
            fc.SMTBit = ht.z3Bit
        else:
            fc.SMTBit = ht.SMTBit
        self.reset_solver()

    def reset_solver(self):
        if self.isZ3:
            self.solver = z3.Solver()
            self.solver.set("timeout", self.solver_info['timeout'])
        else:
            self.solver = smt.Solver()

    # Unique vars are variables that make the formula unique
    @property
    def unique_vars(self):
        return self._unique_vars

    # Free vars are all the variables in the formula
    @property
    def free_vars(self):
        return self._free_vars

    def new_var(self, name, bvlen=None, is_unique=True):
        """
        Create a new variable and add it to the solver.

        Parameters
        ----------
        name : str
            The name of the variable.
        bvlen : int, optional
            The bitvector length of the variable. If None, the default bvlen is used. 
            If bvlen is 0, the variable is a boolean variable.
        is_unique : bool, optional
            Whether the variable is unique.

        Returns
        -------
        ht.SMTBit
            The new variable.
        """
        if bvlen is None:
            bvlen = self.default_bvlen
        bv_info = int(self.isZ3)
        key = f"{name}_{bv_info}_{bvlen}"
        var_name = f"{name}_{bvlen}"
        if key in _cache:
            v =  _cache[key]
        else:
            if bvlen==0:
                v = self.Bit(name=var_name)
            else:
                v = self.BV(name=var_name)
            _cache[key] = v
        # Always add to free vars
        self._free_vars.append(v.value)
        # Add to unique vars if requested
        if is_unique:
            self._unique_vars.append(v.value)
        return v

    def add_constraint(self, c: tp.Union['self.Bit', fc.FormulaConstructor]):
        """
        Add a constraint to the SMT solver.

        Parameters
        ----------
        c : Union[self.Bit, FormulaConstructor]
            The constraint to add. Can be either a Bit from this solver's type system
            or a FormulaConstructor object that can be converted to a Bit.

        Raises
        ------
        ValueError
            If c is not a valid constraint type.
        """
        if self.verbose:
            # Convert to fc.FormulaConstructor
            if not isinstance(c, fc.FormulaConstructor):
                c = fc.And([c])
            self.fc_constraints.append(c)
        if isinstance(c, fc.FormulaConstructor):
            c = c.to_hwtypes().value
        elif isinstance(c, self.Bit):
            c = c.value
        else:
            raise ValueError(f"Invalid constraint type: {type(c)}")
        if self.isZ3:
            self.solver.add(c)
        else:
            self.solver.add_assertion(c)

    # run_mode:
    #   Will return None if no solution found
    #   num_sols: int : >0 returns a generator that yields up to N of the optimal solutions. 0 returns all solutions
    def solve(self, num_sols: int = 1):
        if self.verbose:
            print("Constraints:")
            print(fc.And(self.fc_constraints).serialize())
        assert num_sols >= 0
        if num_sols == 0:
            return self.AllSAT()
        else:
            def generator():
                cnt = 0 
                for sol in self.AllSAT():
                    yield sol
                    cnt += 1
                    if cnt >= num_sols:
                        break
            return generator()

    def AllSAT(self):
        if self.isZ3:
            return self.z3AllSAT()
        else:
            return self.pysmtAllSAT()

    # A generator that yields all solutions
    def pysmtAllSAT(self):
        solver: smt.Solver = self.solver
        while solver.solve():
            full_sol = {v: _to_int(solver.get_value(v)) for v in self.free_vars}
            yield full_sol
            unique_sol = {v: solver.get_value(v) for v in self.unique_vars}
            # Construct sol
            partial_model = [smt.EqualsOrIff(var, val) for var, val in unique_sol.items()]
            solver.add_assertion(smt.Not(smt.And(partial_model)))

    def z3AllSAT(self):
        unique_vars = [v.value for v in self.unique_vars]
        solver: z3.Solver = self.solver
        while solver.check() == z3.sat:
            m = solver.model()
            full_sol = {v: _to_int(m.eval(v)) for v in self.free_vars}
            yield full_sol
            unique_sol = {v: m.eval(v) for v in unique_vars}
            # Construct sol
            blocking_clause = z3.Not(z3.And([v == unique_sol[v] for v in unique_vars]))
            solver.add(blocking_clause)


    # Common operations

    def hard_constraint(self, cons):
        return fc.And(cons).to_hwtypes()

    def gen_min(self, vals):
        min_val = self.BV(-1)
        for val in vals:
            min_val = (val < min_val).ite(val, min_val)
        return min_val

    def gen_min_pred(self, vals, preds):
        assert len(vals) == len(preds)
        min_val = self.BV(-1)
        for val, pred in zip(vals, preds):
            min_val = (pred & (val < min_val)).ite(val, min_val)
        return min_val

    def gen_max(self, vals):
        max_val = self.BV(0)
        for val in vals:
            max_val = (val > max_val).ite(val, max_val)
        return max_val

    def gen_total(self, vals, bvlen=None):
        if bvlen is None:
            BV = self.BV
        else:
            BV = self.BitVector[bvlen]
        return sum(vals, BV(0))

    def combine(self, vals, mode: str, preds=None):
        assert mode in ('min', 'max', 'total', 'min_pred')
        if mode == 'min':
            return self.gen_min(vals)
        elif mode == 'max':
            return self.gen_max(vals)
        elif mode == 'total':
            return self.gen_total(vals)
        elif mode == 'min_pred':
            assert preds is not None
            return self.gen_min_pred(vals, preds)

    def diff_circ(self, a, b, h_scale):
        a, b = self.BV(a), self.BV(b)
        circ_diff = (b > a).ite(a + self.BV(h_scale) - b, a - b)
        return circ_diff

    def L1_circ(self, a, b, h_scale):
        a, b = self.BV(a), self.BV(b)
        abs_diff = (a > b).ite(a - b, b - a)
        abs_diff2 = self.BV(h_scale) - abs_diff
        circ_diff = (abs_diff < abs_diff2).ite(abs_diff, abs_diff2)
        return circ_diff

    def L1(self, a, b):
        a, b = self.BV(a), self.BV(b)
        return (a.bvsge(b)).ite(a - b, b - a)

    def L2(self, a, b):
        a, b = self.BV(a), self.BV(b)
        return (a - b) * (a - b)

    def norm(self, vals: tp.Iterable[tp.Tuple], kind: str, h_scale):
        assert kind in ('diff', 'L1', 'L2', 'L1_circ', 'diff_circ')
        if kind == 'diff':
            return self.gen_total([self.BV(a) - self.BV(b) for a, b in vals])
        elif kind == 'diff_circ':
            return self.gen_total([self.diff_circ(a, b, h_scale) for a, b in vals])
        elif kind == 'L1':
            return self.gen_total([self.L1(a, b) for a, b in vals])
        elif kind == 'L1_circ':
            return self.gen_total([self.L1_circ(a, b, h_scale) for a, b in vals])
        elif kind == 'L2':
            return self.gen_total([self.L2(a, b) for a, b in vals])




# TODO: Implement this
#class SMTOptimizationProblem(SMTConstraintProblem):
#    def __init__(self, bvlen: int = 32, BitVector = ht.z3BitVector, timeout=15000):
#        super().__init__(bvlen, BitVector, timeout)
#        self.objs = []
#
#    def reset_solver(self):
#        if self.isZ3:
#            self.solver = z3.Optimize()
#        else:
#            self.solver = smt.Solver()
#        self.solver.set('timeout', self.timeout)
#
#    def add_obj(self, obj_info):
#        obj, bound, kind = obj_info
#        if kind == 'max':
#            self.solver.maximize(obj.value)
#            self.solver.add(obj.value <= bound)
#        elif kind == 'min':
#            self.solver.minimize(obj.value)
#            self.solver.add(obj.value >= bound)
#        else:
#            raise ValueError(f"Invalid objective kind {kind}")
#        self.objs.append((obj, bound, kind))
#
#    def allSAT(self, thresholds, unique_vars, free_vars, prev_sol):
#        unique_vars = [v.value for v in unique_vars]
#        if prev_sol is not None:
#            blocking_clause = z3.Not(z3.And([v == prev_sol[v] for v in unique_vars]))
#            self.solver.add(blocking_clause)
#            yield prev_sol
#        self.solver.add(fc.And([thresh==obj for thresh, (obj, _, _) in zip(thresholds, self.objs)]).to_hwtypes().value)
#        while self.solver.check() == z3.sat:
#            m = self.solver.model()
#            full_sol = {v: int(m.eval(v).as_long()) for v in free_vars}
#            yield full_sol
#            blocking_clause = z3.Not(z3.And([v == m.eval(v) for v in unique_vars]))
#            self.solver.add(blocking_clause)
#
#
#    # Returns the soft constraint version of the set of constraints (weighted equally)
#    def soft_constraint(self, cons):
#        return self.gen_total([c.ite(self.BV(1), self.BV(0)) for c in cons])
#
#    # multi-objective optimization using lexographic method
#    # returns model if SAT, None if UNSAT
#    def optimize(self, no_opt=False, verbose=True):
#        start_time = timeit.default_timer()
#        self.solver.set('timeout', self.timeout)
#        if self.solver.check() == z3.sat:
#            delta = timeit.default_timer() - start_time
#            if verbose:
#                print("SAT", round(delta,2), flush=True)
#            m = self.solver.model()
#            sol = {v: z3const(m.eval(v)) for v in free_vars}
#            if no_opt:
#                return [], sol
#            return [z3const(m.eval(obj.value)) for obj, _, _ in self.objs], sol
#        else:
#            delta = timeit.default_timer() - start_time
#            print("UNSAT", round(delta, 2), flush=True)
#            return None, None
#
#    # run_mode:
#    #   Will return None if no solution found
#    #   "opt": returns the best thresholds as a tuple of ints
#    #   "one": returns one optimal coloring
#    #   "all": returns a generator that yields all optimal solutions
#    #   N : int : returns a generator that yields the N of the optimal solutions
#    def solve(self, run_mode: tp.Union[str, int], verbose=False, no_opt=False):
#        if isinstance(run_mode, int):
#            num_sols = run_mode
#            run_mode = "all"
#        elif run_mode not in ["all", "one", "opt"]:
#            raise ValueError(f"Unknown run mode, {run_mode}")
#        else:
#            num_sols = None
#
#        if verbose:
#            print("Constraints:")
#            for c in self.constraints:
#                print(c.serialize())
#            print("Objectives:")
#            for o in self.objs:
#                print(o)
#            print("Finding optimal solution", flush=True)
#            print('Optimizing', flush=True)
#        best_thresholds, sol = self.optimize(self.free_vars, no_opt=no_opt)
#
#        if best_thresholds is None:
#            if verbose:
#                print("No solution found")
#            return None
#        if verbose:
#            print("Best thresholds", best_thresholds)
#        if run_mode == "opt":
#            return best_thresholds
#        if run_mode == "one":
#            return sol
#
#        assert run_mode == "all"
#        def generator():
#            for i, new_sol in enumerate(it.islice(self.allSAT(best_thresholds, self.unique_vars, self.free_vars, sol), num_sols)):
#                yield new_sol
#        return generator



#def is_sat(formula: ht.SMTBit, solver_name='z3', logic=None):
#    return smt.is_sat(formula.value, solver_name=solver_name, logic=logic)
#
#def get_model(query: ht.SMTBit, solver_name='z3', logic=None):
#    query = smt.simplify(query.value)
#    vars = query.get_free_variables()
#    model = smt.get_model(smt.And(query), solver_name=solver_name, logic=logic)
#    if model:
#        return {v: int(model.get_value(v).constant_value()) for v in vars}
#    return False
#
#def optimize(
#    constraints: tp.List[ht.SMTBit],
#    objs: tp.List[tp.Tuple[ht.BitVector, int, str]],
#    free_vars,
#    use_z3opt: bool=False,
#    timeout=15000,
#):
#    if use_z3opt:
#        return z3_optimize(constraints, objs, free_vars, timeout)
#    else:
#        return pysmt_optimize(constraints, objs, free_vars, timeout)
#
#
## multi-objective optimization using lexographic method
#def pysmt_optimize(constraints: tp.List[ht.SMTBit], objs: tp.List[tp.Tuple[ht.BitVector, int, str]], free_vars, timeout):
#    '''maximizes objective subject to constraints using binary search'''
#
#    step_size = 1
#    solver_name = 'z3'
#    if step_size != 1:
#        raise NotImplementedError("Binary search with step size != 1 not implemented")
#
#    if not all(kind in ['max', 'min'] for _, _, kind in objs):
#        raise ValueError(f"Invalid objective kind")
#
#    with smt.Solver(name=solver_name) as solver:
#        for i, c in enumerate(constraints):
#            solver.add_assertion(c.to_hwtypes().value)
#        # edge case if no objectives
#        if len(objs) == 0:
#            is_sat = solver.solve()
#            if not is_sat:
#                return None, None
#            model = solver.get_model()
#            sol = {v: int(model.get_value(v).constant_value()) for v in free_vars}
#            return [], sol
#        best_thresholds = []
#        for obj_i, (obj, bound, kind) in enumerate(objs):
#            # check if constraints are satisfiable
#            is_sat = solver.solve()
#            if not is_sat:
#                assert obj_i == 0
#                return None, None
#            # initialize lower/upper bound of binary search
#            best_threshold = int(solver.get_value(obj.value).constant_value())
#            model = solver.get_model()
#
#            # Do binary search
#            if kind=="max":
#                left, right = best_threshold, bound
#                while left <= right:
#                    middle = (left + right) // 2
#                    threshold = middle
#                    solver.push()
#                    solver.add_assertion((obj >= threshold).value)
#                    is_sat = solver.solve()
#                    if is_sat: # went too low
#                        left = middle + step_size
#                        best_threshold = int(solver.get_value(obj.value).constant_value())
#                        model = solver.get_model()
#                        if best_threshold > left:
#                            left = best_threshold
#                    else:  # went too high
#                        right = middle - step_size
#                    solver.pop()
#            else:
#                assert kind == "min"
#                left, right = bound, best_threshold
#                while left <= right:
#                    middle = (left + right) // 2
#                    threshold = middle
#                    solver.push()
#                    solver.add_assertion((obj <= threshold).value)
#                    is_sat = solver.solve()
#                    if is_sat: # went too high
#                        best_threshold = int(solver.get_value(obj.value).constant_value())
#                        model = solver.get_model()
#                        right = middle - step_size
#                        if best_threshold < right:
#                            right = best_threshold
#                    else: # went too low
#                        left = middle + step_size
#                    solver.pop()
#
#            best_thresholds.append(best_threshold)
#            solver.add_assertion((obj == best_threshold).value)
#        sol = {v: int(model.get_value(v).constant_value()) for v in free_vars}
#    return best_thresholds, sol
#
#def z3const(val):
#    if isinstance(val, z3.BoolRef):
#        return bool(val)
#    elif isinstance(val, z3.BitVecRef):
#        return int(val.as_long())
#
#
## multi-objective optimization using lexographic method
## returns model if SAT, None if UNSAT
#def z3_optimize(constraints: tp.List[ht.z3Bit], objs: tp.List[tp.Tuple[ht.z3BitVector, int, str]], free_vars, timeout):
#    s = z3.Optimize()
#    s.set("timeout", timeout)
#    print('Adding constraints', flush=True)
#    for c in constraints:
#        s.add(c.to_hwtypes().value)
#    for o, bound, kind in objs:
#        if kind == 'max':
#            s.maximize(o.value)
#            s.add(o.value <= bound)
#        elif kind == 'min':
#            s.minimize(o.value)
#            s.add(o.value >= bound)
#        else:
#            raise ValueError(f"Invalid objective kind {kind}")
#    print('Real Solve', flush=True)
#    start_time = timeit.default_timer()
#    if s.check() == z3.sat:
#        delta = timeit.default_timer() - start_time
#        print("SAT", round(delta,2), flush=True)
#        m = s.model()
#        sol = {v: z3const(m.eval(v)) for v in free_vars}
#        return [m.eval(obj.value).as_long() for obj, _, _ in objs], sol
#    else:
#        delta = timeit.default_timer() - start_time
#        print("UNSAT", round(delta, 2), flush=True)
#        return None, None
#
#
#
#def z3AllSAT(f: ht.SMTBit, unique_vars, free_vars, prev_sol=None):
#    f = f.value
#    unique_vars = [v.value for v in unique_vars]
#    s = z3.Solver()
#    s.add(f)
#    if prev_sol is not None:
#        blocking_clause = z3.Not(z3.And([v == prev_sol[v] for v in unique_vars]))
#        s.add(blocking_clause)
#        yield prev_sol
#    while s.check() == z3.sat:
#        m = s.model()
#        full_sol = {v: int(m.eval(v).as_long()) for v in free_vars}
#        yield full_sol
#        blocking_clause = z3.Not(z3.And([v == m.eval(v) for v in unique_vars]))
#        s.add(blocking_clause)
#
#def pysmtAllSAT(f: ht.SMTBit, unique_vars, free_vars, prev_sol=None):
#    f = f.value
#    unique_vars = [v.value for v in unique_vars]
#    E_vars = f.get_free_variables()
#    assert all(v in E_vars for v in unique_vars)
#    with smt.Solver(logic=None, name='z3') as solver:
#        solver.add_assertion(f)
#        if prev_sol is not None:
#            #Hack
#            blocking_clause = fc.And([ht.SMTBitVector[32](v) == prev_sol[v] for v in unique_vars]).to_hwtypes()
#            solver.add_assertion(smt.Not(blocking_clause.value))
#            yield prev_sol
#        while solver.solve():
#            full_sol = {v: int(solver.get_value(v).constant_value())
#                        for v in free_vars}
#            yield full_sol
#            unique_sol = {v: solver.get_value(v) for v in unique_vars}
#            # Construct sol
#            blocking_clause = smt.Bool(True)
#            for var, val in unique_sol.items():
#                blocking_clause = smt.And(blocking_clause, smt.Equals(var, val))
#            solver.add_assertion(smt.Not(blocking_clause))
#