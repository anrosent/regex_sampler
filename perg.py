#!/usr/bin/env python3
#
# RESAMPLE.py: Generates a stream of strings (roughly) uniformly sampled
# from the set of strings matching a given regex
#
# anrosent (anson.rosenthal@gmail.com)
import pdb
import sys, string, argparse
from random import randint, choice, random
from re import sre_parse
from itertools import product, chain

# Parse the regex so we can traverse the tree
def parse(s):
    return sre_parse.parse(s)

# Predefined character categories
# TODO: add 'category_not_XXX' support
# TODO: add whitespace support
CATEGORIES = { 'category_digit' : string.digits, 'category_word': string.ascii_letters }

# Sampler function in case we run into an unknown type tag
UNK = lambda x: ''

# Repeat probability for samples on infinite repitition intervals
INF_REPEAT_P = 0.8

# Draws a sample from the geometric distribution on [start, inf) with success
# parameter p
def sample_geometric(p, start=0):
    ctr = start
    while random() < p:
        ctr += 1
    return ctr
        

# Component Sampler functions

# Trival sample from literally matching strings
def sample_literal(x): return chr(x)

def enum_literal(x): return chr(x)

# Sample from on of the predefined character categories
def sample_category(c):
    return choice(CATEGORIES[c])

def enum_category(c):
    return CATEGORIES[c]

# Sample from a range of ASCII values 
# e.g. a-z, A-Z, 0-9
def sample_range(rg):
    s, e = rg
    return chr(randint(s, e))

def enum_range(rg):
    s,e = rg
    return map(chr, range(s,e))

# Sample from one of the regexes in the matching set
def sample_branch(bs):
    _, d = bs
    return sample(choice(d))

def enum_branch(bs):
    _, d = bs
    return chain(*map(enum_gen, d))

# Sample from the set of matching characters 
def sample_in(opts):
    return sample_single(choice(opts))

def enum_in(opts):
    return chain(*map(enum_single, opts))

# Sample repitition interval for given regex
def sample_max_repeat(node):

    # Unpack start, end of repitition interval and regex to repeat
    s, e, d = node

    # If bounded repitition, sample uniformly
    if e < 4294967295:
        repititions = randint(s,e)
    else:
        
        # Interval is unbounded above, so sample geometric distribution
        repititions = sample_geometric(INF_REPEAT_P, s)

    return ''.join(sample(d) for _ in range(repititions))

def enum_max_repeat(node):
    s, e, d = node
    #pdb.set_trace()
    matches = list(enum_gen(d))
    return chain(*(map(joiner, product(matches, repeat=repititions)) for repititions in range(s, e+1)))

# NOTE: considered equivalent to sampling from greedy repeat matcher.
# May or may not be completely equivalent
def sample_min_repeat(node):
    return sample_max_repeat(node)

def enum_min_repeat(node):
    return enum_max_repeat(node)

# Match any character
def sample_any(d):
    return choice(string.printable)

def enum_any(d):
    return string.printable

# Sample from subpattern and cache for backreferences
# FIXME: still doesn't handle assert and assert_not subpatterns
def sample_subpattern(p):
    subpattern_id, d = p
   
    # Sample subpattern and cache
    sampled = sample(d)

    # Check if captured subpattern
    if subpattern_id:
        SUBPATTERNS[subpattern_id] = sampled

    return sampled 

def enum_subpattern(p):
    raise NotImplementedError

# Lookup referenced group and sample from it
def sample_groupref(ref):
    return SUBPATTERNS[ref]

def enum_groupref(ref):
    raise NotImplementedError

# Regex parse node names that we can sample
SAMPLERS = {"literal", "branch", "in", "range", "category", "max_repeat", 
            "any", "subpattern", "min_repeat", 'groupref'}

enum_table = {s: eval("enum_%s" % s) for s in SAMPLERS}

# Map to keep track of subpatterns we see
SUBPATTERNS = {}

# Recursive Sampling functions 

# Sample a single node in the regex
def sample_single(node):

    # Unpack node type and data
    t, data = node

    # Use sampler specified by node type on data
    return (eval("sample_%s" % t) if t in SAMPLERS else UNK)(data)

def enum_single(node):
    #pdb.set_trace()
    t, data = node
    return enum_table[t](data)

# Generates one sample from the (roughly) uniform distribution on the set of strings matching
# the regex whose parse tree is given as argument
def sample(parsed):
    return ''.join(map(sample_single, parsed))

def joiner(t):
    #pdb.set_trace()
    return ''.join(t)

def enum_gen(parsed):
    return map(joiner, product(*list(map(enum_single, parsed))))

# A generator of (roughly) uniform samples from the set of strings matching the regex
# NOTE: This is not actually a uniform sample, for the following reasons
#   - For 'at least n times' patterns, interval [n, inf) is sampled using a geometric distribution
#   - Not sure whether the entire set of matches is actually generable using this scheme 
#     for all regexes.. 
def sampler(s, enum=False):
    tree = parse(s)
    if enum:
        for f in enum_gen(tree):
            yield f
    else:
        while True:
            yield sample(tree)
        
