# Contribution Guide: Quizzes

If you want to add some quiz-type challenges, the DuckDebugger has built-in support for that.  
Questions can include images.  
Answers can be single/multiple-choice 

See `CSharp Owasp Top10` as an example quiz. Accessible at [http://127.0.0.1:5000/quiz/6d57d7573caa/740e5aebfe1d](http://127.0.0.1:5000/quiz/6d57d7573caa/740e5aebfe1d).

See `barebones_js/quizzes.yaml` to see how the quiz is structured.

Associated helper scripts in `barebones_js/utils`:
- `dev_patchQuizIDs.pys`

Answers are stored in the `quiz_answer` table in `reviews.db`