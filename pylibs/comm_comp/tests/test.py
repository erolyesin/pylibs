#!/bin/python3

import math
import os
import random
import re
import sys


#
# Complete the 'saveThePrisoner' function below.
#
# The function is expected to return an INTEGER.
# The function accepts following parameters:
#  1. INTEGER n
#  2. INTEGER m
#  3. INTEGER s
#
# 13 140874526 1
# 5 838370030 1
# 13
# 5
def saveThePrisoner(n, m, s):
    offset = s - 1
    if n == m or not m % n:
        if s == 1:
            return n
        return offset
    if m < n < (m + offset):
        return m + offset - n
    if (m % n + offset) > n:
        return (m % n + offset) % n
    return m % n + offset


if __name__ == '__main__':
    t = int(input().strip())

    for t_itr in range(t):
        first_multiple_input = input().rstrip().split()

        n = int(first_multiple_input[0])

        m = int(first_multiple_input[1])

        s = int(first_multiple_input[2])

        result = saveThePrisoner(n, m, s)

        print(str(result))
    print("DONE")
