# Requests

## Get the question details (title, id, difficulty, etc.)

```graphql
query questionTitle($titleSlug: String!) {
  question(titleSlug: $titleSlug) {
    questionId
    title
    titleSlug
    difficulty
    likes
    dislikes
    categoryTitle
  }
}
```

## Get the question content (description, examples, etc.)

```graphql
query questionContent($titleSlug: String!) {
  question(titleSlug: $titleSlug) {
    content
    mysqlSchemas
    dataSchemas
  }
}
```

## Get some information about the tests

```graphql
query consolePanelConfig($titleSlug: String!) {
  question(titleSlug: $titleSlug) {
    questionId
    questionFrontendId
    questionTitle
    enableDebugger
    enableRunCode
    enableSubmit
    enableTestMode
    exampleTestcaseList
    metaData
  }
}
```

## Get information about the solution boilerplates

```graphql
query questionEditorData($titleSlug: String!) {
  question(titleSlug: $titleSlug) {
    questionId
    questionFrontendId
    codeSnippets {
      lang
      langSlug
      code
    }
    envInfo
    enableRunCode
    hasFrontendPreview
    frontendPreviews
  }
}
```

## Get topics

```graphql
query singleQuestionTopicTags($titleSlug: String!) {
  question(titleSlug: $titleSlug) {
    topicTags {
      name
      slug
    }
  }
}
```

## Get acceptation stats

```graphql
query questionStats($titleSlug: String!) {
  question(titleSlug: $titleSlug) {
    stats
  }
}
```

## Get similar questions

```graphql
query SimilarQuestions($titleSlug: String!) {
  question(titleSlug: $titleSlug) {
    similarQuestionList {
      difficulty
      titleSlug
      title
      translatedTitle
      isPaidOnly
    }
  }
}
``````

## Get solutions

```graphql
query communitySolutions($questionSlug: String!, $skip: Int!, $first: Int!, $query: String, $orderBy: TopicSortingOption, $languageTags: [String!], $topicTags: [String!]) {
  questionSolutions(
    filters: {questionSlug: $questionSlug, skip: $skip, first: $first, query: $query, orderBy: $orderBy, languageTags: $languageTags, topicTags: $topicTags}
  ) {
    hasDirectResults
    totalNum
    solutions {
      id
      title
      commentCount
      topLevelCommentCount
      viewCount
      pinned
      isFavorite
      solutionTags {
        name
        slug
      }
      post {
        id
        status
        voteStatus
        voteCount
        creationDate
        isHidden
        author {
          username
          isActive
          nameColor
          activeBadge {
            displayName
            icon
          }
          profile {
            userAvatar
            reputation
          }
        }
      }
      searchMeta {
        content
        contentType
        commentAuthor {
          username
        }
        replyAuthor {
          username
        }
        highlights
      }
    }
  }
}
```

> "variables":{"query":"","languageTags":["python3"],"topicTags":[],"questionSlug":"remove-k-digits","skip":0,"first":15,"orderBy":"most_votes"},"operationName":"communitySolutions"

## Get solution details

```graphql
query communitySolution($topicId: Int!) {
  topic(id: $topicId) {
    id
    viewCount
    topLevelCommentCount
    subscribed
    title
    pinned
    solutionTags {
      name
      slug
    }
    hideFromTrending
    commentCount
    isFavorite
    post {
      id
      voteCount
      voteStatus
      content
      updationDate
      creationDate
      status
      isHidden
      author {
        isDiscussAdmin
        isDiscussStaff
        username
        nameColor
        activeBadge {
          displayName
          icon
        }
        profile {
          userAvatar
          reputation
        }
        isActive
      }
      authorIsModerator
      isOwnPost
    }
  }
}
```

## Get solution author

```graphql
 query solutionArticleInformation($topicId: Int!) {
  topic(id: $topicId) {
    title
    post {
      author {
        username
      }
    }
  }
}
```
