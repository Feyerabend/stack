"""
Chapter 6, Exercise 3 — solution code.

Run sum_to for n = 3 and measure the continuation. (a) record len(kont) at each
recursive call; (b) confirm it does not grow with n (tail form) and point to the
responsible line in step_ret; (c) rewrite in non-tail form n + sum_to(...) and
show the continuation grows linearly in n.

How to run:   python3 ex03_tco_kont.py
Expected:     "tail: max kont flat across n (…); non-tail: grows with n (…)"

(b) WHY TAIL IS FLAT. In the tail form, the recursive call is the whole else
    branch — nothing is pending after it. The responsible behaviour is in
    apply(): a closure application returns Eval(body, new_env, kont) with the
    SAME kont it was handed — no frame is pushed for the call. (Equivalently, in
    step_ret the IfF frame is consumed by choosing the branch, and the branch's
    tail call adds nothing.) So the machine re-enters sum_to's body with the
    continuation it already had: bounded space, a real loop.

(c) WHY NON-TAIL GROWS. In `n + sum_to(n-1)`, the `+` must happen AFTER the call
    returns, so evaluating it leaves a BinOpRF frame (holding the left value n,
    waiting for the right) on the continuation before the recursive call. One
    such frame is added per call, so |kont| grows linearly in n — the classic
    stack growth tail-call elimination removes.
"""

from _harness import setup, run_states, max_kont_depth

TAIL = """module M
fn sum_to(n : Int, acc : Int) : Int =
  if n == 0 then acc else sum_to(n - 1, acc + n)
fn main(io : IO) : Int = sum_to({N}, 0)
"""

NONTAIL = """module M
fn sum_to(n : Int) : Int =
  if n == 0 then 0 else n + sum_to(n - 1)
fn main(io : IO) : Int = sum_to({N})
"""


def max_kont_for(template, n):
    env, m = setup(template.format(N=n))
    states, result = run_states(env, m)
    return max_kont_depth(states), result


if __name__ == "__main__":
    ns = [1, 3, 5, 10]
    tail = {n: max_kont_for(TAIL, n) for n in ns}
    nontail = {n: max_kont_for(NONTAIL, n) for n in ns}

    # correctness: both compute 1+...+n = n(n+1)/2
    for n in ns:
        assert tail[n][1].n == n * (n + 1) // 2
        assert nontail[n][1].n == n * (n + 1) // 2

    tail_depths = {n: d for n, (d, _) in tail.items()}
    nontail_depths = {n: d for n, (d, _) in nontail.items()}

    # (b) tail: max kont depth is constant across n
    assert len(set(tail_depths.values())) == 1, tail_depths
    # (c) non-tail: max kont depth strictly increases with n
    ds = [nontail_depths[n] for n in ns]
    assert all(a < b for a, b in zip(ds, ds[1:])), nontail_depths

    print(f"tail: max kont flat across n ({tail_depths}); "
          f"non-tail: grows with n ({nontail_depths})")
