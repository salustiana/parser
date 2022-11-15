import sys
from collections import namedtuple

# XXX: these are defined in "lexer.h"
TK_STR = 149
TK_ID = 150
BN_ES = -8
TK_EOF = -1

grammar = dict()
start_sym = ""
Token = namedtuple("Token", ["type", "str_val"])
tk = Token(0, 0)
curr_nt = ""
curr_prod = list()
tk_n = 0


def print_token(tk):
    print(tk.type, end='\t')
    if tk.type == TK_ID or tk.type == TK_STR:
        print(tk.str_val)
        return
    print(chr(tk.type))


def repr_sym(sym):
    if sym == TK_ID:
        return "`id`"
    if sym == TK_STR:
        return "`str`"
    if sym == BN_ES or sym == "":
        return "``"
    try:
        ret = "`" + str(chr(sym)) + "`"
    except (TypeError, ValueError):
        ret = "<" + str(sym) + ">"
    return ret


def tk_gen():
    global tk_n
    for tk in sys.stdin.readlines():
        t, v = tk.split('\t', 1)
        tk_n += 1
        yield (int(t), v.rstrip())

tokens = tk_gen()


def expected(exp):
    raise Exception(
        f"on token {tk_n} \"{chr(tk.type)}\": "
        f"expected {exp}"
    )


def next_token():
    global tk
    tk = Token(*tokens.__next__())


def skip_tks(chars):
    for char in chars:
        if tk.type != ord(char):
            expected(chars)
        next_token()


def add_prod():
    global grammar
    global curr_nt
    global curr_prod

    grammar[curr_nt].append(curr_prod.copy())
    curr_prod = list()


def create_entry(key, table):
    table[key] = list()


def print_grammar():
    for nt, prods in grammar.items():
        print("<", nt, "> ::= ", sep="", end="")
        first = 1
        for prod in prods:
            if first:
                first = 0
            else:
                print("\t| ", end="")
            for sym in prod:
                print(repr_sym(sym), "", end="")
            print()
        print()


def print_first(sym):
    global first_tab
    print("FIRST(", sym, "): ", sep="")
    print("\t", [repr_sym(s) for s in first_tab[sym]])


def print_follow(nt):
    global follow_tab
    print("FOLLOW(", nt, "): ", sep="")
    print("\t", [repr_sym(s) for s in follow_tab[nt]])


def parse_prods():
    global tk
    global curr_nt
    global curr_prod

    more_input = 1
    while more_input:
        if tk.type == ord('|'): # new prod for curr_nt
            add_prod()
            next_token()
            continue

        elif tk.type == ord('<'): # parse nonterm
            next_token()
            if tk.type != TK_ID:
                expected("nonterm")
            nt = tk.str_val
            next_token()
            if tk.type != ord('>'):
                expected("'>'")
            try: # BN could end here
                next_token()
            except StopIteration:
                more_input = 0
            if tk.type == ord(':'): # we are in a new def
                skip_tks("::=")
                add_prod()
                curr_nt = nt # start prod for new def
                if grammar.get(curr_nt) == None:
                    create_entry(curr_nt, grammar)
                continue
            curr_prod.append(nt) # add the nonterm to curr_prod

        elif tk.type == ord('`'): # parse a terminal
            next_token()
            if tk.type == ord('`'): # empty string (``)
                curr_prod.append(BN_ES)
                try: # BN could end here
                    next_token()
                except StopIteration:
                    more_input = 0
                continue
            curr_prod.append(tk.type)
            next_token()
            if tk.type != ord('`'):
                expected("'`'")
            try: # BN could end here
                next_token()
            except StopIteration:
                more_input = 0

        else:
            print_token(tk)
            expected("a token supported by BN syntax")

        if not more_input:
            add_prod()


def parse_bn():
    global tk
    global curr_nt
    global curr_prod
    global start_sym

    next_token()
    if tk.type != ord('<'):
        expected("\"<symbol>\"")
    next_token()
    if tk.type != TK_ID:
        expected("\"symbol\"")

    curr_nt = tk.str_val
    start_sym = curr_nt
    next_token()

    if tk.type != ord('>'):
        expected("'>'")
    next_token()

    skip_tks("::=")

    if grammar.get(curr_nt) == None:
        grammar[curr_nt] = list()
    curr_prod = list()

    try:
        parse_prods()
    except StopIteration:
        return


# TODO: algorithm to remove cycles and e-prods
# all nullable nonterms can be found with FIRST(nonterm)

# XXX: grammar must have no cycles or e-prods
def elim_left_rec():
    global grammar

    # list the non terms in some order
    non_terms = list()
    for nt in grammar.keys():
        non_terms.append(nt)

    for i, nt_i in enumerate(non_terms):
        # replace prods of the form nt_i -> nt_j x
        # for nt_i -> y1 x | y2 x ... | yk x
        # where x is any symbol string and yn are
        # all current nt_j productions (immediate left
        # recursion for nt_j has already been eliminated,
        # because j < i)
        for j, nt_j in enumerate(non_terms):
            if j == i:
                break
            for p_i in range(len(grammar[nt_i])):
                if grammar[nt_i][p_i][0] == nt_j:
                    prod_tail = grammar[nt_i].pop(p_i)[1:]
                    for j_prod in grammar[nt_j]:
                        grammar[nt_i].append(j_prod + prod_tail)

        # eliminate immediate left recursion for nt_i
        left_rec_prod_tails = list()
        non_left_rec_prods = list()
        for prod in grammar[nt_i]:
            if prod[0] == nt_i:
                left_rec_prod_tails.append(prod[1:])
            else:
                non_left_rec_prods.append(prod)

        if not left_rec_prod_tails:
            continue

        grammar[nt_i] = list()
        nt_i_prime = nt_i + "_1"
        create_entry(nt_i_prime, grammar)
        for nlrp in non_left_rec_prods:
            grammar[nt_i].append(nlrp + [nt_i_prime])
        for lrpt in left_rec_prod_tails:
            grammar[nt_i_prime].append(lrpt + [nt_i_prime])
        grammar[nt_i_prime].append([BN_ES])


first_tab = dict()

# XXX grammar must have no left-recursion
def first(symbol):
    global grammar

    if type(symbol) == int: # symbol is a terminal
        return [symbol] # FIRST(term) = { term }

    if first_tab.get(symbol): # return FIRST(symbol) if it was already computed
        return first_tab[symbol]

    create_entry(symbol, first_tab)
    for prod in grammar[symbol]:
        # add FIRST(sym) for every sym in the prod,
        # until sym cannot be reduced to the empty string
        # (BN_ES is not in first(sym))
        added_es = 1
        for sym in prod:
            if not added_es:
                break

            added_es = 0
            for s in first(sym):
                if s not in first_tab[symbol]:
                    first_tab[symbol].append(s)
                if s == BN_ES:
                    added_es = 1

    return first_tab[symbol]


def compute_first_tab():
    for sym in grammar.keys():
        first(sym)


def first_of_sym_string(sym_list):
    ret = list()
    all_have_es = 1
    added_es = 1
    for sym in sym_list:
        if not added_es:
            all_have_es = 0
            break
        added_es = 0
        for s in first(sym):
            if s == BN_ES:
                added_es = 1
            else:
                ret.append(s)
    # add the empty string only if every
    # symbol in the string is nullable
    if all_have_es:
        ret.append(BN_ES)
    return ret


follow_tab = dict()

def compute_follow_tab():
    global follow_tab
    global start_sym

    create_entry(start_sym, follow_tab)
    follow_tab[start_sym].append(TK_EOF)

    added_to_follow = 1
    while added_to_follow:
        added_to_follow = 0
        for nt in grammar.keys():
            for prod in grammar[nt]:
                for i, s in enumerate(prod):
                    if type(s) != str: # if s is not nonterm
                        continue

                    if follow_tab.get(s) == None:
                        create_entry(s, follow_tab)

                    # if A -> xBy add {FIRST(y) - BN_ES} to FOLLOW(B)
                    # (where x and y are strings)
                    if i < (len(prod)-1):
                        for term in first_of_sym_string(prod[i+1:]):
                            if term != BN_ES and term not in follow_tab[s]:
                                follow_tab[s].append(term)
                                added_to_follow = 1

                    # if A->xB or (A->xBy and BN_ES is in FIRST(y))
                    # then add FOLLOW(A) to FOLLOW(B)
                    if i == (len(prod)-1) or (
                            BN_ES not in first_of_sym_string(prod[i+1:])
                    ):
                        for term in follow_tab[nt]:
                            if term not in follow_tab[s]:
                                follow_tab[s].append(term)
                                added_to_follow = 1



if __name__ == "__main__":
    parse_bn()
    elim_left_rec()
    print_grammar()

    compute_first_tab()
    for nt in grammar.keys():
        print_first(nt)
    print()

    compute_follow_tab()
    for nt in grammar.keys():
        print_follow(nt)
