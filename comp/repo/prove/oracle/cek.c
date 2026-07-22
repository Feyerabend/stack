/*
 * cek.c — Lark C CEK machine.
 *
 * The machine has three global variables representing the current state:
 *   _mode  — EVAL (reduce an expression) or RET (deliver a value to a frame)
 *   _expr  — expression to reduce (EVAL mode)
 *   _env   — local environment (EVAL mode)
 *   _val   — value to deliver (RET mode)
 *
 * The continuation is a fixed-size stack of LkFrame values.
 *
 * All runtime heap objects (closures, tuples, constructors, strings built at
 * runtime) are allocated from a single bump-pointer arena.  The arena is
 * created once per cek_run call and released on exit.
 */

#include "cek.h"
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>


/* -- Arena -- */

#ifndef LARK_ARENA_SIZE
#  define LARK_ARENA_SIZE (512u * 1024u)
#endif

static LkArena _ar;   /* base malloc'd in cek_run — see below (lazily committed,
                         so a large LARK_ARENA_SIZE costs only touched pages) */

void* arena_alloc(LkArena* a, size_t bytes) {
    bytes = (bytes + 7u) & ~7u;
    if (a->used + bytes > a->cap) {
        fputs("lark: arena overflow\n", stderr);
        exit(1);
    }
    void* p = a->base + a->used;
    a->used += bytes;
    return p;
}

#define AR(bytes) arena_alloc(&_ar, (bytes))


/* -- Top-level environment -- */

/*
 * Top-level names (functions, lets, constructors) are stored in a flat
 * mutable array rather than the persistent linked list used for locals.
 * This means closures created at the top level do not need to capture a
 * snapshot of the top-level env — they just look things up here at call
 * time.  Mutual recursion therefore works without backpatching.
 */

#ifndef LARK_TOP_MAX
#  define LARK_TOP_MAX 512
#endif

typedef struct { const char* name; LkVal val; } TopEntry;
static TopEntry _top[LARK_TOP_MAX];
static int      _top_n = 0;

static void top_set(const char* name, LkVal val) {
    for (int i = 0; i < _top_n; i++) {
        if (strcmp(_top[i].name, name) == 0) { _top[i].val = val; return; }
    }
    _top[_top_n++] = (TopEntry){ name, val };
}

static LkVal* top_get(const char* name) {
    for (int i = 0; i < _top_n; i++) {
        if (strcmp(_top[i].name, name) == 0) return &_top[i].val;
    }
    return NULL;
}


/* -- Local environment -- */

static LkEnv* env_bind(LkEnv* env, const char* name, LkVal val) {
    LkEnv* node  = AR(sizeof(LkEnv));
    node->name   = name;
    node->val    = val;
    node->next   = env;
    return node;
}

static LkVal env_lookup(LkEnv* env, const char* name) {
    for (LkEnv* n = env; n; n = n->next)
        if (strcmp(n->name, name) == 0) return n->val;
    LkVal* v = top_get(name);
    if (v) return *v;
    fprintf(stderr, "lark: unbound: %s\n", name);
    exit(1);
}


/* -- Dispatch table -- */

#ifndef LARK_DISPATCH_MAX
#  define LARK_DISPATCH_MAX 128
#endif

typedef struct { const char* method; const char* type_; LkVal impl; } DispEntry;
static DispEntry _disp[LARK_DISPATCH_MAX];
static int       _disp_n = 0;

static void disp_set(const char* method, const char* type_, LkVal impl) {
    for (int i = 0; i < _disp_n; i++) {
        if (strcmp(_disp[i].method, method) == 0 &&
            strcmp(_disp[i].type_,  type_)  == 0) { _disp[i].impl = impl; return; }
    }
    _disp[_disp_n++] = (DispEntry){ method, type_, impl };
}

static LkVal* disp_get(const char* method, const char* type_) {
    for (int i = 0; i < _disp_n; i++) {
        if (strcmp(_disp[i].method, method) == 0 &&
            strcmp(_disp[i].type_,  type_)  == 0) return &_disp[i].impl;
    }
    return NULL;
}


/* -- Constructor table -- */

#ifndef LARK_CON_MAX
#  define LARK_CON_MAX 128
#endif

typedef struct { const char* tag; const char* type_name; int arity; } ConEntry;
static ConEntry _con[LARK_CON_MAX];
static int      _con_n = 0;

static void con_register(const char* tag, const char* type_name, int arity) {
    for (int i = 0; i < _con_n; i++) {
        if (strcmp(_con[i].tag, tag) == 0) {
            _con[i].type_name = type_name; _con[i].arity = arity; return;
        }
    }
    _con[_con_n++] = (ConEntry){ tag, type_name, arity };
}

static const char* con_type(const char* tag) {
    for (int i = 0; i < _con_n; i++)
        if (strcmp(_con[i].tag, tag) == 0) return _con[i].type_name;
    return tag;
}


/* -- Value factories -- */

static LkVal lk_int(int32_t i)        { return (LkVal){ .kind=V_INT,     .i=i   }; }
static LkVal lk_float(uint32_t f)     { return (LkVal){ .kind=V_FLOAT,   .f=f   }; }
static LkVal lk_bool(int b)           { return (LkVal){ .kind=V_BOOL,    .b=b   }; }
static LkVal lk_str(const char* s)    { return (LkVal){ .kind=V_STR,     .s=s   }; }
static LkVal lk_unit(void)            { return (LkVal){ .kind=V_UNIT             }; }
static LkVal lk_io(void)              { return (LkVal){ .kind=V_IO               }; }
static LkVal lk_builtin(const char* n){ return (LkVal){ .kind=V_BUILTIN, .builtin=n }; }
static LkVal lk_dispatch(const char* m){ return (LkVal){ .kind=V_DISPATCH,.method=m  }; }

static LkVal lk_tuple(const LkVal* elems, int n) {
    LkTuple* t = AR(sizeof(LkTuple) + (size_t)n * sizeof(LkVal));
    t->n = n;
    memcpy(t->elems, elems, (size_t)n * sizeof(LkVal));
    return (LkVal){ .kind=V_TUPLE, .tup=t };
}

static LkVal lk_con(const char* tag, const LkVal* fields, int n) {
    LkCon* c = AR(sizeof(LkCon) + (size_t)n * sizeof(LkVal));
    c->tag = tag; c->n = n;
    if (n > 0) memcpy(c->fields, fields, (size_t)n * sizeof(LkVal));
    return (LkVal){ .kind=V_CON, .con=c };
}

static LkVal lk_partial(const char* tag, int arity, const LkVal* args, int n) {
    LkPartCon* pc = AR(sizeof(LkPartCon) + (size_t)n * sizeof(LkVal));
    pc->tag = tag; pc->arity = arity; pc->n = n;
    if (n > 0) memcpy(pc->args, args, (size_t)n * sizeof(LkVal));
    return (LkVal){ .kind=V_PARTIAL, .part=pc };
}

static LkVal lk_builtin_partial(const char* name, int arity,
                                 const LkVal* args, int n) {
    LkPartBuiltin* pb = AR(sizeof(LkPartBuiltin) + (size_t)n * sizeof(LkVal));
    pb->name = name; pb->arity = arity; pb->n = n;
    if (n > 0) memcpy(pb->args, args, (size_t)n * sizeof(LkVal));
    return (LkVal){ .kind=V_BUILTIN_PART, .bpart=pb };
}

static LkVal lk_closure(const char* param, const LkExpr* body,
                         LkEnv* env, const char* rec) {
    LkClosure* c = AR(sizeof(LkClosure));
    c->param = param; c->body = body; c->env = env; c->rec = rec;
    return (LkVal){ .kind=V_CLOSURE, .clos=c };
}

static LkVal lk_print_io(LkVal io) {
    LkVal* p = AR(sizeof(LkVal));
    *p = io;
    return (LkVal){ .kind=V_PRINT_IO, .pio=p };
}


/* -- Float helpers -- */

static float bits_f32(uint32_t bits) {
    float f; memcpy(&f, &bits, 4); return f;
}
static uint32_t f32_bits(float f) {
    uint32_t bits; memcpy(&bits, &f, 4); return bits;
}


/* -- String helpers -- */

/* Concatenate two C strings into a new arena-allocated string. */
static const char* str_cat(const char* a, const char* b) {
    size_t la = strlen(a), lb = strlen(b);
    char*  s  = AR(la + lb + 1);
    memcpy(s, a, la);
    memcpy(s + la, b, lb);
    s[la + lb] = '\0';
    return s;
}

/* Parse a signed decimal integer into *out; return 1 on success, 0 if the
 * string is malformed.  Stricter than strtol (no whitespace, no prefixes) to
 * stay byte-for-byte in agreement with the Python CEK's _parse_int. */
static int parse_int_c(const char* s, int32_t* out) {
    if (s[0] == '\0') return 0;
    size_t i = 0;
    int    neg = 0;
    if (s[0] == '+' || s[0] == '-') {
        neg = (s[0] == '-');
        i = 1;
        if (s[i] == '\0') return 0;
    }
    int64_t val = 0;
    for (; s[i]; i++) {
        char c = s[i];
        if (c < '0' || c > '9') return 0;
        val = val * 10 + (c - '0');
    }
    *out = (int32_t)(neg ? -val : val);   /* wrap to int32, like _wrap_i32 */
    return 1;
}

/* Parse a decimal float into *out (as f32 bits); return 1 on success, 0 if
 * malformed.  Accepts exactly the lexer's FLOAT shape — optional sign, one or
 * more digits, '.', one or more digits, no exponent/whitespace/prefixes — to
 * stay byte-for-byte in agreement with the Python CEK's _parse_float. */
static int parse_float_c(const char* s, uint32_t* out) {
    if (s[0] == '\0') return 0;
    size_t i = 0;
    if (s[0] == '+' || s[0] == '-') i = 1;
    size_t digits_before = 0;
    for (; s[i] >= '0' && s[i] <= '9'; i++) digits_before++;
    if (digits_before == 0 || s[i] != '.') return 0;
    i++;                                        /* consume '.' */
    size_t digits_after = 0;
    for (; s[i] >= '0' && s[i] <= '9'; i++) digits_after++;
    if (digits_after == 0 || s[i] != '\0') return 0;
    *out = f32_bits(strtof(s, NULL));
    return 1;
}

/* Copy a string into the arena. */
static const char* str_dup(const char* s) {
    size_t n = strlen(s);
    char*  d = AR(n + 1);
    memcpy(d, s, n + 1);
    return d;
}

/* Format float32 bits as a Lark float literal string. */
static const char* show_float(uint32_t bits) {
    char buf[32];
    float f = bits_f32(bits);
    snprintf(buf, sizeof buf, "%.7g", f);
    if (!strchr(buf, '.') && !strchr(buf, 'e') &&
        !strchr(buf, 'n') && !strchr(buf, 'i')) {
        size_t n = strlen(buf);
        buf[n] = '.'; buf[n+1] = '0'; buf[n+2] = '\0';
    }
    return str_dup(buf);
}


/* -- Show -- */

static const char* val_show(LkVal v) {
    char buf[32];
    switch (v.kind) {
        case V_INT:   snprintf(buf, sizeof buf, "%d", v.i);  return str_dup(buf);
        case V_FLOAT: return show_float(v.f);
        case V_BOOL:  return v.b ? "true" : "false";
        case V_STR:   return v.s;
        case V_UNIT:  return "()";
        case V_TUPLE: {
            const char* r = "(";
            for (int i = 0; i < v.tup->n; i++) {
                if (i) r = str_cat(r, ", ");
                r = str_cat(r, val_show(v.tup->elems[i]));
            }
            return str_cat(r, ")");
        }
        case V_CON:
            if (v.con->n == 0) return v.con->tag;
            {
                const char* r = str_cat(v.con->tag, "(");
                for (int i = 0; i < v.con->n; i++) {
                    if (i) r = str_cat(r, ", ");
                    r = str_cat(r, val_show(v.con->fields[i]));
                }
                return str_cat(r, ")");
            }
        default:
            snprintf(buf, sizeof buf, "<val:%d>", v.kind);
            return str_dup(buf);
    }
}


/* -- Runtime type name (for dispatch) -- */

static const char* val_type(LkVal v) {
    switch (v.kind) {
        case V_INT:   return "Int";
        case V_FLOAT: return "Float";
        case V_BOOL:  return "Bool";
        case V_STR:   return "String";
        case V_UNIT:  return "()";
        case V_CON:   return con_type(v.con->tag);
        default:      return "?";
    }
}


/* -- Value equality (used by literal patterns) -- */

static int val_eq(LkVal a, LkVal b) {
    if (a.kind != b.kind) return 0;
    switch (a.kind) {
        case V_INT:   return a.i == b.i;
        case V_FLOAT: return a.f == b.f;
        case V_BOOL:  return a.b == b.b;
        case V_STR:   return strcmp(a.s, b.s) == 0;
        case V_UNIT:  return 1;
        default:      return 0;
    }
}

static LkVal lit_val(LkLit lit) {
    switch (lit.kind) {
        case LIT_INT:   return lk_int(lit.i);
        case LIT_FLOAT: return lk_float(lit.f);
        case LIT_BOOL:  return lk_bool(lit.b);
        case LIT_STR:   return lk_str(lit.s);
        case LIT_UNIT:  return lk_unit();
    }
    return lk_unit();
}


/* -- Binary / unary operations -- */

static LkVal binop(const char* op, LkVal l, LkVal r) {
    if (strcmp(op, "+") == 0 && l.kind == V_STR && r.kind == V_STR)
        return lk_str(str_cat(l.s, r.s));

    if (l.kind == V_INT && r.kind == V_INT) {
        int32_t a = l.i, b = r.i;
        if (strcmp(op, "+")  == 0) return lk_int(a + b);
        if (strcmp(op, "-")  == 0) return lk_int(a - b);
        if (strcmp(op, "*")  == 0) return lk_int(a * b);
        if (strcmp(op, "/")  == 0) return lk_int(b ? a / b : 0);
        /* Truncate-toward-zero to match RV32 rem: a - b*(a/b). */
        if (strcmp(op, "%")  == 0) return lk_int(b ? a - b*(a/b) : 0);
        if (strcmp(op, "==") == 0) return lk_bool(a == b);
        if (strcmp(op, "!=") == 0) return lk_bool(a != b);
        if (strcmp(op, "<")  == 0) return lk_bool(a <  b);
        if (strcmp(op, "<=") == 0) return lk_bool(a <= b);
        if (strcmp(op, ">")  == 0) return lk_bool(a >  b);
        if (strcmp(op, ">=") == 0) return lk_bool(a >= b);
    }

    if (l.kind == V_FLOAT && r.kind == V_FLOAT) {
        float a = bits_f32(l.f), b = bits_f32(r.f);
        if (strcmp(op, "+")  == 0) return lk_float(f32_bits(a + b));
        if (strcmp(op, "-")  == 0) return lk_float(f32_bits(a - b));
        if (strcmp(op, "*")  == 0) return lk_float(f32_bits(a * b));
        if (strcmp(op, "/")  == 0) return lk_float(b==0.0f ? 0x7FC00000u : f32_bits(a/b));
        if (strcmp(op, "==") == 0) return lk_bool(a == b);
        if (strcmp(op, "!=") == 0) return lk_bool(a != b);
        if (strcmp(op, "<")  == 0) return lk_bool(a <  b);
        if (strcmp(op, "<=") == 0) return lk_bool(a <= b);
        if (strcmp(op, ">")  == 0) return lk_bool(a >  b);
        if (strcmp(op, ">=") == 0) return lk_bool(a >= b);
    }

    if (strcmp(op, "and") == 0)
        return lk_bool(l.kind==V_BOOL && r.kind==V_BOOL && l.b && r.b);
    if (strcmp(op, "or") == 0)
        return lk_bool((l.kind==V_BOOL && l.b) || (r.kind==V_BOOL && r.b));

    fprintf(stderr, "lark: bad binop '%s'\n", op); exit(1);
}

static LkVal unaryop(const char* op, LkVal v) {
    if (strcmp(op, "-") == 0) {
        if (v.kind == V_INT)   return lk_int(-v.i);
        if (v.kind == V_FLOAT) return lk_float(f32_bits(-bits_f32(v.f)));
    }
    if (strcmp(op, "not") == 0 && v.kind == V_BOOL) return lk_bool(!v.b);
    fprintf(stderr, "lark: bad unaryop '%s'\n", op); exit(1);
}


/* -- Pattern matching -- */

/* Try to match val against pat.  On success return 1 and add bindings to
 * *env_out.  On failure return 0; *env_out may have been partially extended
 * but the caller discards the result. */
static int match_pat(const LkPat* pat, LkVal val, LkEnv** env_out) {
    switch (pat->kind) {
        case PAT_WILD:
            return 1;

        case PAT_VAR:
            *env_out = env_bind(*env_out, pat->var, val);
            return 1;

        case PAT_LIT:
            return val_eq(val, lit_val(pat->lit));

        case PAT_CON:
            if (strcmp(pat->con.name, "True")  == 0 && pat->con.n_args == 0)
                return val.kind == V_BOOL && val.b;
            if (strcmp(pat->con.name, "False") == 0 && pat->con.n_args == 0)
                return val.kind == V_BOOL && !val.b;
            if (val.kind != V_CON) return 0;
            if (strcmp(val.con->tag, pat->con.name) != 0) return 0;
            if (val.con->n != pat->con.n_args) return 0;
            for (int i = 0; i < pat->con.n_args; i++)
                if (!match_pat(pat->con.args[i], val.con->fields[i], env_out)) return 0;
            return 1;

        case PAT_TUPLE:
            if (val.kind != V_TUPLE || val.tup->n != pat->tup.n) return 0;
            for (int i = 0; i < pat->tup.n; i++)
                if (!match_pat(pat->tup.elems[i], val.tup->elems[i], env_out)) return 0;
            return 1;
    }
    return 0;
}


/* -- Built-in functions -- */

/* Abort with a clear message if arg has the wrong kind. */
#define BUILTIN_EXPECT(kind_name, kind_enum) \
    do { if (arg.kind != (kind_enum)) { \
        fprintf(stderr, "lark: %s expects %s (got kind %d)\n", \
                name, (kind_name), arg.kind); \
        exit(1); \
    } } while (0)

static LkVal apply_builtin(const char* name, LkVal arg) {
    if (strcmp(name, "print") == 0) {
        BUILTIN_EXPECT("IO", V_IO);
        return lk_print_io(arg);
    }

    if (strcmp(name, "read") == 0) {
        BUILTIN_EXPECT("IO", V_IO);
        char buf[1024];
        if (!fgets(buf, sizeof buf, stdin)) buf[0] = '\0';
        size_t n = strlen(buf);
        if (n && buf[n-1] == '\n') buf[n-1] = '\0';
        LkVal pair[2] = { arg, lk_str(str_dup(buf)) };
        return lk_tuple(pair, 2);
    }

    if (strcmp(name, "read_all") == 0) {
        BUILTIN_EXPECT("IO", V_IO);
        /* Slurp all of stdin verbatim (no newline stripping) — the whole-source
         * read the self-hosting bootstrap needs.  Read into a growing heap buffer
         * of unknown final size, then copy once into the arena. */
        size_t cap = 65536, len = 0;
        char*  tmp = (char*)malloc(cap);
        if (!tmp) { fputs("lark: read_all oom\n", stderr); exit(1); }
        size_t r;
        char   chunk[65536];
        while ((r = fread(chunk, 1, sizeof chunk, stdin)) > 0) {
            if (len + r + 1 > cap) {
                while (len + r + 1 > cap) cap *= 2;
                char* grown = (char*)realloc(tmp, cap);
                if (!grown) { fputs("lark: read_all oom\n", stderr); exit(1); }
                tmp = grown;
            }
            memcpy(tmp + len, chunk, r);
            len += r;
        }
        tmp[len] = '\0';
        const char* s = str_dup(tmp);           /* into the arena */
        free(tmp);
        LkVal pair[2] = { arg, lk_str(s) };
        return lk_tuple(pair, 2);
    }

    if (strcmp(name, "show") == 0)
        return lk_str(val_show(arg));

    if (strcmp(name, "int_to_float") == 0) {
        BUILTIN_EXPECT("Int", V_INT);
        return lk_float(f32_bits((float)arg.i));
    }

    if (strcmp(name, "float_to_int") == 0) {
        BUILTIN_EXPECT("Float", V_FLOAT);
        return lk_int((int32_t)bits_f32(arg.f));
    }

    if (strcmp(name, "float_to_bits") == 0) {
        /* Reinterpret the float32 bit pattern as an integer (mirrors
           emit_c_ast._f32_bits / cek.py float_to_bits).  arg.f already holds
           the f32 bits; FLOAT literals are non-negative, so bit 31 is clear
           and the (int32_t) view equals the unsigned value Python returns. */
        BUILTIN_EXPECT("Float", V_FLOAT);
        return lk_int((int32_t)arg.f);
    }

    if (strcmp(name, "int_to_string") == 0)
        return lk_str(val_show(arg));

    if (strcmp(name, "float_to_string") == 0)
        return lk_str(val_show(arg));

    if (strcmp(name, "int_abs") == 0) {
        BUILTIN_EXPECT("Int", V_INT);
        /* INT32_MIN negation overflows; saturate to INT32_MAX like Python abs would
         * differ, but the type checker prevents values that large reaching here
         * in practice (Int is int32_t throughout). */
        int32_t v = arg.i;
        return lk_int(v < 0 ? (v == INT32_MIN ? INT32_MAX : -v) : v);
    }

    if (strcmp(name, "float_abs") == 0) {
        BUILTIN_EXPECT("Float", V_FLOAT);
        return lk_float(arg.f & 0x7FFFFFFFu);
    }

    if (strcmp(name, "float_sqrt") == 0) {
        BUILTIN_EXPECT("Float", V_FLOAT);
        return lk_float(f32_bits(sqrtf(bits_f32(arg.f))));
    }

    if (strcmp(name, "float_floor") == 0) {
        BUILTIN_EXPECT("Float", V_FLOAT);
        return lk_float(f32_bits(floorf(bits_f32(arg.f))));
    }

    if (strcmp(name, "float_ceil") == 0) {
        BUILTIN_EXPECT("Float", V_FLOAT);
        return lk_float(f32_bits(ceilf(bits_f32(arg.f))));
    }

    if (strcmp(name, "string_length") == 0) {
        BUILTIN_EXPECT("String", V_STR);
        return lk_int((int32_t)strlen(arg.s));
    }

    if (strcmp(name, "char_to_string") == 0) {
        BUILTIN_EXPECT("Int", V_INT);
        /* One byte from the low 8 bits.  The inverse of string_index, which
         * returns (unsigned char), so the mask is a no-op on anything it
         * produced.  A Lark String is UTF-8 bytes; cek.py agrees. */
        char b[2] = { (char)(arg.i & 0xFF), '\0' };
        return lk_str(str_dup(b));
    }

    if (strcmp(name, "string_to_int") == 0) {
        BUILTIN_EXPECT("String", V_STR);
        int32_t n;
        if (parse_int_c(arg.s, &n)) {
            LkVal field = lk_int(n);
            return lk_con("Ok", &field, 1);   /* Result(Int, String) */
        }
        LkVal field = lk_str("string_to_int: not an integer");
        return lk_con("Err", &field, 1);
    }

    if (strcmp(name, "string_to_float") == 0) {
        BUILTIN_EXPECT("String", V_STR);
        uint32_t bits;
        if (parse_float_c(arg.s, &bits)) {
            LkVal field = lk_float(bits);
            return lk_con("Ok", &field, 1);   /* Result(Float, String) */
        }
        LkVal field = lk_str("string_to_float: not a float");
        return lk_con("Err", &field, 1);
    }

    fprintf(stderr, "lark: unknown builtin: %s\n", name);
    exit(1);
}


/* Number of arguments a built-in consumes; anything unlisted is unary. */
static int builtin_arity(const char* name) {
    if (strcmp(name, "string_index") == 0) return 2;
    if (strcmp(name, "string_slice") == 0) return 3;
    if (strcmp(name, "min") == 0)          return 2;
    if (strcmp(name, "max") == 0)          return 2;
    return 1;
}

/* Dispatch a fully-applied multi-argument built-in (see builtin_arity). */
static LkVal apply_builtin_n(const char* name, const LkVal* args, int n) {
    (void)n;
    if (strcmp(name, "string_index") == 0) {
        LkVal s = args[0], i = args[1];
        if (s.kind != V_STR || i.kind != V_INT) {
            fputs("lark: string_index expects (String, Int)\n", stderr); exit(1);
        }
        int32_t idx = i.i;
        size_t  len = strlen(s.s);
        if (idx >= 0 && (size_t)idx < len)
            return lk_int((unsigned char)s.s[idx]);
        return lk_int(-1);                     /* out of bounds → -1 (defined) */
    }
    if (strcmp(name, "string_slice") == 0) {
        LkVal s = args[0], lo = args[1], hi = args[2];
        if (s.kind != V_STR || lo.kind != V_INT || hi.kind != V_INT) {
            fputs("lark: string_slice expects (String, Int, Int)\n", stderr); exit(1);
        }
        int32_t len = (int32_t)strlen(s.s);
        int32_t a = lo.i < 0 ? 0 : (lo.i > len ? len : lo.i);
        int32_t b = hi.i < 0 ? 0 : (hi.i > len ? len : hi.i);
        if (a >= b) return lk_str("");
        int32_t m   = b - a;
        char*   out = AR((size_t)m + 1);
        memcpy(out, s.s + a, (size_t)m);
        out[m] = '\0';
        return lk_str(out);
    }
    if (strcmp(name, "min") == 0 || strcmp(name, "max") == 0) {
        LkVal a = args[0], b = args[1];
        if (a.kind != V_INT || b.kind != V_INT) {
            fprintf(stderr, "lark: %s expects (Int, Int)\n", name); exit(1);
        }
        if (strcmp(name, "min") == 0) return lk_int(a.i <= b.i ? a.i : b.i);
        return lk_int(a.i >= b.i ? a.i : b.i);
    }
    fprintf(stderr, "lark: unknown multi-arg builtin: %s\n", name);
    exit(1);
}

#undef BUILTIN_EXPECT


/* -- Machine state -- */

typedef enum { MODE_EVAL, MODE_RET } CekMode;

static CekMode        _mode;
static const LkExpr*  _expr;
static LkEnv*         _env;
static LkVal          _val;


/* -- Continuation stack -- */

#ifndef LARK_KONT_MAX
#  define LARK_KONT_MAX 2048
#endif

static LkFrame _kont[LARK_KONT_MAX];
static int     _ksp = 0;

static void kont_push(LkFrame f) {
    if (_ksp >= LARK_KONT_MAX) {
        fputs("lark: continuation stack overflow\n", stderr); exit(1);
    }
    _kont[_ksp++] = f;
}

static LkFrame kont_pop(void) { return _kont[--_ksp]; }


/* -- Apply a function value to an argument -- */

/*
 * Applying to a closure sets _mode = MODE_EVAL and returns 0 (caller should
 * continue the main loop).  Applying to a builtin / partial / print-IO
 * returns 1 and places the result in _val (caller should set _mode=MODE_RET).
 *
 * The split avoids a recursive call to the main loop for the common case of
 * entering a closure body.  Multi-arg applications that produce intermediate
 * closures still call cek_run_until (below) for correctness.
 */
static int apply_val(LkVal fn, LkVal arg);   /* returns 1 if result in _val */

static int apply_val(LkVal fn, LkVal arg) {
    switch (fn.kind) {
        case V_CLOSURE: {
            LkClosure* c  = fn.clos;
            LkEnv*     e  = env_bind(c->env, c->param, arg);
            if (c->rec) e = env_bind(e, c->rec, fn);
            _mode = MODE_EVAL;
            _expr = c->body;
            _env  = e;
            return 0;
        }

        case V_PARTIAL: {
            LkPartCon* pc  = fn.part;
            int        n   = pc->n + 1;
            if (n > pc->arity) {
                fprintf(stderr,
                        "lark: constructor '%s' over-applied (%d/%d args)\n",
                        pc->tag, n, pc->arity);
                exit(1);
            }
            if (n == pc->arity) {
                LkCon* c = AR(sizeof(LkCon) + (size_t)n * sizeof(LkVal));
                c->tag = pc->tag; c->n = n;
                memcpy(c->fields, pc->args, (size_t)pc->n * sizeof(LkVal));
                c->fields[pc->n] = arg;
                _val = (LkVal){ .kind=V_CON, .con=c };
            } else {
                LkPartCon* nc = AR(sizeof(LkPartCon) + (size_t)n * sizeof(LkVal));
                nc->tag = pc->tag; nc->arity = pc->arity; nc->n = n;
                memcpy(nc->args, pc->args, (size_t)pc->n * sizeof(LkVal));
                nc->args[pc->n] = arg;
                _val = (LkVal){ .kind=V_PARTIAL, .part=nc };
            }
            return 1;
        }

        case V_BUILTIN: {
            int arity = builtin_arity(fn.builtin);
            if (arity == 1) {
                _val = apply_builtin(fn.builtin, arg);
            } else {
                _val = lk_builtin_partial(fn.builtin, arity, &arg, 1);
            }
            return 1;
        }

        case V_BUILTIN_PART: {
            LkPartBuiltin* pb = fn.bpart;
            int   nn = pb->n + 1;
            LkVal acc[4];                 /* max builtin arity is 3 */
            memcpy(acc, pb->args, (size_t)pb->n * sizeof(LkVal));
            acc[pb->n] = arg;
            if (nn == pb->arity) {
                _val = apply_builtin_n(pb->name, acc, nn);
            } else {
                _val = lk_builtin_partial(pb->name, pb->arity, acc, nn);
            }
            return 1;
        }

        case V_PRINT_IO:
            if (arg.kind != V_STR) {
                fputs("lark: print expects String\n", stderr); exit(1);
            }
            printf("%s\n", arg.s);
            _val = *fn.pio;
            return 1;

        case V_DISPATCH: {
            const char* tn   = val_type(arg);
            LkVal*      impl = disp_get(fn.method, tn);
            if (!impl) {
                fprintf(stderr, "lark: no impl of '%s' for '%s'\n",
                        fn.method, tn);
                exit(1);
            }
            return apply_val(*impl, arg);
        }

        default:
            fprintf(stderr, "lark: not a function (kind=%d)\n", fn.kind);
            exit(1);
    }
}


/* -- CEK main loop -- */

/*
 * Run until the continuation stack depth returns to `stop_sp` and the
 * machine is in MODE_RET.  Used both for the top-level run (stop_sp=0) and
 * for sub-computations inside multi-arg application (stop_sp = current depth
 * after the pending frame has been popped).
 */
static LkVal cek_run_until(int stop_sp) {
    for (;;) {
        if (_mode == MODE_RET && _ksp == stop_sp) return _val;

        if (_mode == MODE_EVAL) {
            const LkExpr* e   = _expr;
            LkEnv*        env = _env;

            switch (e->kind) {

                case EXPR_LIT:
                    _mode = MODE_RET;
                    _val  = lit_val(e->lit);
                    break;

                case EXPR_VAR:
                case EXPR_CON:
                    _mode = MODE_RET;
                    _val  = env_lookup(env, e->name);
                    break;

                case EXPR_TUPLE:
                    if (e->tup.n == 0) {
                        _mode = MODE_RET; _val = lk_unit();
                    } else {
                        /* Pre-allocate the complete LkTuple (header + FAM) so that
                         * each FRAME_TUPLE pop writes directly into the final object —
                         * no per-element copies, no extra allocations. */
                        LkTuple* tup = AR(sizeof(LkTuple) +
                                          (size_t)e->tup.n * sizeof(LkVal));
                        tup->n = e->tup.n;
                        kont_push((LkFrame){
                            .kind  = FRAME_TUPLE, .env = env,
                            .tuple = { .remaining   = e->tup.elems + 1,
                                       .n_remaining = e->tup.n - 1,
                                       .tup         = tup,
                                       .n_done      = 0 }
                        });
                        _expr = e->tup.elems[0];
                    }
                    break;

                case EXPR_APPLY:
                    kont_push((LkFrame){
                        .kind     = FRAME_APPLY_FN, .env = env,
                        .apply_fn = { .args   = e->app.args,
                                      .n_args = e->app.n_args }
                    });
                    _expr = e->app.fn;
                    break;

                case EXPR_BINOP:
                    kont_push((LkFrame){
                        .kind    = FRAME_BINOP_L, .env = env,
                        .binop_l = { .op = e->binop.op, .right = e->binop.right }
                    });
                    _expr = e->binop.left;
                    break;

                case EXPR_UNARY:
                    kont_push((LkFrame){
                        .kind  = FRAME_UNARY,
                        .unary = { .op = e->unary.op }
                    });
                    _expr = e->unary.operand;
                    break;

                case EXPR_LET:
                    kont_push((LkFrame){
                        .kind = FRAME_LET, .env = env,
                        .let  = { .name = e->let.name, .body = e->let.body }
                    });
                    _expr = e->let.val;
                    break;

                case EXPR_IF:
                    kont_push((LkFrame){
                        .kind = FRAME_IF, .env = env,
                        .if_  = { .then_ = e->if_.then_, .else_ = e->if_.else_ }
                    });
                    _expr = e->if_.cond;
                    break;

                case EXPR_MATCH:
                    kont_push((LkFrame){
                        .kind  = FRAME_MATCH, .env = env,
                        .match = { .arms = e->match.arms, .n_arms = e->match.n_arms }
                    });
                    _expr = e->match.scrutinee;
                    break;

                case EXPR_LAMBDA:
                    _mode = MODE_RET;
                    _val  = lk_closure(e->lam.param, e->lam.body, env, NULL);
                    break;

                default:
                    fprintf(stderr, "lark: unknown expr kind %d\n", e->kind);
                    exit(1);
            }

        } else { /* MODE_RET — deliver _val to the top frame */
            LkFrame fr  = kont_pop();
            LkVal   val = _val;

            switch (fr.kind) {

                case FRAME_TUPLE: {
                    /* Write the just-evaluated element directly into the
                     * pre-allocated LkTuple (no memcpy, no extra allocation). */
                    fr.tuple.tup->elems[fr.tuple.n_done] = val;
                    int nd = fr.tuple.n_done + 1;
                    if (fr.tuple.n_remaining == 0) {
                        _mode = MODE_RET;
                        _val  = (LkVal){ .kind=V_TUPLE, .tup=fr.tuple.tup };
                    } else {
                        kont_push((LkFrame){
                            .kind  = FRAME_TUPLE, .env = fr.env,
                            .tuple = { .remaining   = fr.tuple.remaining + 1,
                                       .n_remaining = fr.tuple.n_remaining - 1,
                                       .tup         = fr.tuple.tup,
                                       .n_done      = nd }
                        });
                        _mode = MODE_EVAL;
                        _expr = fr.tuple.remaining[0];
                        _env  = fr.env;
                    }
                    break;
                }

                case FRAME_APPLY_FN:
                    /* val is the function; start on the first argument */
                    if (fr.apply_fn.n_args == 0) {
                        fputs("lark: internal error: application with zero arguments\n",
                              stderr);
                        exit(1);
                    }
                    kont_push((LkFrame){
                        .kind      = FRAME_APPLY_ARG, .env = fr.env,
                        .apply_arg = { .fn_val      = val,
                                       .remaining   = fr.apply_fn.args + 1,
                                       .n_remaining = fr.apply_fn.n_args - 1 }
                    });
                    _mode = MODE_EVAL;
                    _expr = fr.apply_fn.args[0];
                    _env  = fr.env;
                    break;

                case FRAME_APPLY_ARG:
                    if (fr.apply_arg.n_remaining == 0) {
                        /* Last argument — apply and stay in the loop. */
                        if (!apply_val(fr.apply_arg.fn_val, val))
                            continue;          /* closure entered; MODE_EVAL set */
                        _mode = MODE_RET;      /* builtin / partial returned _val */
                    } else {
                        /*
                         * Intermediate argument: apply fn to arg to produce a
                         * partial result, which becomes the new fn_val for the
                         * remaining args.  If the result is another closure we
                         * run it to completion first (cek_run_until with the
                         * current depth as the stopping point).
                         */
                        int save_sp = _ksp;
                        if (!apply_val(fr.apply_arg.fn_val, val)) {
                            /* Closure entered; run to completion, result in _val. */
                            cek_run_until(save_sp);
                        }
                        LkVal partial = _val;
                        kont_push((LkFrame){
                            .kind      = FRAME_APPLY_ARG, .env = fr.env,
                            .apply_arg = { .fn_val      = partial,
                                           .remaining   = fr.apply_arg.remaining + 1,
                                           .n_remaining = fr.apply_arg.n_remaining - 1 }
                        });
                        _mode = MODE_EVAL;
                        _expr = fr.apply_arg.remaining[0];
                        _env  = fr.env;
                    }
                    break;

                case FRAME_LET:
                    _mode = MODE_EVAL;
                    _expr = fr.let.body;
                    _env  = env_bind(fr.env, fr.let.name, val);
                    break;

                case FRAME_IF:
                    if (val.kind != V_BOOL) {
                        fputs("lark: if condition not Bool\n", stderr); exit(1);
                    }
                    _mode = MODE_EVAL;
                    _expr = val.b ? fr.if_.then_ : fr.if_.else_;
                    _env  = fr.env;
                    break;

                case FRAME_MATCH: {
                    int matched = 0;
                    for (int i = 0; i < fr.match.n_arms; i++) {
                        LkEnv* new_env = fr.env;
                        if (match_pat(fr.match.arms[i].pat, val, &new_env)) {
                            _mode = MODE_EVAL;
                            _expr = fr.match.arms[i].body;
                            _env  = new_env;
                            matched = 1;
                            break;
                        }
                    }
                    if (!matched) {
                        fputs("lark: non-exhaustive match\n", stderr); exit(1);
                    }
                    break;
                }

                case FRAME_BINOP_L:
                    kont_push((LkFrame){
                        .kind    = FRAME_BINOP_R,
                        .binop_r = { .op = fr.binop_l.op, .left = val }
                    });
                    _mode = MODE_EVAL;
                    _expr = fr.binop_l.right;
                    _env  = fr.env;
                    break;

                case FRAME_BINOP_R:
                    _mode = MODE_RET;
                    _val  = binop(fr.binop_r.op, fr.binop_r.left, val);
                    break;

                case FRAME_UNARY:
                    _mode = MODE_RET;
                    _val  = unaryop(fr.unary.op, val);
                    break;

                default:
                    fprintf(stderr, "lark: unknown frame kind %d\n", fr.kind);
                    exit(1);
            }
        }
    }
}


/* -- Program evaluation -- */

/* Register built-in constructors and names shared by all programs. */
static void register_builtins(void) {
    con_register("Nil",  "List",   0);
    con_register("Cons", "List",   2);
    con_register("Ok",   "Result", 1);
    con_register("Err",  "Result", 1);

    top_set("print",          lk_builtin("print"));
    top_set("read",           lk_builtin("read"));
    top_set("read_all",       lk_builtin("read_all"));
    top_set("show",           lk_builtin("show"));
    top_set("int_to_float",   lk_builtin("int_to_float"));
    top_set("float_to_int",   lk_builtin("float_to_int"));
    top_set("float_to_bits",  lk_builtin("float_to_bits"));
    top_set("int_to_string",  lk_builtin("int_to_string"));
    top_set("float_to_string",lk_builtin("float_to_string"));
    top_set("int_abs",        lk_builtin("int_abs"));
    top_set("min",            lk_builtin("min"));
    top_set("max",            lk_builtin("max"));
    top_set("float_abs",      lk_builtin("float_abs"));
    top_set("float_sqrt",     lk_builtin("float_sqrt"));
    top_set("float_floor",    lk_builtin("float_floor"));
    top_set("float_ceil",     lk_builtin("float_ceil"));
    top_set("string_length",  lk_builtin("string_length"));
    top_set("string_index",   lk_builtin("string_index"));
    top_set("string_slice",   lk_builtin("string_slice"));
    top_set("char_to_string", lk_builtin("char_to_string"));
    top_set("string_to_int",  lk_builtin("string_to_int"));
    top_set("string_to_float",lk_builtin("string_to_float"));
    top_set("Nil",  lk_con("Nil", NULL, 0));
    top_set("Cons", lk_partial("Cons", 2, NULL, 0));
    top_set("Ok",   lk_partial("Ok",  1, NULL, 0));
    top_set("Err",  lk_partial("Err", 1, NULL, 0));
    top_set("True",  lk_bool(1));
    top_set("False", lk_bool(0));
}

static void eval_prog(const LkProg* prog) {
    for (int i = 0; i < prog->n_decls; i++) {
        const LkDecl* d = prog->decls[i];
        switch (d->kind) {

            case DECL_FN:
                /* Top-level closures capture NULL local env; lookups fall
                 * through to top_env so mutual recursion works without
                 * any backpatching. */
                top_set(d->name, lk_closure(d->fn.param, d->fn.body,
                                            NULL, d->name));
                break;

            case DECL_LET:
                _mode = MODE_EVAL; _expr = d->let_val; _env = NULL;
                top_set(d->name, cek_run_until(0));
                break;

            case DECL_TYPE:
                for (int j = 0; j < d->type_.n_variants; j++) {
                    const LkVariant* v = &d->type_.variants[j];
                    con_register(v->name, d->name, v->arity);
                    LkVal cv = v->arity == 0
                        ? lk_con(v->name, NULL, 0)
                        : lk_partial(v->name, v->arity, NULL, 0);
                    top_set(v->name, cv);
                }
                break;

            case DECL_IMPL:
                for (int j = 0; j < d->impl.n_methods; j++) {
                    const LkMethod* m = &d->impl.methods[j];
                    LkVal closure = lk_closure(m->param, m->body, NULL, m->name);
                    disp_set(m->name, d->name, closure);
                    if (!top_get(m->name))
                        top_set(m->name, lk_dispatch(m->name));
                }
                break;
        }
    }
}


/* -- Entry point -- */

void cek_run(const LkProg* prog) {
    _ar.base = (char*)malloc(LARK_ARENA_SIZE);
    if (!_ar.base) { fputs("lark: cannot allocate arena\n", stderr); exit(1); }
    _ar.cap  = LARK_ARENA_SIZE;
    _ar.used = 0;
    _ksp  = 0;
    _top_n = 0;
    _disp_n = 0;
    _con_n  = 0;

    register_builtins();
    eval_prog(prog);

    LkVal* main_fn = top_get("main");
    if (!main_fn) {
        fputs("lark: no main\n", stderr); exit(1);
    }

    /* Call main(io) */
    if (!apply_val(*main_fn, lk_io())) {
        cek_run_until(0);
    }
}
