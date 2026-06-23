"""
Lark interference graph — built from per-instruction liveness.

A node is a Tmp name. Interference edge (u, v): u and v are simultaneously
live at some program point and cannot share a register.
A copy edge (u, v): u = v (IAssign with Tmp src) — candidates for coalescing.

Build algorithm (Appel §11.1, adapted):
  For each basic block, scan instructions in REVERSE order:
    • For each def d:
        add interference edges between d and every variable in `live`
        (for copy instructions: skip d–src edge; record as copy instead)
    • Update: live = (live – defs) ∪ uses
  After the block backward pass, `live` = live_in[block].
  Add a clique for that set to capture simultaneously-live variables that
  are never "defined" within any block (i.e., function parameters and
  variables live across a join with no intervening definition).
"""

from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from dataclasses import dataclass, field
from tac import Tmp, Instr, TAC, IAssign
from cfg import CFG, cfg_of_tac
from liveness import Liveness, analyse, defs, uses


# ── Data structure ─────────────────────────────────────────────────────────────

@dataclass
class IGraph:
    fn_name: str
    nodes:   set[str]            = field(default_factory=set)
    interf:  dict[str, set[str]] = field(default_factory=dict)  # symmetric
    copies:  dict[str, set[str]] = field(default_factory=dict)  # symmetric

    def _ensure(self, name: str) -> None:
        if name not in self.interf:
            self.nodes.add(name)
            self.interf[name] = set()
            self.copies[name] = set()

    def add_interf(self, u: str, v: str) -> None:
        if u == v:
            return
        self._ensure(u);  self._ensure(v)
        self.interf[u].add(v)
        self.interf[v].add(u)

    def add_copy(self, u: str, v: str) -> None:
        if u == v:
            return
        self._ensure(u);  self._ensure(v)
        self.copies[u].add(v)
        self.copies[v].add(u)

    def interferes(self, u: str, v: str) -> bool:
        return v in self.interf.get(u, set())

    def degree(self, u: str) -> int:
        return len(self.interf.get(u, set()))

    def neighbours(self, u: str) -> set[str]:
        return self.interf.get(u, set())


# ── Builder ────────────────────────────────────────────────────────────────────

def build_igraph(cfg: CFG, lv: Liveness) -> IGraph:
    ig = IGraph(fn_name=cfg.fn_name)

    # Seed all node names so the graph is complete even for isolated variables
    for blk in cfg:
        for name in lv.live_in[blk.label]:
            ig._ensure(name)
        for instr in blk.instrs:
            for name in defs(instr) | uses(instr):
                ig._ensure(name)

    for blk in cfg:
        live: set[str] = set(lv.live_out[blk.label])

        for instr in reversed(blk.instrs):
            d_set = defs(instr)
            u_set = uses(instr)

            # Detect copy:  dst = src_tmp  (IAssign with Tmp source)
            is_copy = isinstance(instr, IAssign) and isinstance(instr.src, Tmp)
            copy_src: str | None = instr.src.name if is_copy else None

            if is_copy:
                # Remove the copy source from live before adding edges so that
                # dst and src are copy-related, not interference-related.
                live_for_edges = live - {copy_src}
                for d in d_set:
                    ig.add_copy(d, copy_src)
                    for x in live_for_edges:
                        if x != d:
                            ig.add_interf(d, x)
            else:
                for d in d_set:
                    for x in live:
                        if x != d:
                            ig.add_interf(d, x)

            live = (live - d_set) | u_set

        # After the backward pass, live == live_in[blk].
        # Add clique edges for variables simultaneously live at block entry —
        # covers parameters and variables live across a join with no
        # definition in this block.
        live_list = list(live)
        for i in range(len(live_list)):
            for j in range(i + 1, len(live_list)):
                ig.add_interf(live_list[i], live_list[j])

    return ig


def igraph_of_tac(tac: TAC) -> list[IGraph]:
    graphs = []
    for cfg in cfg_of_tac(tac):
        lv = analyse(cfg)
        graphs.append(build_igraph(cfg, lv))
    return graphs


# ── Pretty printer ─────────────────────────────────────────────────────────────

def pretty_igraph(ig: IGraph) -> str:
    n_edges = sum(len(v) for v in ig.interf.values()) // 2
    lines   = [f"IGraph {ig.fn_name!r}  {len(ig.nodes)} nodes  {n_edges} edges"]
    for node in sorted(ig.nodes):
        nbrs = sorted(ig.interf[node])
        cps  = sorted(ig.copies[node])
        row  = f"  {node:14s} deg={ig.degree(node):2d}"
        if nbrs: row += f"  interferes: {{{', '.join(nbrs)}}}"
        if cps:  row += f"  copies: {{{', '.join(cps)}}}"
        lines.append(row)
    return "\n".join(lines)


# ── CLI ────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import parser as _parser
    import infer  as _infer
    from lower import lower

    if len(sys.argv) < 2:
        print("usage: python3 src/igraph.py <file.lark>", file=sys.stderr)
        sys.exit(1)

    path  = sys.argv[1]
    prog  = _parser.parse_file(path)
    tprog = _infer.typecheck(prog, source_file=path)
    tac   = lower(tprog)
    for ig in igraph_of_tac(tac):
        print(pretty_igraph(ig))
        print()
