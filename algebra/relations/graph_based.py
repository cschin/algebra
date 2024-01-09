"""Functions to compare LCS graphs."""


from itertools import product
from ..lcs import edit_distance
from .relation import Relation


def are_equivalent(reference, lhs, rhs):
    """Check if two LCS graphs are equivalent."""
    return supremal_based_are_equivalent(reference, lhs.supremal, rhs.supremal)


def contains(reference, lhs, rhs):
    """Check if `lhs` contains `rhs`."""
    return supremal_based_contains(reference, lhs.supremal, rhs.supremal)


def is_contained(reference, lhs, rhs):
    """Check if `lhs` is contained in `rhs`."""
    return supremal_based_contains(reference, rhs.supremal, lhs.supremal)


def are_disjoint(reference, lhs, rhs):
    """Check if two LCS graphs are disjoint."""
    return compare(reference, lhs, rhs) == Relation.DISJOINT


def have_overlap(reference, lhs, rhs):
    """Check if two LCS graphs overlap."""
    return compare(reference, lhs, rhs) == Relation.OVERLAP


def compare(reference, lhs, rhs):
    """Compare two LCS graphs.

    Parameters
    ----------
    reference : str
        The reference sequence.
    lhs : `LCSgraph`
        The LCS graph on the left-hand side.
    rhs : `LCSgraph`
        The LCS graph on the right-hand side.

    Returns
    -------
    `Relation`
        The relation between the two LCS graphs.
    """

    if lhs.supremal == rhs.supremal:
        return Relation.EQUIVALENT

    if lhs.supremal.is_disjoint(rhs.supremal):
        return Relation.DISJOINT

    start = min(lhs.supremal.start, rhs.supremal.start)
    end = max(lhs.supremal.end, rhs.supremal.end)

    # TODO: class method on LCSgraph?
    def observed(supremal):
        return (reference[min(start, supremal.start):supremal.start] +
                supremal.sequence +
                reference[supremal.end:max(end, supremal.end)])

    lhs_observed = observed(lhs.supremal)
    rhs_observed = observed(rhs.supremal)
    distance = edit_distance(lhs_observed, rhs_observed)

    if lhs.distance + rhs.distance == distance:
        return Relation.DISJOINT

    if lhs.distance - rhs.distance == distance:
        return Relation.CONTAINS

    if rhs.distance - lhs.distance == distance:
        return Relation.IS_CONTAINED

    for lhs_variant, rhs_variant in product(lhs.edges(), rhs.edges()):
        if not lhs_variant.is_disjoint(rhs_variant):
            return Relation.OVERLAP

    return Relation.DISJOINT
