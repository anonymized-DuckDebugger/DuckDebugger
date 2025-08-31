# Endpoints

This document goes over the available endpoints. Documentation is currently incomplete

**How to contribute here:**
- Update this document whenever changes to the API occur.
- Open issues (labeled *endpoints*) when:
    1. Data fields should be removed
    2. Data fields are wanted but not present
    3. s 
- Close issues when the fix is pushed to the repo **after being merged to `main` or `deployment`**. Branching strategy also currently TBD.

---

## /start

**Methods:** GET
**Purpose:** Retrieves info on available challenges.

### Input format:
```js
// none, you just /GET it.
```
### Output format:
```js
{
  "exercises": {
    "1a0aa4440bbf": {
      "language": "csharp",
      "name": "Ghost in the..Entity?",
      "source": "csharp_xxe.cs"
    },
    // ...
// ...
  },
  "quizzes": {
    "UUID_QUIZ": {
      "language": "CSharp",
      "name": "CSharp Owasp Top10",
    }
  }
}
```

---
