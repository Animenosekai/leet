import math


class Solution:
    def __init__(self) -> None:
        """Initialize the solution"""
        self.memory: dict[int, bool] = {1: False, 2: True, 3: True}

    def is_prime(self, n: int) -> bool:
        """
        Checks if the input number is prime

        Parameters
        ----------
        n: int

        Returns
        -------
        bool
        """
        if n in self.memory:
            return self.memory[n]
        if n % 2 == 0 or n % 3 == 0:
            self.memory[n] = False
            return False
        for i in range(5, int(math.sqrt(n) + 1), 6):
            if n % i == 0 or n % (i + 2) == 0:
                self.memory[n] = False
                return False
        self.memory[n] = True
        return True

    def decompose(self, n: int):
        """
        Decomposes the input number into its prime factors

        Parameters
        ----------
        n: int
            The input number

        Yields
        ------
        int
            The prime factors of the input number
        """
        for element in range(2, n + 1):
            if not self.is_prime(element):
                continue
            while n % element == 0:
                n = n // element
                yield element

    def judgeSquareSum(self, c: int) -> bool:
        """
        This solution uses Fermat's theorem on sums of two squares

        Parameters
        ----------
        c: int
            The input number

        Returns
        -------
        bool
            True if the input number can be represented as the sum of two squares
            False otherwise
        """
        if self.is_prime(c) and c % 2 == 1:
            return c % 4 != 3
        # Count for the current element in the decomposition
        count = 0
        for element in self.decompose(c):
            # Using "Fermat's theorem on sums of two squares"
            # ref: https://en.wikipedia.org/wiki/Fermat%27s_theorem_on_sums_of_two_squares
            if element % 4 == 3:
                count += 1
            elif count % 3 != 0:
                return False
            else:
                count = 0
        return True

