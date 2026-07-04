/*
 * eval.c — Normalisation by Evaluation (NbE)
 *
 * The idea: instead of defining reduction rules on syntax (rewrite trees),
 * we evaluate terms into a semantic domain (Val) using the *host language's*
 * function application for beta reduction, then "quote" back to syntax.
 *
 *   nbe_eval : Env -> Term -> Val     (Term → semantic value)
 *   nbe_vapp : Val  -> Val  -> Val    (semantic function application)
 *   nbe_quote: depth -> Val -> Term   (semantic value → normal form)
 *
 * The key insight: a VL_LAM closure IS a function in C. Applying it is just
 * evaluating its body in an extended environment. No substitution needed.
 *
 * Normal forms: a term is in normal form when nbe_eval followed by nbe_quote
 * produces the same tree.  nbe_nf(a,t) = nbe_quote(a,0, nbe_eval(a,NULL,t)).
 *
 * Neutrals: when a eliminator (natrec, case, fst, ...) is applied to a
 * variable (not a constructor), it cannot fire.  We build a VL_NEUTRAL value
 * that records the head variable and the accumulated eliminators (the spine).
 * nbe_quote replays the spine back to syntax.
 */
#include <stdio.h>
#include <stdlib.h>
#include "eval.h"
#include "defs.h"

/* ── Environment lookup */

static Val *env_lookup(Arena *a, Env *env, int idx, int orig) {
    for (; env && idx > 0; env = env->next, idx--);
    if (!env) {
        fprintf(stderr, "eval: free variable at de Bruijn index %d\n", orig);
        return vl_neutral(a, -(orig + 1), NULL);
    }
    return env->val;
}

/* ── Projections on values */

Val *nbe_vfst(Arena *a, Val *v) {
    if (v->tag == VL_PAIR)    return v->pair.fst;
    if (v->tag == VL_NEUTRAL)
        return vl_neutral(a, v->neutral.lvl, spine_fst(a, v->neutral.spine));
    fprintf(stderr, "vfst: not a pair\n"); exit(1);
}

Val *nbe_vsnd(Arena *a, Val *v) {
    if (v->tag == VL_PAIR)    return v->pair.snd;
    if (v->tag == VL_NEUTRAL)
        return vl_neutral(a, v->neutral.lvl, spine_snd(a, v->neutral.spine));
    fprintf(stderr, "vsnd: not a pair\n"); exit(1);
}

/* ── Nat recursor */

Val *nbe_vnatrec(Arena *a, Val *motive, Val *base, Val *step, Val *n) {
    if (n->tag == VL_ZERO)
        return base;
    if (n->tag == VL_SUCC) {
        Val *prev = nbe_vnatrec(a, motive, base, step, n->succ);
        return nbe_vapp(a, nbe_vapp(a, step, n->succ), prev);
    }
    if (n->tag == VL_NEUTRAL)
        return vl_neutral(a, n->neutral.lvl,
                          spine_natrec(a, motive, base, step,
                                       n->neutral.spine));
    fprintf(stderr, "vnatrec: not a Nat\n"); exit(1);
}

/* ── Bool eliminator */

Val *nbe_vboolrec(Arena *a, Val *motive, Val *tcase, Val *fcase, Val *b) {
    if (b->tag == VL_TRUE)    return tcase;
    if (b->tag == VL_FALSE)   return fcase;
    if (b->tag == VL_NEUTRAL)
        return vl_neutral(a, b->neutral.lvl,
                          spine_boolrec(a, motive, tcase, fcase,
                                        b->neutral.spine));
    fprintf(stderr, "vboolrec: not a Bool\n"); exit(1);
}

/* ── Empty eliminator (ex falso) */

Val *nbe_vabort(Arena *a, Val *motive, Val *e) {
    if (e->tag == VL_NEUTRAL)
        return vl_neutral(a, e->neutral.lvl,
                          spine_abort(a, motive, e->neutral.spine));
    fprintf(stderr, "vabort: scrutinee is not neutral (Empty has no constructors)\n");
    exit(1);
}

/* ── Circle recursor
 *
 * β-rule: S1rec B b l base ≡ b  (fires when scrut = VL_BASE)
 * Stays neutral on any other neutral scrutinee.
 */

Val *nbe_vcircrec(Arena *a, Val *motive, Val *base_case, Val *loop_case, Val *s) {
    if (s->tag == VL_BASE)    return base_case;
    if (s->tag == VL_NEUTRAL)
        return vl_neutral(a, s->neutral.lvl,
                          spine_circrec(a, motive, base_case, loop_case,
                                        s->neutral.spine));
    fprintf(stderr, "vcircrec: not a circle value\n"); exit(1);
}

/* ── Truncation eliminator
 *
 * β-rule: truncrec A B f (trint A a) ≡ f a
 * trint A a is a neutral with lvl=TRINT_CONST_LVL and spine [SP_APP a, SP_APP A].
 * (spine head = most recently applied = a; next = A)
 */

Val *nbe_vtruncret(Arena *a, Val *ty_a, Val *ty_b, Val *func, Val *t) {
    if (t->tag == VL_NEUTRAL && t->neutral.lvl == TRINT_CONST_LVL) {
        Spine *sp = t->neutral.spine;
        if (sp && sp->kind == SP_APP &&
            sp->next && sp->next->kind == SP_APP &&
            !sp->next->next)
            return nbe_vapp(a, func, sp->val);  /* f a */
    }
    if (t->tag == VL_NEUTRAL)
        return vl_neutral(a, t->neutral.lvl,
                          spine_truncrec(a, ty_a, ty_b, func, t->neutral.spine));
    fprintf(stderr, "vtruncret: scrutinee is not a truncated value\n");
    exit(1);
}

/* ── Sum eliminator */

Val *nbe_vcase(Arena *a, Val *motive, Val *lcase, Val *rcase, Val *s) {
    if (s->tag == VL_INL)    return nbe_vapp(a, lcase, s->inj);
    if (s->tag == VL_INR)    return nbe_vapp(a, rcase, s->inj);
    if (s->tag == VL_NEUTRAL)
        return vl_neutral(a, s->neutral.lvl,
                          spine_casesplit(a, motive, lcase, rcase, s->neutral.spine));
    fprintf(stderr, "vcase: not a Sum value\n"); exit(1);
}

/* ── Unit eliminator */

Val *nbe_vunitrec(Arena *a, Val *motive, Val *base, Val *s) {
    if (s->tag == VL_STAR)    return base;
    if (s->tag == VL_NEUTRAL)
        return vl_neutral(a, s->neutral.lvl,
                          spine_unitrec(a, motive, base, s->neutral.spine));
    fprintf(stderr, "vunitrec: not a Unit value\n"); exit(1);
}

/* ── W-type eliminator
 *
 * β-rule: wrec P s (sup a f) ≡ s a f (λb. wrec P s (f b))
 *
 * The IH λb. wrec P s (f b) is built as a VL_LAM whose body is a synthetic
 * TM_WREC term.  The closure captures [children, step, motive] so that when
 * applied to b the env is [b(0), children(1), step(2), motive(3)].
 */

Val *nbe_vwrec(Arena *a, Val *motive, Val *step, Val *w) {
    if (w->tag == VL_SUP) {
        Val *label    = w->pair.fst;
        Val *children = w->pair.snd;
        Env *captured = env_cons(a, children,
                        env_cons(a, step,
                        env_cons(a, motive, NULL)));
        /* body: wrec(VAR 3, VAR 2, APP(VAR 1, VAR 0)) */
        Term *body = tm_wrec(a, tm_var(a, 3), tm_var(a, 2),
                             tm_app(a, tm_var(a, 1), tm_var(a, 0)));
        Val *ih = vl_lam(a, "b", captured, body);
        return nbe_vapp(a, nbe_vapp(a, nbe_vapp(a, step, label), children), ih);
    }
    if (w->tag == VL_NEUTRAL)
        return vl_neutral(a, w->neutral.lvl,
                          spine_wrec(a, motive, step, w->neutral.spine));
    fprintf(stderr, "vwrec: not a W-type value\n"); exit(1);
}

/* ── J eliminator */

Val *nbe_vj(Arena *a, Val *ty, Val *lhs, Val *motive,
            Val *base, Val *endpoint, Val *proof) {
    if (proof->tag == VL_REFL) return base;
    if (proof->tag == VL_NEUTRAL)
        return vl_neutral(a, proof->neutral.lvl,
                          spine_j(a, ty, lhs, motive, base, endpoint,
                                  proof->neutral.spine));
    fprintf(stderr, "vj: not an identity proof\n"); exit(1);
}

/* ── Inductive family eliminator */

Val *nbe_vindrec(Arena *a, int fam_idx, Val *motive, Val **cases, Val *scrut) {
    if (scrut->tag == VL_INDCON) {
        if (scrut->indcon.fam_idx != fam_idx) {
            fprintf(stderr,
                    "vindrec: scrutinee is constructor of '%s' (family %d),"
                    " expected '%s' (family %d)\n",
                    ind_get(scrut->indcon.fam_idx)->name, scrut->indcon.fam_idx,
                    ind_get(fam_idx)->name, fam_idx);
            exit(1);
        }
        int k        = scrut->indcon.ctor_idx;
        IndDef *fam  = ind_get(fam_idx);
        if (k < 0 || k >= fam->n_ctors) {
            fprintf(stderr,
                    "vindrec: constructor index %d out of range [0,%d) for '%s'\n",
                    k, fam->n_ctors, fam->name);
            exit(1);
        }
        int n_params = fam->n_params;
        Val *c = cases[k];
        /* Skip param args: case functions take only the ctor-local args. */
        for (int i = n_params; i < scrut->indcon.n_args; i++) {
            Val *arg = scrut->indcon.args[i];
            c = nbe_vapp(a, c, arg);
            int ap = i - n_params;  /* position among ctor args for is_recursive */
            if (ind_is_recursive_pos(fam_idx, k, ap))
                c = nbe_vapp(a, c, nbe_vindrec(a, fam_idx, motive, cases, arg));
        }
        return c;
    }
    if (scrut->tag == VL_NEUTRAL) {
        int n = ind_get(fam_idx)->n_ctors;
        return vl_neutral(a, scrut->neutral.lvl,
                          spine_indrec(a, fam_idx, motive, n, cases,
                                       scrut->neutral.spine));
    }
    fprintf(stderr,
            "vindrec: scrutinee has tag %d, expected VL_INDCON of '%s' or VL_NEUTRAL\n",
            scrut->tag, ind_get(fam_idx)->name);
    exit(1);
}

/* ── Spine helper: SP_WEAKEN ───────────────────────────────────────────────
 * Records a stuck  weaken a_ty ctx_g ty_t body  on a neutral spine so that
 * quote_spine can reconstruct the term and type-checking can proceed.
 */
static Spine *spine_weaken(Arena *a, Val *a_ty, Val *ctx_g, Val *ty_t, Spine *next) {
    Spine *sp = (Spine *)arena_alloc(a, sizeof(Spine));
    sp->kind          = SP_WEAKEN;
    sp->weaken_s.a_ty  = a_ty;
    sp->weaken_s.ctx_g = ctx_g;
    sp->weaken_s.ty_t  = ty_t;
    sp->next          = next;
    return sp;
}

/* ── Weaken primitive helpers ──────────────────────────────────────────────
 *
 * weaken a g t e : Expr (ext a g) t
 *   Inserts a new innermost binding of type `a` into the context of every
 *   variable reference in `e`.  Implemented by structural recursion on the
 *   VL_INDCON tree; does NOT use indrec, so it avoids the ext-commutativity
 *   definitional gap.
 *
 * weaken_ctx(a, ctx, d)   — insert `a` at depth d in ctx
 * shift_var_val(a, v, d)  — shift Var `v` at cutoff d
 * weaken_expr_val(a, e, d)— shift all Var refs in Expr `e` at cutoff d
 */

/* Lazy family/ctor index cache, initialised on first weaken call. */
static int wk_init      = 0;
static int wk_expr_fam  = -1;
static int wk_var_fam   = -1;
static int wk_ctx_fam   = -1;
static int wk_ext_ctor  = -1;
static int wk_here_ctor = -1;
static int wk_there_ctor= -1;
static int wk_evar_ctor = -1;
static int wk_elam_ctor = -1;
static int wk_eapp_ctor = -1;
static int wk_elet_ctor = -1;
static int wk_eif_ctor  = -1;

static void init_weaken_cache(void) {
    if (wk_init) return;
    wk_init = 1;
    wk_expr_fam   = ind_lookup("Expr");
    wk_var_fam    = ind_lookup("Var");
    wk_ctx_fam    = ind_lookup("Ctx");
    if (wk_expr_fam < 0 || wk_var_fam < 0 || wk_ctx_fam < 0) {
        fprintf(stderr, "weaken: Expr/Var/Ctx family not found\n"); exit(1);
    }
    wk_ext_ctor   = ind_ctor_lookup(wk_ctx_fam,  "ext");
    wk_here_ctor  = ind_ctor_lookup(wk_var_fam,  "here");
    wk_there_ctor = ind_ctor_lookup(wk_var_fam,  "there");
    wk_evar_ctor  = ind_ctor_lookup(wk_expr_fam, "EVar");
    wk_elam_ctor  = ind_ctor_lookup(wk_expr_fam, "ELam");
    wk_eapp_ctor  = ind_ctor_lookup(wk_expr_fam, "EApp");
    wk_elet_ctor  = ind_ctor_lookup(wk_expr_fam, "ELet");
    wk_eif_ctor   = ind_ctor_lookup(wk_expr_fam, "EIf");
    if (wk_ext_ctor < 0 || wk_here_ctor < 0 || wk_there_ctor < 0 ||
        wk_evar_ctor < 0 || wk_elam_ctor < 0 || wk_eapp_ctor < 0 ||
        wk_elet_ctor < 0 || wk_eif_ctor  < 0) {
        fprintf(stderr, "weaken: required constructor(s) not found in Ctx/Var/Expr\n"); exit(1);
    }
}

/* Insert a_ty as new binding at depth d in ctx.
 * weaken_ctx(a, ctx, 0) = ext a ctx
 * weaken_ctx(a, ext s g, d+1) = ext s (weaken_ctx a g d)  */
static Val *weaken_ctx(Arena *a, Val *ctx, Val *a_ty, int d) {
    Val **args = (Val **)arena_alloc(a, 2 * sizeof(Val *));
    if (d == 0) {
        args[0] = a_ty; args[1] = ctx;
        return vl_indcon(a, wk_ctx_fam, wk_ext_ctor, 2, args);
    }
    /* Must be ext s g */
    if (ctx->tag != VL_INDCON || ctx->indcon.ctor_idx != wk_ext_ctor) {
        fprintf(stderr, "weaken: weaken_ctx: expected ext constructor at depth %d\n", d);
        exit(1);
    }
    Val *s  = ctx->indcon.args[0];
    Val *g_ = ctx->indcon.args[1];
    args[0] = s;
    args[1] = weaken_ctx(a, g_, a_ty, d - 1);
    return vl_indcon(a, wk_ctx_fam, wk_ext_ctor, 2, args);
}

/* Shift a Var value by inserting a_ty at cutoff d.
 *   here g t  (index 0):
 *     d == 0: wrap with there → Var (ext a (ext t g)) t
 *     d > 0:  update g       → here (weaken_ctx g d-1) t
 *   there g t s v_inner  (index 1+k):
 *     d == 0: wrap whole val → there (ext s g) t a (there g t s v_inner)
 *     d > 0:  recurse        → there (weaken_ctx g d-1) t s (shift_var v_inner d-1)
 */
static Val *shift_var_val(Arena *a, Val *v, Val *a_ty, int d) {
    if (v->tag != VL_INDCON || v->indcon.fam_idx != wk_var_fam) {
        fprintf(stderr, "weaken: shift_var_val: expected Var VL_INDCON\n");
        exit(1);
    }
    int ctor = v->indcon.ctor_idx;
    if (ctor == wk_here_ctor) {
        Val *g = v->indcon.args[0];
        Val *t = v->indcon.args[1];
        if (d == 0) {
            /* there (ext t g) t a_ty (here g t) : Var (ext a_ty (ext t g)) t
             * `there`'s first argument is the context of the INNER variable,
             * ext t g — not g.  Passing g here produced an ill-typed value:
             * found in Phase 9 by discharging this primitive as weaken_l
             * (lark-weaken.lcore); the there-case below always had it right.
             * Primitive outputs are never re-checked by the kernel, so the
             * bug was invisible until an independent, fully-checked
             * implementation disagreed. */
            Val **etg = (Val **)arena_alloc(a, 2 * sizeof(Val *));
            etg[0] = t; etg[1] = g;
            Val *ext_t_g = vl_indcon(a, wk_ctx_fam, wk_ext_ctor, 2, etg);
            Val **args = (Val **)arena_alloc(a, 4 * sizeof(Val *));
            args[0] = ext_t_g; args[1] = t; args[2] = a_ty; args[3] = v;
            return vl_indcon(a, wk_var_fam, wk_there_ctor, 4, args);
        } else {
            /* here (weaken_ctx g (d-1)) t */
            Val *g_new = weaken_ctx(a, g, a_ty, d - 1);
            Val **args = (Val **)arena_alloc(a, 2 * sizeof(Val *));
            args[0] = g_new; args[1] = t;
            return vl_indcon(a, wk_var_fam, wk_here_ctor, 2, args);
        }
    } else { /* there_ctor */
        Val *g       = v->indcon.args[0];
        Val *t       = v->indcon.args[1];
        Val *s       = v->indcon.args[2];
        Val *v_inner = v->indcon.args[3];
        if (d == 0) {
            /* there (ext s g) t a_ty v : Var (ext a_ty (ext s g)) t */
            Val **esg = (Val **)arena_alloc(a, 2 * sizeof(Val *));
            esg[0] = s; esg[1] = g;
            Val *ext_s_g = vl_indcon(a, wk_ctx_fam, wk_ext_ctor, 2, esg);
            Val **args = (Val **)arena_alloc(a, 4 * sizeof(Val *));
            args[0] = ext_s_g; args[1] = t; args[2] = a_ty; args[3] = v;
            return vl_indcon(a, wk_var_fam, wk_there_ctor, 4, args);
        } else {
            /* there (weaken_ctx g (d-1)) t s (shift_var v_inner (d-1)) */
            Val *g_new       = weaken_ctx(a, g, a_ty, d - 1);
            Val *v_inner_new = shift_var_val(a, v_inner, a_ty, d - 1);
            Val **args = (Val **)arena_alloc(a, 4 * sizeof(Val *));
            args[0] = g_new; args[1] = t; args[2] = s; args[3] = v_inner_new;
            return vl_indcon(a, wk_var_fam, wk_there_ctor, 4, args);
        }
    }
}

/* Shift all Var references in Expr value e at cutoff d.
 * Invariant: e : Expr g t  →  result : Expr (weaken_ctx g d) t
 */
static Val *weaken_expr_val(Arena *a, Val *e, Val *a_ty, int d) {
    if (e->tag != VL_INDCON || e->indcon.fam_idx != wk_expr_fam) {
        fprintf(stderr, "weaken: weaken_expr_val: expected Expr VL_INDCON (tag=%d)\n",
                e->tag);
        exit(1);
    }
    int    ctor = e->indcon.ctor_idx;
    Val  **old  = e->indcon.args;
    int    n    = e->indcon.n_args;
    if (n < 1) {
        fprintf(stderr, "weaken: weaken_expr_val: Expr ctor has %d args, expected >= 1\n", n);
        exit(1);
    }
    Val  **args = (Val **)arena_alloc(a, n * sizeof(Val *));
    for (int i = 0; i < n; i++) args[i] = old[i];

    /* Update the context index (args[0]) for every constructor. */
    args[0] = weaken_ctx(a, old[0], a_ty, d);

    if (ctor == wk_evar_ctor) {
        /* EVar g t v → EVar g' t (shift_var v d) */
        if (n < 3) {
            fprintf(stderr, "weaken: EVar ctor has %d args, expected 3\n", n); exit(1);
        }
        args[2] = shift_var_val(a, old[2], a_ty, d);
    } else if (ctor == wk_elam_ctor) {
        /* ELam g a_lam b body → ELam g' a_lam b (weaken body at d+1) */
        if (n < 4) {
            fprintf(stderr, "weaken: ELam ctor has %d args, expected 4\n", n); exit(1);
        }
        args[3] = weaken_expr_val(a, old[3], a_ty, d + 1);
    } else if (ctor == wk_eapp_ctor) {
        /* EApp g a b f x → EApp g' a b (weaken f) (weaken x) */
        if (n < 5) {
            fprintf(stderr, "weaken: EApp ctor has %d args, expected 5\n", n); exit(1);
        }
        args[3] = weaken_expr_val(a, old[3], a_ty, d);
        args[4] = weaken_expr_val(a, old[4], a_ty, d);
    } else if (ctor == wk_elet_ctor) {
        /* ELet g a b val body → ELet g' a b (weaken val) (weaken body at d+1) */
        if (n < 5) {
            fprintf(stderr, "weaken: ELet ctor has %d args, expected 5\n", n); exit(1);
        }
        args[3] = weaken_expr_val(a, old[3], a_ty, d);
        args[4] = weaken_expr_val(a, old[4], a_ty, d + 1);
    } else if (ctor == wk_eif_ctor) {
        /* EIf g t c th el → EIf g' t (weaken c) (weaken th) (weaken el) */
        if (n < 5) {
            fprintf(stderr, "weaken: EIf ctor has %d args, expected 5\n", n); exit(1);
        }
        args[2] = weaken_expr_val(a, old[2], a_ty, d);
        args[3] = weaken_expr_val(a, old[3], a_ty, d);
        args[4] = weaken_expr_val(a, old[4], a_ty, d);
    }
    /* Literals: only args[0] (context) updated above; rest unchanged. */
    return vl_indcon(a, wk_expr_fam, ctor, n, args);
}

/* ── Eval */

/*
 * nbe_vapp — semantic function application.
 *
 * Three cases:
 *   VL_LAM   : beta-reduce by evaluating the body in an extended environment.
 *              This is the entire substitution mechanism: push arg onto env,
 *              evaluate body.  No traversal of the term tree needed.
 *   VL_NEUTRAL: the function is stuck (it is a variable or an unapplied axiom).
 *              Record the argument on the spine so quote can reproduce the app.
 *   VL_FIX   : unfold one step — (fix f) arg → (f (fix f)) arg.
 *              The fix is not unrolled until applied; this keeps recursion lazy.
 */
Val *nbe_vapp(Arena *a, Val *fun, Val *arg) {
    switch (fun->tag) {
    case VL_LAM:
        return nbe_eval(a, env_cons(a, arg, fun->lam.env), fun->lam.body);
    case VL_NEUTRAL:
        return vl_neutral(a, fun->neutral.lvl,
                          spine_cons(a, arg, fun->neutral.spine));
    case VL_FIX:
        /* (fix f) arg → (f (fix f)) arg  — unfold one step */
        return nbe_vapp(a, nbe_vapp(a, fun->fix_fun, vl_fix(a, fun->fix_fun)), arg);
    default:
        fprintf(stderr, "vapp: not a function\n"); exit(1);
    }
}

/*
 * nbe_eval — evaluate a Term to a Val.
 *
 * env is a linked list of Val*s; de Bruijn index k → env->val after k .next
 * hops.  Every compound term evaluates its sub-terms and builds a Val.
 *
 * Notable cases:
 *   TM_VAR   : variable lookup in env.
 *   TM_LAM   : capture the current env in a closure (do NOT evaluate the body
 *              yet — that happens lazily in nbe_vapp when an argument arrives).
 *   TM_APP   : evaluate both sides, then call nbe_vapp for beta reduction.
 *   TM_ANN   : annotations are type-only; evaluation erases them.
 *   TM_PI/SIG: keep the codomain as an unevaluated Term plus the current env,
 *              just like TM_LAM.  The cod is only opened when checked or applied.
 *   TM_NATREC: delegate to nbe_vnatrec which fires or builds a neutral.
 *   TM_GLOBAL: retrieve the pre-evaluated Val stored in the global def table.
 */
Val *nbe_eval(Arena *a, Env *env, Term *t) {
    switch (t->tag) {
    case TM_VAR:  return env_lookup(a, env, t->idx, t->idx);
    case TM_LAM:  return vl_lam(a, t->lam.name, env, t->lam.body);
    case TM_APP:  return nbe_vapp(a, nbe_eval(a, env, t->app.fun),
                                     nbe_eval(a, env, t->app.arg));
    case TM_PI:   return vl_pi   (a, t->pi.name, nbe_eval(a, env, t->pi.dom), env, t->pi.cod);
    case TM_SIG:  return vl_sigma(a, t->pi.name, nbe_eval(a, env, t->pi.dom), env, t->pi.cod);
    case TM_UNI:  return vl_uni(a, t->ulevel);
    case TM_ANN:  return nbe_eval(a, env, t->ann.term);
    case TM_PAIR: return vl_pair(a, nbe_eval(a, env, t->pair.fst),
                                    nbe_eval(a, env, t->pair.snd));
    case TM_FST:  return nbe_vfst(a, nbe_eval(a, env, t->elim));
    case TM_SND:  return nbe_vsnd(a, nbe_eval(a, env, t->elim));
    case TM_ID:   return vl_id(a, nbe_eval(a, env, t->id.ty),
                                  nbe_eval(a, env, t->id.lhs),
                                  nbe_eval(a, env, t->id.rhs));
    case TM_REFL: return vl_refl(a, nbe_eval(a, env, t->refl));
    case TM_UA:     return vl_neutral(a, UA_CONST_LVL,     NULL);
    case TM_FUNEXT: return vl_neutral(a, FUNEXT_CONST_LVL, NULL);
    case TM_NAT:    return vl_nat(a);
    case TM_ZERO:   return vl_zero(a);
    case TM_SUCC:   return vl_succ(a, nbe_eval(a, env, t->elim));
    case TM_NATREC: return nbe_vnatrec(a,
                        nbe_eval(a, env, t->natrec.motive),
                        nbe_eval(a, env, t->natrec.base),
                        nbe_eval(a, env, t->natrec.step),
                        nbe_eval(a, env, t->natrec.scrut));
    case TM_GLOBAL: return def_get(t->idx)->val;
    case TM_BOOL:   return vl_bool(a);
    case TM_TRUE:   return vl_true(a);
    case TM_FALSE:  return vl_false(a);
    case TM_BOOLREC: return nbe_vboolrec(a,
                        nbe_eval(a, env, t->boolrec.motive),
                        nbe_eval(a, env, t->boolrec.tcase),
                        nbe_eval(a, env, t->boolrec.fcase),
                        nbe_eval(a, env, t->boolrec.scrut));
    case TM_J:    return nbe_vj(a,
                      nbe_eval(a, env, t->j.ty),
                      nbe_eval(a, env, t->j.lhs),
                      nbe_eval(a, env, t->j.motive),
                      nbe_eval(a, env, t->j.base),
                      nbe_eval(a, env, t->j.endpoint),
                      nbe_eval(a, env, t->j.proof));
    case TM_W:
        return vl_w(a, t->pi.name, nbe_eval(a, env, t->pi.dom), env, t->pi.cod);
    case TM_SUP:
        return vl_sup(a, nbe_eval(a, env, t->sup.label),
                         nbe_eval(a, env, t->sup.children));
    case TM_WREC:
        return nbe_vwrec(a,
                   nbe_eval(a, env, t->wrec.motive),
                   nbe_eval(a, env, t->wrec.step),
                   nbe_eval(a, env, t->wrec.scrut));
    case TM_EMPTY:
        return vl_empty(a);
    case TM_ABORT:
        return nbe_vabort(a,
                   nbe_eval(a, env, t->abort_t.motive),
                   nbe_eval(a, env, t->abort_t.scrut));
    case TM_UNIT:
        return vl_unit(a);
    case TM_STAR:
        return vl_star(a);
    case TM_UNITREC:
        return nbe_vunitrec(a,
                   nbe_eval(a, env, t->unitrec_t.motive),
                   nbe_eval(a, env, t->unitrec_t.base),
                   nbe_eval(a, env, t->unitrec_t.scrut));
    case TM_SUM:
        return vl_sum(a, nbe_eval(a, env, t->sum_t.left),
                         nbe_eval(a, env, t->sum_t.right));
    case TM_INL:
        return vl_inl(a, nbe_eval(a, env, t->elim));
    case TM_INR:
        return vl_inr(a, nbe_eval(a, env, t->elim));
    case TM_CASESPLIT:
        return nbe_vcase(a,
                   nbe_eval(a, env, t->casesplit_t.motive),
                   nbe_eval(a, env, t->casesplit_t.lcase),
                   nbe_eval(a, env, t->casesplit_t.rcase),
                   nbe_eval(a, env, t->casesplit_t.scrut));
    case TM_TRUNC:   return vl_neutral(a, TRUNC_CONST_LVL,  NULL);
    case TM_TRINT:   return vl_neutral(a, TRINT_CONST_LVL,  NULL);
    case TM_SQUASH:  return vl_neutral(a, SQUASH_CONST_LVL, NULL);
    case TM_TRUNCREC:
        return nbe_vtruncret(a,
                   nbe_eval(a, env, t->truncrec_t.ty_a),
                   nbe_eval(a, env, t->truncrec_t.ty_b),
                   nbe_eval(a, env, t->truncrec_t.func),
                   nbe_eval(a, env, t->truncrec_t.scrut));
    case TM_CIRCLE:  return vl_circle(a);
    case TM_BASE:    return vl_base(a);
    case TM_LOOP:    return vl_neutral(a, LOOP_CONST_LVL, NULL);
    case TM_CIRCREC:
        return nbe_vcircrec(a,
                   nbe_eval(a, env, t->circrec_t.motive),
                   nbe_eval(a, env, t->circrec_t.base_case),
                   nbe_eval(a, env, t->circrec_t.loop_case),
                   nbe_eval(a, env, t->circrec_t.scrut));
    case TM_INDTYPE: {
        int n = t->indtype.n_args;
        Val **args = n > 0 ? (Val **)arena_alloc(a, n * sizeof(Val *)) : NULL;
        for (int i = 0; i < n; i++) args[i] = nbe_eval(a, env, t->indtype.args[i]);
        return vl_indtype(a, t->indtype.fam_idx, n, args);
    }
    case TM_INDCON: {
        int n = t->indcon.n_args;
        Val **args = n > 0 ? (Val **)arena_alloc(a, n * sizeof(Val *)) : NULL;
        for (int i = 0; i < n; i++) args[i] = nbe_eval(a, env, t->indcon.args[i]);
        return vl_indcon(a, t->indcon.fam_idx, t->indcon.ctor_idx, n, args);
    }
    case TM_INDREC: {
        int fam_idx = t->indrec.fam_idx;
        int n       = t->indrec.n_cases;
        int expect  = ind_get(fam_idx)->n_ctors;
        if (n != expect) {
            fprintf(stderr,
                    "eval: indrec for '%s' has %d case(s), expected %d\n",
                    ind_get(fam_idx)->name, n, expect);
            exit(1);
        }
        Val *motive = t->indrec.motive ? nbe_eval(a, env, t->indrec.motive) : NULL;
        Val **cases = n > 0 ? (Val **)arena_alloc(a, n * sizeof(Val *)) : NULL;
        for (int i = 0; i < n; i++) cases[i] = nbe_eval(a, env, t->indrec.cases[i]);
        Val *scrut = nbe_eval(a, env, t->indrec.scrut);
        return nbe_vindrec(a, fam_idx, motive, cases, scrut);
    }

    case TM_FIX:
        return vl_fix(a, nbe_eval(a, env, t->fix.body));
    case TM_WEAKEN: {
        Val *a_ty  = nbe_eval(a, env, t->weaken.ty_a);
        Val *ctx_g = nbe_eval(a, env, t->weaken.ctx_g);
        Val *ty_t  = nbe_eval(a, env, t->weaken.ty_t);
        Val *body  = nbe_eval(a, env, t->weaken.body);
        if (body->tag == VL_NEUTRAL)
            return vl_neutral(a, body->neutral.lvl,
                              spine_weaken(a, a_ty, ctx_g, ty_t, body->neutral.spine));
        init_weaken_cache();
        return weaken_expr_val(a, body, a_ty, 0);
    }
    case TM_LEVEL: return vl_level(a);
    case TM_LZERO: return vl_lzero(a);
    case TM_LSUC:  return vl_lsuc(a, nbe_eval(a, env, t->elim));
    case TM_UNI_V: {
        Val *lv = nbe_eval(a, env, t->uni_v_lvl);
        /* Concrete level: collapse to VL_UNI */
        int n = 0; Val *cur = lv;
        while (cur->tag == VL_LSUC) { n++; cur = cur->succ; }
        if (cur->tag == VL_LZERO) return vl_uni(a, n);
        return vl_uni_v(a, lv);  /* neutral level */
    }

    case TM_HOLE:
        fprintf(stderr, "eval: TM_HOLE reached — term not elaborated\n");
        exit(1);

    default:
        fprintf(stderr, "eval: unhandled term tag %d\n", t->tag);
        exit(1);
    }
}

/* ── Quote */

static Term *quote(Arena *a, int depth, Val *v);

static Term *quote_spine(Arena *a, int depth, Term *head, Spine *sp) {
    if (!sp) return head;
    Term *inner = quote_spine(a, depth, head, sp->next);
    switch (sp->kind) {
    case SP_APP: return tm_app(a, inner, quote(a, depth, sp->val));
    case SP_FST: return tm_fst(a, inner);
    case SP_SND: return tm_snd(a, inner);
    case SP_J:
        return tm_j(a,
                    quote(a, depth, sp->j.ty),
                    quote(a, depth, sp->j.lhs),
                    quote(a, depth, sp->j.motive),
                    quote(a, depth, sp->j.base),
                    quote(a, depth, sp->j.endpoint),
                    inner);
    case SP_NATREC:
        return tm_natrec(a,
                         quote(a, depth, sp->natrec.motive),
                         quote(a, depth, sp->natrec.base),
                         quote(a, depth, sp->natrec.step),
                         inner);
    case SP_BOOLREC:
        return tm_boolrec(a,
                          quote(a, depth, sp->boolrec.motive),
                          quote(a, depth, sp->boolrec.tcase),
                          quote(a, depth, sp->boolrec.fcase),
                          inner);
    case SP_WREC:
        return tm_wrec(a,
                       quote(a, depth, sp->wrec.motive),
                       quote(a, depth, sp->wrec.step),
                       inner);
    case SP_ABORT:
        return tm_abort(a, quote(a, depth, sp->abort_s.motive), inner);
    case SP_UNITREC:
        return tm_unitrec(a,
                          quote(a, depth, sp->unitrec_s.motive),
                          quote(a, depth, sp->unitrec_s.base),
                          inner);
    case SP_CASESPLIT:
        return tm_casesplit(a,
                            quote(a, depth, sp->casesplit_s.motive),
                            quote(a, depth, sp->casesplit_s.lcase),
                            quote(a, depth, sp->casesplit_s.rcase),
                            inner);
    case SP_TRUNCREC:
        return tm_truncrec(a,
                           quote(a, depth, sp->truncrec_s.ty_a),
                           quote(a, depth, sp->truncrec_s.ty_b),
                           quote(a, depth, sp->truncrec_s.func),
                           inner);
    case SP_CIRCREC:
        return tm_circrec(a,
                          quote(a, depth, sp->circrec_s.motive),
                          quote(a, depth, sp->circrec_s.base_case),
                          quote(a, depth, sp->circrec_s.loop_case),
                          inner);
    case SP_INDREC: {
        int n = sp->indrec.n_cases;
        Term **cases = n > 0 ? (Term **)arena_alloc(a, n * sizeof(Term *)) : NULL;
        for (int i = 0; i < n; i++) cases[i] = quote(a, depth, sp->indrec.cases[i]);
        Term *motive = sp->indrec.motive ? quote(a, depth, sp->indrec.motive) : NULL;
        return tm_indrec(a, sp->indrec.fam_idx, motive, n, cases, inner);
    }
    case SP_WEAKEN:
        return tm_weaken(a,
                         quote(a, depth, sp->weaken_s.a_ty),
                         quote(a, depth, sp->weaken_s.ctx_g),
                         quote(a, depth, sp->weaken_s.ty_t),
                         inner);
    default:
        fprintf(stderr, "quote_spine: unhandled spine kind %d\n", sp->kind);
        exit(1);
    }
}

static Term *quote(Arena *a, int depth, Val *v) {
    switch (v->tag) {
    case VL_LAM: {
        Val *fresh = vl_neutral(a, depth, NULL);
        Val *body  = nbe_eval(a, env_cons(a, fresh, v->lam.env), v->lam.body);
        return tm_lam(a, v->lam.name, quote(a, depth + 1, body));
    }
    case VL_PI: {
        Term *dom  = quote(a, depth, v->pi.dom);
        Val  *fresh = vl_neutral(a, depth, NULL);
        Val  *cod   = nbe_eval(a, env_cons(a, fresh, v->pi.env), v->pi.cod);
        return tm_pi(a, v->pi.name, dom, quote(a, depth + 1, cod));
    }
    case VL_SIGMA: {
        Term *dom  = quote(a, depth, v->pi.dom);
        Val  *fresh = vl_neutral(a, depth, NULL);
        Val  *cod   = nbe_eval(a, env_cons(a, fresh, v->pi.env), v->pi.cod);
        return tm_sig(a, v->pi.name, dom, quote(a, depth + 1, cod));
    }
    case VL_UNI:
        return tm_uni(a, v->ulevel);
    case VL_NEUTRAL: {
        Term *head;
        if      (v->neutral.lvl == UA_CONST_LVL)     head = tm_ua(a);
        else if (v->neutral.lvl == FUNEXT_CONST_LVL) head = tm_funext(a);
        else if (v->neutral.lvl == TRUNC_CONST_LVL)  head = tm_trunc(a);
        else if (v->neutral.lvl == TRINT_CONST_LVL)  head = tm_trint(a);
        else if (v->neutral.lvl == SQUASH_CONST_LVL) head = tm_squash(a);
        else if (v->neutral.lvl == LOOP_CONST_LVL)   head = tm_loop(a);
        else head = tm_var(a, depth - v->neutral.lvl - 1);
        return quote_spine(a, depth, head, v->neutral.spine);
    }
    case VL_PAIR:
        return tm_pair(a, quote(a, depth, v->pair.fst),
                          quote(a, depth, v->pair.snd));
    case VL_ID:
        return tm_id(a, quote(a, depth, v->id.ty),
                        quote(a, depth, v->id.lhs),
                        quote(a, depth, v->id.rhs));
    case VL_REFL:
        return tm_refl(a, quote(a, depth, v->refl));
    case VL_NAT:   return tm_nat(a);
    case VL_ZERO:  return tm_zero(a);
    case VL_SUCC:  return tm_succ(a, quote(a, depth, v->succ));
    case VL_BOOL:  return tm_bool(a);
    case VL_TRUE:  return tm_true(a);
    case VL_FALSE: return tm_false(a);
    case VL_W: {
        Term *dom   = quote(a, depth, v->pi.dom);
        Val  *fresh = vl_neutral(a, depth, NULL);
        Val  *cod   = nbe_eval(a, env_cons(a, fresh, v->pi.env), v->pi.cod);
        return tm_w(a, v->pi.name, dom, quote(a, depth + 1, cod));
    }
    case VL_SUP:
        return tm_sup(a, quote(a, depth, v->pair.fst),
                         quote(a, depth, v->pair.snd));
    case VL_EMPTY:
        return tm_empty(a);
    case VL_UNIT:
        return tm_unit(a);
    case VL_STAR:
        return tm_star(a);
    case VL_SUM:
        return tm_sum(a, quote(a, depth, v->pair.fst),
                         quote(a, depth, v->pair.snd));
    case VL_INL:
        return tm_inl(a, quote(a, depth, v->inj));
    case VL_INR:
        return tm_inr(a, quote(a, depth, v->inj));
    case VL_CIRCLE: return tm_circle(a);
    case VL_BASE:   return tm_base(a);
    case VL_INDTYPE: {
        int n = v->indtype.n_args;
        Term **args = n > 0 ? (Term **)arena_alloc(a, n * sizeof(Term *)) : NULL;
        for (int i = 0; i < n; i++) args[i] = quote(a, depth, v->indtype.args[i]);
        return tm_indtype(a, v->indtype.fam_idx, n, args);
    }
    case VL_INDCON: {
        int n = v->indcon.n_args;
        Term **args = n > 0 ? (Term **)arena_alloc(a, n * sizeof(Term *)) : NULL;
        for (int i = 0; i < n; i++) args[i] = quote(a, depth, v->indcon.args[i]);
        return tm_indcon(a, v->indcon.fam_idx, v->indcon.ctor_idx, n, args);
    }
    case VL_FIX:
        return tm_fix(a, quote(a, depth, v->fix_fun));
    case VL_LEVEL: return tm_level(a);
    case VL_LZERO: return tm_lzero(a);
    case VL_LSUC:  return tm_lsuc(a, quote(a, depth, v->succ));
    case VL_UNI_V:
        if (!v->uni_v_lvl) {
            /* VL_UNI_V(NULL) is the checker's omega sentinel; nbe_eval never
               produces it, so quote should never see it with closed terms. */
            fprintf(stderr, "quote: internal error: VL_UNI_V with NULL level\n");
            exit(1);
        }
        return tm_uni_v(a, quote(a, depth, v->uni_v_lvl));
    default:
        fprintf(stderr, "quote: unhandled val tag %d\n", v->tag);
        exit(1);
    }
}

Term *nbe_quote(Arena *a, int depth, Val *v) { return quote(a, depth, v); }

Term *nbe_nf(Arena *a, Term *t) {
    return nbe_quote(a, 0, nbe_eval(a, NULL, t));
}
