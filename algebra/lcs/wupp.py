def edit(reference, observed):

    matrix = [[None for _ in range(len(observed) + 1)]
              for _ in range(len(reference) + 1)]

    def func(idx):
        limit = max(diagonals[idx + offset - 1], diagonals[idx + offset + 1])
        print(f"limit: {limit}")

        if idx >= 0:
            row = diagonals[idx + offset] + 1
            col = row + idx
            print(f"row and col before while {row}, {col}")

            while (row <= len(reference) and
                   col <= len(observed) and
                   (row <= limit or reference[row - 1] == observed[col - 1])):

                print(row, col, reference[row - 1] == observed[col - 1])
                matrix[row][col] = abs(delta) + 2 * it
                row += 1
                col += 1

            if col <= len(observed) and row <= len(reference):
                matrix[row][col] = abs(delta) + 2 * it + 2

            return min(row, len(reference))
        else:
            col = diagonals[idx + offset] + 1
            row = col - idx
            print(f"row and col before while {row}, {col}")

            while (row <= len(reference) and
                   col <= len(observed) and
                   (col <= limit or reference[row - 1] == observed[col - 1])):

                print(row, col, reference[row - 1] == observed[col - 1])
                matrix[row][col] = abs(delta) + 2 * it
                row += 1
                col += 1

            if col <= len(observed) and row <= len(reference):
                matrix[row][col] = abs(delta) + 2 * it + 2

            return min(col, len(observed))

    diagonals = [0] * (len(reference) + len(observed) + 3)
    offset = len(reference) + 1
    delta = len(observed) - len(reference)

    it = 0

    #while diagonals[delta + offset] <= max(len(observed), len(reference)):
    while True:
        print(f"it in while: {it}")

        if delta >= 0:
            lower = range(-it, delta)
            upper = range(delta + it, delta, -1)
        else:
            lower = range(delta - it, delta)
            upper = range(it, delta, -1)

        for diag_idx in lower:
            print(f"lower: {diag_idx}")
            diagonals[diag_idx + offset] = func(diag_idx)

        for diag_idx in upper:
            print(f"upper: {diag_idx}")
            diagonals[diag_idx + offset] = func(diag_idx)

        print(f"delta: {delta}")
        diagonals[delta + offset] = func(delta)

        print(f"diagonals: {diagonals}")
        import pprint
        pprint.pprint(matrix, width=20)

        if diagonals[delta+offset] > len(reference):
            break
        if diagonals[delta+offset] > len(observed):
            break

        it += 1

    # from pprint import pprint
    # pprint(matrix)
    print(diagonals)

    print(f"it at end: {it}")

    return abs(delta) + 2 * it, matrix