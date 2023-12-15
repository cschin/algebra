"""Extract canonical variant representations from all minimal
LCS alignments with support for tandem repeats and complex variants."""


from collections import deque
from ..lcs import lcs_graph
from ..lcs.supremals import supremal, supremal_sequence, trim
from ..variants import Variant, patch, reverse_complement


def canonical(observed, root):
    """Traverse (BFS) the LCS graph to extract the canonical variant,
    i.e., minimize the number separate variants within an allele.

    If there are multiple minimal variant representations (locally), a
    (local) supremal variant will be created. This allows for the
    detection of tandem repeats as well as complex variants.

    Parameters
    ----------
    observed : str
        The observed sequence.
    root : `_Node` (opaque data type)
        The root of the LCS graph.

    Returns
    -------
    list
        The canonical list of variants (allele).

    See Also
    --------
    `algebra.lcs.lcs_graph` : Constructs the LCS graph.
    """

    def lowest_common_ancestor(n_a, e_a, n_b, e_b):
        while n_a:
            n = n_b
            while n:
                if n == n_a:
                    return n_a, e_a, e_b
                n, e_b, _ = visited[n]
            n_a, e_a, _ = visited[n_a]

    shift = root.row
    queue = deque([(root, None, None, 0)])
    visited = {}

    while queue:
        node, parent, edge, distance = queue.popleft()

        if not node.edges:
            sink = node

        if node in visited:
            other_parent, other_edge, other_distance = visited[node]

            if distance > other_distance:
                continue

            lca, edge_a, edge_b = lowest_common_ancestor(other_parent, other_edge, parent, edge)
            start = min(edge_a.start, edge_b.start)

            if other_parent != parent and parent.row == other_parent.row and parent.col == other_parent.col:
                end = max(parent.row, visited[parent][1].end, visited[other_parent][1].end)
                delins = Variant(start, end, observed[lca.col - shift:parent.col - shift])
                visited[other_parent] = lca, delins, distance - 1
            else:
                end = max(node.row, edge.end, other_edge.end)
                delins = Variant(start, end, observed[lca.col - shift:node.col - shift])
                visited[node] = lca, delins, distance

        else:
            visited[node] = parent, edge, distance

            for succ_node, succ_edge in node.edges:
                queue.append((succ_node, node, succ_edge, distance + 1))

    variants = []
    while sink:
        sink, variant, _ = visited[sink]
        if variant:
            variants.insert(0, variant)

    return variants


def diagonal(reference, observed, root):
    """Experimental minimal canonical represantion.
    """
    diff = len(reference) - len(observed)
    variants = []
    node = root
    while True:
        best = None
        best_edge = None
        for child, edge in node.edges:
            child_diff = child.row - child.col
            if best is None or abs(child_diff) < abs(best.row - best.col):
                best = child
                best_edge = edge
            if child_diff == diff:
                best = child
                best_edge = edge
                break

        if not best:
            return variants

        variants.append(best_edge)
        node = best


def extract_sequence(reference, observed):
    """Extract the canonical variant representation (allele) for a
    reference and observed sequence."""
    variant, root = supremal_sequence(reference, observed)
    return canonical(variant.sequence, root), variant, root


def extract_supremal(reference, variant):
    """Extract the canonical variant representation (allele) for a
    supremal variant."""
    root = lcs_graph(reference[variant.start:variant.end], variant.sequence, variant.start)
    return canonical(variant.sequence, root, 0), variant, root


def extract(reference, variants):
    """Extract the canonical variant representation together with its
    supremal representation for an allele."""
    variant, root = supremal(reference, variants)
    observed = patch(reference, variants)
    return canonical(observed, root, 0), variant, root


def to_hgvs(variants, reference):
    """Experimental version of HGVS serialization with support for
    tandem repeats and complex variants."""
    def repeats(word):
        length = 0
        idx = 1
        lps = [0] * len(word)
        while idx < len(word):
            if word[idx] == word[length]:
                length += 1
                lps[idx] = length
                idx += 1
            elif length != 0:
                length = lps[length - 1]
            else:
                lps[idx] = 0
                idx += 1

        pattern = len(word) - length
        if pattern == 0:
            return "", 0, 0
        return word[:pattern], len(word) // pattern, len(word) % pattern

    def to_hgvs_position(start, end):
        if end - start == 1:
            return f"{start + 1}"
        if start == end:
            return f"{start}_{start + 1}"
        return f"{start + 1}_{end}"

    def hgvs(variant, reference):
        inserted_unit, inserted_number, inserted_remainder = repeats(variant.sequence)
        deleted = reference[variant.start:variant.end]
        deleted_unit, deleted_number, deleted_remainder = repeats(deleted)

        # Select a non-minimal repeat unit if reference and observed are
        # in agreement.
        diff = len(inserted_unit) - len(deleted_unit)
        if diff < 0 and deleted_unit == variant.sequence[:len(inserted_unit) + -diff]:
            inserted_unit = deleted_unit
            inserted_number = 1
        elif diff > 0 and inserted_unit == deleted[:len(deleted_unit) + diff]:
            deleted_unit = inserted_unit
            deleted_number = 1
            deleted_remainder -= diff

        # Repeat structure
        if deleted_unit == inserted_unit:
            if deleted_number == inserted_number:
                raise ValueError("empty variant")

            # Duplication
            if deleted_number == 1 and inserted_number == 2:
                return f"{to_hgvs_position(variant.start + inserted_remainder, variant.start + inserted_remainder + len(inserted_unit))}dup"
            return f"{to_hgvs_position(variant.start, variant.end - deleted_remainder)}{inserted_unit}[{inserted_number}]"

        # Prefix and suffix trimming
        start, end = trim(deleted, variant.sequence)
        trimmed = Variant(variant.start + start, variant.end - end, variant.sequence[start:len(variant.sequence) - end])

        # Inversion
        if len(trimmed.sequence) > 1 and trimmed.sequence == reverse_complement(reference[trimmed.start:trimmed.end]):
            return f"{to_hgvs_position(trimmed.start, trimmed.end)}inv"

        # Deletion/insertion with repeated insertion
        inserted_unit, inserted_number, inserted_remainder = repeats(trimmed.sequence)
        if inserted_number > 1:
            suffix = f"{inserted_unit}[{inserted_number}]"
            if inserted_remainder:
                suffix = f"[{suffix};{inserted_unit[:inserted_remainder]}]"

            if trimmed.start == trimmed.end:
                return f"{to_hgvs_position(trimmed.start, trimmed.end)}ins{suffix}"
            return f"{to_hgvs_position(trimmed.start, trimmed.end)}delins{suffix}"

        # All other variants
        return trimmed.to_hgvs(reference)

    if not variants:
        return "="

    if len(variants) == 1:
        return hgvs(variants[0], reference)

    return f"[{';'.join([hgvs(variant, reference) for variant in variants])}]"
