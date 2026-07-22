"""
Lark CFG — control-flow graph built from a TAC Function.

Used by liveness analysis and the register allocator.

Block boundaries:
  • Index 0 is always a leader.
  • An ILabel instruction starts a new block (its name becomes the block label).
  • The instruction after any IJump / ICondJump / IReturn is a leader.

ILabel instructions are kept as the first instruction of their block so the
full body can be reconstructed; they contribute no defs or uses to liveness.
"""

from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from dataclasses import dataclass, field
from tac import (
    Function, Instr, TAC,
    ILabel, IJump, ICondJump, IReturn,
)


# -- Data structures --

@dataclass
class BasicBlock:
    label:  str
    instrs: list[Instr]         = field(default_factory=list)
    succs:  list[str]           = field(default_factory=list)
    preds:  list[str]           = field(default_factory=list)


@dataclass
class CFG:
    fn_name: str
    blocks:  dict[str, BasicBlock]   # label → block, definition order
    entry:   str                      # label of entry block
    exits:   list[str]                # labels of blocks ending with IReturn

    def __iter__(self):
        return iter(self.blocks.values())

    def block(self, label: str) -> BasicBlock:
        return self.blocks[label]


# -- Builder --

def build_cfg(fn: Function) -> CFG:
    body = fn.body

    if not body:
        lbl = "__entry__"
        return CFG(fn_name=fn.name,
                   blocks={lbl: BasicBlock(label=lbl)},
                   entry=lbl, exits=[])

    # Step 1 — find all leader indices
    leaders: set[int] = {0}
    for i, instr in enumerate(body):
        if isinstance(instr, ILabel):
            leaders.add(i)
        if isinstance(instr, (IJump, ICondJump, IReturn)) and i + 1 < len(body):
            leaders.add(i + 1)

    sorted_leaders = sorted(leaders)

    # Step 2 — slice body into BasicBlocks
    blocks_ordered: list[BasicBlock] = []
    for k, start in enumerate(sorted_leaders):
        end   = sorted_leaders[k + 1] if k + 1 < len(sorted_leaders) else len(body)
        slice_ = body[start:end]

        if isinstance(slice_[0], ILabel):
            lbl = slice_[0].name
        elif k == 0:
            lbl = "__entry__"
        else:
            lbl = f"__block_{k}__"   # should not occur in well-formed TAC

        blocks_ordered.append(BasicBlock(label=lbl, instrs=list(slice_)))

    # Step 3 — wire successor edges
    exits: list[str] = []
    for i, blk in enumerate(blocks_ordered):
        term = blk.instrs[-1] if blk.instrs else None
        if isinstance(term, IJump):
            blk.succs.append(term.label)
        elif isinstance(term, ICondJump):
            blk.succs.append(term.true_label)
            blk.succs.append(term.false_label)
        elif isinstance(term, IReturn):
            exits.append(blk.label)
        else:
            # fall-through to the next block
            if i + 1 < len(blocks_ordered):
                blk.succs.append(blocks_ordered[i + 1].label)

    # Step 4 — fill predecessor edges
    block_dict: dict[str, BasicBlock] = {b.label: b for b in blocks_ordered}
    for blk in blocks_ordered:
        for s in blk.succs:
            if s in block_dict:
                block_dict[s].preds.append(blk.label)

    return CFG(fn_name=fn.name,
               blocks=block_dict,
               entry=blocks_ordered[0].label,
               exits=exits)


def cfg_of_tac(tac: TAC) -> list[CFG]:
    return [build_cfg(fn) for fn in tac.functions]


# -- Pretty printer --

def pretty_cfg(cfg: CFG) -> str:
    from tac import _instr_str
    lines = [f"CFG {cfg.fn_name!r}  entry={cfg.entry!r}"]
    for blk in cfg.blocks.values():
        lines.append(f"  [{blk.label}]  preds={blk.preds}  succs={blk.succs}")
        for instr in blk.instrs:
            lines.append(f"      {_instr_str(instr).strip()}")
    return "\n".join(lines)


# -- CLI --

if __name__ == "__main__":
    import parser as _parser
    import infer  as _infer
    from lower import lower

    if len(sys.argv) < 2:
        print("usage: python3 src/cfg.py <file.lark>", file=sys.stderr)
        sys.exit(1)

    path  = sys.argv[1]
    prog  = _parser.parse_file(path)
    tprog = _infer.typecheck(prog, source_file=path)
    tac   = lower(tprog)
    for cfg in cfg_of_tac(tac):
        print(pretty_cfg(cfg))
        print()
