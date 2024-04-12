CHARACTERS = {"(", "[", "{"}
class Solution:
    def isValid(self, s: str) -> bool:
        stack = []
        for letter in s:
            if letter in CHARACTERS:
                stack.append(letter)
            else:
                try:
                    last = stack.pop()
                except IndexError:
                    return False
                if letter == ")" and last != "(":
                    return False
                if letter == "]" and last != "[":
                    return False
                if letter == "}" and last != "{":
                    return False
        return not stack