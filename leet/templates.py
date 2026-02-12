"""The templates for the markdown files."""

QUESTION_MARKDOWN = """\
---
id: {id}
slug: "{slug}"
difficulty: "{difficulty}"
likes: {likes}
dislikes: {dislikes}
category: "{category}"
---

# [{title}](https://leetcode.com/problems/{slug}/)

{content}

## Topics

{topics}

## Similar Questions

{similar_questions}

## Stats

| Total Accepted | Total Submissions | Acceptance Rate |
| -------------- | ----------------- | --------------- |
| {total_accepted} | {total_submissions} | {acceptance_rate}% |
"""
# Variables: {slug}, {difficulty}, {likes}, {dislikes}, {category}, {title},
# {content}, {topics}, {similar_questions}, {total_accepted},
# {total_submissions}, {acceptance_rate}
