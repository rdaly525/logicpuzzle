import timeit

import hwtypes as ht
import pysmt.shortcuts as smt
import typing as tp
import z3
from hwtypes import smt_utils as fc
import itertools as it
from contextlib import contextmanager

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
    def __init__(self, default_bvlen: int = 32, timeout=15000, logic=None, solver_name='z3', verbose=False):
        self.default_bvlen = default_bvlen
        self.BitVector = ht.SMTBitVector
        self.BV = self.BitVector[self.default_bvlen]
        self.Bit = ht.SMTBit
        self.fc_constraints = []
        self._unique_vars = []
        self._free_vars = []
        self.verbose = verbose
        self.solver_info = {
            'timeout': timeout,
            'logic': logic,
            'solver_name': solver_name,
        }
        fc.SMTBit = ht.SMTBit
        self.reset_solver()
        self._context_level = 0

    def reset_solver(self):
        self.solver = smt.Solver(
            name=self.solver_info['solver_name'],
            logic=self.solver_info['logic'],
            #timeout=self.solver_info['timeout']
        )

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
        key = f"{name}_{bvlen}"
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

    def is_sat(self):
        for _ in self.AllSAT():
            return True
        return False
    
    def is_unsat(self):
        return not self.is_sat()
    
    # Common operations


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

    def gen_total(self, vals: tp.Iterable[tp.Union[ht.SMTBit, ht.SMTBitVector]]) -> ht.SMTBitVector:
        # Calculate required bitwidth to prevent overflow
        max_bvlen = 0
        for val in vals:
            if isinstance(val, ht.SMTBitVector):
                max_bvlen = max(max_bvlen, val.size)
            elif isinstance(val, ht.SMTBit):
                max_bvlen = max(max_bvlen, 1)
        
        # For each value of size N bits, max value is 2^N - 1
        # With L values, max sum is L * (2^N - 1)
        # Need enough bits to represent L * (2^N - 1)
        # L * (2^N - 1) < 2^required_bvlen
        # required_bvlen = ceil(log2(L * (2^N - 1)))
        # Simplified: required_bvlen = N + ceil(log2(L))
        L = len(list(vals))
        required_bvlen = max_bvlen + (L-1).bit_length()
        BV = self.BitVector[required_bvlen]

        # Convert all values to BitVectors of required length
        converted_vals = []
        for val in vals:
            if isinstance(val, ht.SMTBit):
                converted_vals.append(BV(val.value))
            else:  # SMTBitVector
                converted_vals.append(val.zext(required_bvlen - val.size))

        return sum(converted_vals, BV(0))
    
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

    def L1(self, a, b):
        a, b = self.BV(a), self.BV(b)
        return (a.bvsge(b)).ite(a - b, b - a)

    def L2(self, a, b):
        a, b = self.BV(a), self.BV(b)
        return (a - b) * (a - b)

    @contextmanager
    def solve_context(self):
        """
        Context manager for temporary solver constraints.
        Pushes solver state on enter, pops on exit.
        
        Usage:
            with problem.solve_context():
                problem.add_constraint(...)
                result = problem.solve()
        """
        self.solver.push()
        self._context_level += 1
        try:
            yield self
        finally:
            self.solver.pop()
            self._context_level -= 1