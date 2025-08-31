#!/usr/bin/env python3
import random
import yaml
import json
import sys
import os

currentScriptPath = os.path.dirname(os.path.abspath(__file__))


with open(f'{currentScriptPath}/lang2sast.yaml', 'r') as json_file:
    lang2sast = yaml.safe_load(json_file)

with open(f'{currentScriptPath}/ext2lang.json', 'r') as json_file:
    # Dict of extension:language i.e. ".py":"python"
    ext2lang = json.load(json_file)    

def getExtension(filename):
    return filename.split(".")[-1].lower()

def getLang(filename):
    filenameExt = getExtension(filename)
    language = ext2lang.get(filenameExt, "unknown")
    return language

def substringFromRight(inputString, pattern, includePattern=True):
    index = inputString.find(pattern)
    if index == -1: # pattern not found
        result = ''
    else:
        if not includePattern:
            index += len(pattern)
        result = inputString[index:]
    return result

def getJustFilename(fileNamePlusPath):
    return os.path.basename(fileNamePlusPath)

adjectives = ["quick", "lazy", "sleepy", "noisy", "hungry", "happy", "sad", "angry", "tiny", "huge", "eager", "brave", "shy", "bold", "gentle", "fierce", "calm", "playful", "clever", "silly"]
animals    = ["lion", "tiger", "bear", "wolf", "fox", "elephant", "giraffe", "zebra", "rhino", "hippo","kangaroo", "koala", "panda", "sloth", "leopard", "cheetah", "raccoon", "squirrel", "owl", "eagle"]

def get_random_name():
    adjective = random.choice(adjectives)
    animal = random.choice(animals)
    return f"{adjective} {animal}"

#  ----------[ FILES LOADING ]-----------  #
try:
    with open(f'{currentScriptPath}/../exercises.yaml', 'r') as f:
        exercises = yaml.safe_load(f)
except Exception as e:
    print(f"Error: {e}")

def getFileContents(filename):
    with open(filename, 'r') as f:
        try:
            contents = f.readlines()
        except:
            contents = ""
            print(f"Error: {e}")
        return contents
  

def find_exercise_folder(uuid, base_path=f"{os.path.abspath(currentScriptPath+'/../exercises')}"):
    """
    Find the path of the subdirectory in /exercises that ends with the given UUID.

    :param uuid: UUID of the exercise.
    :param base_path: Base directory where exercises are stored.
    :return: Path to the exercise directory or None if not found.
    """
    if not os.path.exists(base_path):
        print(f"Base path {base_path} does not exist.")
        return None

    for dir_name in os.listdir(base_path):
        dir_path = os.path.join(base_path, dir_name)
        if os.path.isdir(dir_path) and dir_name.endswith(f"__{uuid}"): # DOUBLE UNDERLINE!
            return dir_path                      

    print(f"[utils] No directory found for UUID {uuid}")
    return None

def get_exercise_displayName(exerciseFolder):
    try:
        name = exerciseFolder.split("__")[-2].split('/')[-1]
    except Exception as e:
        print(f"[utils] e")
        name = get_random_name()
    finally:
        return name
    

# 'exercises.yaml' evolved a bit:
# --NEW--
# e78749961806:
#   source: python_flask.py
# --OLD--
# e78749961806: (old)
#   file_css: static/style.py.css
#   file_source: python_flask.py
#   language: python
#   name: Flaskful of bugs
#   type: review

# -- legacy code salvation in 3 lines:
for k, v in exercises.items():
    exercises[k]['name']     = get_exercise_displayName(find_exercise_folder(uuid=k))
    exercises[k]['language'] = getLang(v['source'])
    
#  ----------[ QUIZ UTILS ]-----------  #

def add_question_indices_and_count(quiz_data):
    # Iterate over each quiz in the top-level dictionary
    for quiz_key, quiz in quiz_data.items():
        # Add total number of questions after the "flag" key
        num_questions = len(quiz.get('questions', []))
        if num_questions:
            quiz['total_questions'] = num_questions
        
        # Update each question with an index after the "id" key
        for index, question in enumerate(quiz['questions'], start=1):
            question['question_index'] = index

try:
    with open(f'{currentScriptPath}/../quizzes.yaml', 'r') as f:
        quizzes = yaml.safe_load(f)
        add_question_indices_and_count(quizzes)
except Exception as e:
    print(f"Error: {e}")
        
def quiz_UUID2quiz(quizUUID):
    quiz = quizzes.get(quizUUID, None)
    if quiz == None:
        raise ValueError(f"No question found with ID: {quizUUID}")
    return quiz

def quiz_UUID2question(questionUUID, quiz):
    question = next((q for q in quiz.get('questions', []) if q['id'] == questionUUID), None)

    if question == None:
        raise ValueError(f"No question found with ID: {questionUUID} -- quiz: {quiz['id']} )")
    return question

def quiz_get_answers_TF(question):
    answers_TF = {key: value['correct'] for key, value in question['answers'].items()}
    return answers_TF

def quiz_assess_user_answers(answers_TF, user_answers):
    answers_T = [key for key, value in answers_TF.items() if value]
    return sorted(user_answers) == sorted(answers_T)

# def generate_scorecard(interactions, reportType, uuidCookie = None):
#     _result = None

#     if reportType == "cwe-1000":
#         # do analysis
#         _result = analysis_result
#     elif reportType == "cwe-1400":
#         # do analysis
#         _result = analysis_result

#     result = json.loads(_result)

#     return result

#  ----------[ MESSAGES ]-----------  #
#  ----------[ FOR THE  ]-----------  #
#  ----------[   USER   ]-----------  #
def random_encouragement():
    encouragements = [
        "Keep pushing forward!",
        "You're doing great!",
        "Stay positive and strong!",
        "Keep up the good work!",
        "Believe in yourself!",
        "Never give up!",
        "You can do it!",
        "Keep on shining!",
        "Every effort counts!",
        "Success is just around the corner!"
    ]
    return random.choice(encouragements)

def random_mockery():
    mockeries = [
        "Is your keyboard jammed, or is that your best attempt?",
        "Oops! Try again, but with a little less error this time.",
        "I see you're practicing... to lose!",
        "If at first you don't succeed, redefine success.",
        "That effort was... adorable.",
        "Are you a software update? Because I can't wait to ignore you.",
        "You must be a keyboard warrior, because that was a real 'strong' attempt.",
        "Wow, you really set the bar low for everyone else.",
        "I'd agree with you, but then we'd both be wrong.",
        "Keep rolling your eyes. Maybe you'll find a brain back there."
    ]
    return random.choice(mockeries)    


#  ----------[ DEAD CODE ]-----------  #

def render_solution(filename):
    solutionHtml = ""
    try:
        with open(filename, 'r') as f:
            try:
                solution = yaml.safe_load(f)
            except yaml.YAMLError as e:
                print(f"[utils.render_solution] -- '{filename}' is a malformed yaml. -- {e}")
            for k, v in solution.items():
                solutionHtml += f"<p><b>{k}:</b> {v}</p>\n"
    except FileNotFoundError as e:
        solutionHtml = "<i>Solution not yet defined</i><br>a.k.a.<br>The dev slacked off."
    finally:
        return solutionHtml
    


# ------------------------------ #
def main():
    surprise = """
                                                                                                              
                        ████████████████████                    
                    ████▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▓▓██                
                  ██▒▒▒▒░░░░░░░░░░░░░░░░░░░░░░░░████            
                ██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░██          
                ██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░▒▒▓▓        
              ██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░██        
              ██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░██      
              ██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░██      
            ██▒▒░░░░██████░░░░░░░░░░░░░░░░██████░░░░░░░░██      
            ██░░░░░░  ▒▒██░░░░░░░░░░░░░░░░  ▒▒██░░░░░░░░██      
            ██░░░░░░▓▓████░░░░░░░░░░░░░░░░██████░░░░░░░░██      
            ██░░░░░░▒▒▒▒▒▒░░░░░░████░░░░░░▒▒▒▒▒▒░░░░░░░░██      
            ██░░░░░░░░░░░░░░░░██    ██░░░░░░░░░░░░░░░░░░██      
            ██░░░░░░░░░░░░░░░░██    ██░░░░░░░░░░░░░░░░░░██      
            ██░░░░░░░░░░░░░░▓▓░░    ██░░░░░░░░░░░░░░░░░░██      
            ██░░░░░░░░░░░░██          ██░░░░░░░░░░░░░░██        
            ██░░░░░░░░████            ██░░░░░░░░░░░░░░██        
              ██░░████                  ██░░░░░░░░░░██          
              ████                      ██░░░░░░░░░░██          
          ████            ██    ██        ██░░░░░░██            
      ██▓▓░░░░            ██    ██        ░░▓▓░░▓▓              
  ████░░░░                ░░    ░░          ░░██                
██                                              ██              
██                 it is what it is            ░░▓▓            
  ██▒▒▓▓                                      ▓▓▓▓              
        ██████████                      ██████                  
                  ██████████████████████░░██                    
                ▓▓▒▒▒▒▒▒░░░░░░░░░░░░▒▒▒▒░░██                    
              ██▒▒░░░░░░░░░░░░░░░░░░░░░░░░██                    
              ██░░░░░░░░░░░░░░░░░░░░░░░░░░██            ████    
            ▓▓▒▒░░░░░░░░░░░░░░░░░░░░░░░░░░▒▒▓▓        ██▒▒▒▒▓▓  
            ██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░██      ██░░░░░░██  
          ██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░██      ██░░░░░░██  
          ██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░▒▒▓▓  ▓▓▒▒░░░░░░██  
          ██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░██  ██░░░░░░░░░░██
        ██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░▒▒██▒▒░░░░░░░░░░██
        ██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░██░░░░░░░░░░░░██
        ██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░▒▒██░░░░░░░░░░██
      ██▒▒░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░██░░░░░░░░░░██
      ██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░██
      ██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░██
      ██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░██
      ██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░██  
        ██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░██  
        ██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░██    
          ██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░██      
            ████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  ░░████        
              ░░██████▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓██            

"""
    print(surprise)

if __name__ == "__main__":
    main()    