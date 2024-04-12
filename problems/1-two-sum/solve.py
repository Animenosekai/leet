class Solution:
    def twoSum(self, nums: List[int], target: int) -> List[int]:
        for index, element in enumerate(nums):
            try:
                return [index, nums.index(target - element, index + 1)]
            except ValueError:
                continue