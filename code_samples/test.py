import numpy as np

SIZE = 5
springerX = [2, 1, -1, -2, -2, -1, 1, 2]
springerY = [1, 2, 2, 1, -1, -2, -2, -1]

spielfeld = np.zeros(shape=(SIZE, SIZE))


def sprung(x, y, nr):
    if nr == SIZE * SIZE:
        spielfeld[x, y] = nr
        return True
    else:
        for versuch in range(0, 8):
            x_n = x + springerX[versuch]
            y_n = y + springerY[versuch]
            if 0 <= x_n < SIZE and 0 <= y_n < SIZE and spielfeld[x_n, y_n] == 0 and sprung(x_n, y_n, nr + 1):
                spielfeld[x, y] = nr
                print("")
                return True
    # spielfeld[x, y] = 0
    return False


print(sprung(0, 0, 1))
print(spielfeld)
