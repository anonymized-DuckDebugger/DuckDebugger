#!/usr/bin/env python3
import re

def parse_solution_comment(lineNumber, commentStr):
    """
    Example:
    commentStr='comment text @@TAGS tag1 tag2 @@NUMS 1 2 5-9 @@KWORDS kw1 kw2 kw3'

    where:
    @@TAGS    -- define tags to categorize the text by        --> [tag1, tag2]
    @@NUMS    -- other line numbers the comment applies to    --> [1,2,5,6,7,8,9]
    @@KWORDS  -- keywords to assess solutio by (pending TODO) --> kw1 kw2 kw3

    IMPORTANT:
        1. Values for each tag are SPACE-separated. No commas nothing else.
        2. Algorithm assumes all tags are optional and don't have a set order.
    """
    # Split the string by the markers
    parts = re.split(r'(@@TAGS|@@NUMS|@@KWORDS)', commentStr)
    # Initialize the dictionary with default values
    result = {"comment": "",
              "tags"   : [],
              "nums"   : {lineNumber},
              "kwords" : []
             }

    # Process each part
    i = 0
    while i < len(parts):
        
        part = parts[i].strip()
        tag  = parts[i-1].strip()
        
        if i == 0: # The comment is always the first part
            tag='comment'
            result["comment"] = part

        if tag == "@@TAGS":
            result["tags"] = part.split()
            
        elif tag == "@@NUMS":
            nums = part.split()
            for num in nums:
                
                # relative notation i.e +3 -1
                if  num.startswith("+") or num.startswith("-"):
                    result["nums"].add(int(lineNumber)+int(num))
                
                # range notation i.e. 5-7
                elif '-' in num:
                    start, end = map(int, num.split('-'))
                    result["nums"].update(range(start, end + 1))
                
                # bare number
                else:
                    result["nums"].add(int(num))
        elif tag == "@@KWORDS":
            result["kwords"] = part.split()
        
        i += 2

    return result

def expand_solution(solutionInline):
        # return stmt is the same as:
    # for k, v in solutionInline.items():
    #     solutionInline[k] = parse_solution_comment(k, v)
        # OR
    # {k: (lambda x: parse_solution_comment(k, x))(v) for k, v in solutionInline.items()}

  # EXPANDED SOLUTION FORMAT:
  #   dict with this structure
  # {42: {'comment': 'comment text', 
  #       'kwords':  ['kw1', 'kw2', 'kw3'],
  #       'nums':    {42, 1, 2, 5, 6, 7, 8, 9},
  #       'tags':    ['tag1', 'tag2']
  #      },
  #  69: {..}  <-- keys are line nums.
  # }

    return {k: parse_solution_comment(k,v) for k, v in solutionInline.items()}

def tags_minOne(tag, comments):
    if type(comments)==dict:
        comments = comments.values()
    return any([tag in c for c in comments])

def tags_all(tag, comments):
    if type(comments)==dict:
        comments = comments.values()
    return all([tag in c for c in comments])

def lineNumbersUnion(expandedSolution):
    return set().union(*(entry['nums'] for entry in expandedSolution.values()))

def diffAnswers(userAnswer, intendedAnswer, threshold, method='naive'):
    """
    userAnser: {lineNum: '<text comment>'}
    intendedAnswer: {lineNum: <solution_comment>} <-- see 'parse_solution_comment' for inner structure

    possible methods:
        naive
            Checks if the user commented anything on the expected lines.
            Content does not matter.
        naive-multiple-correct
            Checks if the user commented anything on the expected lines.
            Content still does not matter.
        keywords
            Like naive-multiple-correct PLUS checking keywords. #TODO - hmm? 
            Non-matching keywords on correct lines still give 0.49 "points" #TODO - up for debate?
            Content matters.
    """

    # TODO: comments in userAnswer on lines that are not part of intendedAnswer DEDUCT POINTS

    # if there's no tags present, fall back to 'naive' evaluation -- this way old answers won't break
    if not tags_minOne('@@', intendedAnswer):
        method = 'naive'
    # otherwise we expand the answer
    else:
        intendedAnswer_Expanded = expand_solution(intendedAnswer)
        # time for sanity checks and cascade fallbacks
        if method == 'keywords':
            if not tags_all('@@NUMS', intendedAnswer):
                method = 'naive-multiple-correct' # fall back again
        if method == 'naive-multiple-correct':
            if not tags_minOne('@@NUMS', intendedAnswer):
                method = 'naive' # fall back again

    
    
    # line numbers on which the user commented.            
    lineNums_user = set([int(key) for key, value in userAnswer.items() if value])

    if method == 'naive': #just check if the user left comments where we expected
        lineNums_intended = set(intendedAnswer.keys())
        findingPercentage = 1 - float(len(lineNums_intended - lineNums_user)) / float(len(lineNums_intended))

    elif method == 'naive-multiple-correct': # One intended_solution entry can have multiple lines it applies to.
        # TODO: untested
        # User:
            # 12, 23       ---> len(lineNums_user)              = 2
        # Expected:
            # 12: 15-17    union: {12,15,16,17,20,23,24,32}     
            # 20: 23-24 
            # 32: 32       ---> len(lineNums_intended)          = 3
            #------------- ---> len(lineNums_intended_expanded) = 8
        lineNums_intended = set(intendedAnswer.keys())
        lineNums_intended_multiple = lineNumbersUnion(intendedAnswer_Expanded)
        userAnswers_onExpectedLines = {n for n in lineNums_user if n in lineNums_intended_multiple} # alt: {k: d1[k] for k in d1 if k in d2} where d1=user, d2=expandedIntended

        findingPercentage = float(len(userAnswers_onExpectedLines)) / float(len(lineNums_intended))
        
    elif method == 'keywords':
        # TODO: untested
        lineNums_intended = set(intendedAnswer.keys())
        lineNums_intended_multiple = lineNumbersUnion(intendedAnswer_Expanded)
        userAnswers_onExpectedLines = {n for n in lineNums_user if n in lineNums_intended_multiple}
        
        # Notation:
        #   user: d1{k1:v1}
        #   answ: d2{k2:{nums:[..], kwords:[..]}}
        # Check for k1,v1 in d1.items() :
        # for which key k2 of d2 is k1 found among nums of d2,
        # and how many keywords from d2[k2]['kwords'] are found in v1.
        #
        # result stored in r:{lineNum: keywordCount}  only if count(foundKeywords)>0
        userAnswers_onExpectedLines_keywordCount = {}
        for line_user, comment_user in userAnswers_onExpectedLines.items():
            for _, comment_sol in intendedAnswer_Expanded.items():
                if line_user in comment_sol['nums']:
                    keyword_count = sum(keyword in comment_user for keyword in comment_sol['keywords'])
                    if keyword_count:
                        userAnswers_onExpectedLines_keywordCount[line_user] = {keyword_count}

        findingPercentage = float(len(userAnswers_onExpectedLines_keywordCount)) / float(len(lineNums_intended))
    
    
    else:
        print("ain't no way.")
        
        lineNums_intended = None
        findingPercentage = None

    return lineNums_user, lineNums_intended, findingPercentage




