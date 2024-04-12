ROMAN_TO_INT = {
    "I": 1,
    "V": 5,
    "X": 10,
    "L": 50,
    "C": 100,
    "D": 500,
    "M": 1000,
}
class Solution:
    def romanToInt(self, s: str) -> int:
        result = 0
        last = 0
        for c in s:
            current = ROMAN_TO_INT[c]
            result += current
            if current > last:
                result -= 2 * last
            last = current
        return result