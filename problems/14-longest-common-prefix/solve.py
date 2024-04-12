class Solution:
    def longestCommonPrefix(self, strs: List[str]) -> str:
        def longest_prefix(first: str, second: str) -> str:
            result = ""
            for letter1, letter2 in zip(first, second):
                if letter1 != letter2:
                    return result
                result += letter1
            return result
        if not strs:
            return ""
        if len(strs) == 1:
            return strs[0]
        longest = longest_prefix(strs[0], strs[1])
        if not longest:
            return ""
        for element in strs[2:]:
            longest = longest_prefix(longest, element)
        return longest
