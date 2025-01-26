import pygame
import random
import sys
from typing import List, Set, Tuple
from dataclasses import dataclass
from logicpuzzles.board import Board, Face
from hwtypes import SMTBitVector as SBV
from hwtypes import SMTBit
import pysmt.shortcuts as smt
from pysmt.logics import BV
from ..utils.smt_utils import SMTConstraintProblem
import typing as tp

@dataclass
class MineCell(Face):
    """Represents a cell in the minesweeper grid"""
    is_mine: bool = False
    adjacent_mines: int = 0
    
    def __str__(self):
        if self.is_mine:
            return 'X'
        return '.' if self.adjacent_mines == 0 else str(self.adjacent_mines)

class MineBoard(Board):
    face_t = MineCell

