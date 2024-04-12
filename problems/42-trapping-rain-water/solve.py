class Solution:
    def trap(self, height: List[int]) -> int:
        result = 0
        last_indices = [0]
        for index, element in enumerate(height[1:], start=1):
            while height[last_indices[-1]] < element:
                try:
                    last_index = last_indices.pop()
                    if not last_indices:
                        break
                except IndexError:
                    break
                past_index = last_indices[-1]
                current_height = min(element, height[past_index]) - height[last_index]
                current_width = index - past_index - 1
                result += current_height * current_width
            last_indices.append(index)
        return result
