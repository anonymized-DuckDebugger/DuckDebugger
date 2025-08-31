#!/usr/bin/env python3
from flask import Flask
from flask import flash
from flask import request
from flask import url_for
from flask import jsonify
from flask import redirect
from flask import render_template
from flask import send_from_directory

from flask_sqlalchemy import SQLAlchemy
from urllib.parse     import urlparse
from datetime         import datetime
from flask_cors       import CORS

import sqlite3
import random
import json
import yaml
import re
import os
import pandas as pd

# own libs
from utils import utils
exercises = utils.exercises

from solution_related import parse_solution_comment # <-- everything to do with answers
from solution_related import lineNumbersUnion
from solution_related import expand_solution
from solution_related import diffAnswers     
from solution_related import tags_minOne
from solution_related import tags_all

from utils import scorecard
from pprint import pprint

# This function is used to minimize and sanitize some the jsons sent to the frontend.
# #TODO - move to utils?
def removeKeysFromDict(d, keys_to_remove=['flag', 'disabled','questions']):
    """
    Recursively remove keys from the dictionary.

    :param d: The dictionary from which to remove keys.
    :param keys_to_remove: The list of keys to remove.
    :return: The dictionary with specified keys removed.
    """
    if isinstance(d, dict):
        return {k: removeKeysFromDict(v, keys_to_remove) 
                for k, v in d.items() if k not in keys_to_remove}
    elif isinstance(d, list):
        return [removeKeysFromDict(v, keys_to_remove) for v in d]
    else:
        return d

# when deployed, run with '<FlagYouWantTurnedFalse>=1 ./mockserver'
BACKENDONLY = True if     os.getenv('BACKENDONLY')        else False
DEPLOYMENT  = True if     os.getenv('DD_DEPLOY')          else False
DEVELOPMENT = False# True if not os.getenv('ITZSHOWTIME')        else False
DEBUG       = False# if not os.getenv('ITZSHOWTIMEFORREAL') else False

print(f'>>> [STARTED {__file__.split("/")[-1]}]<<<\n {BACKENDONLY=} {DEVELOPMENT=} {DEBUG=}\n\n\n{"-"*80}')

if DEVELOPMENT: # we're 
    import subprocess
    import shutil

if DEBUG:
    import code
    import IPython
    def break_interactive(message=None):
        if message:
            print(f"\n\n{'>'*10}[{message}]{'<'*10}\n")
        code.interact(local=locals())

currentScriptPath = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__)
if not DEPLOYMENT:
    CORS(app)
else:
    CORS(app, resources={r"/*": {"origins": "https://review/.redacted-domain.tld"}})

## --- DB ---
# Store db in same folder as 
db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), '', 'reviews.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
db = SQLAlchemy(app)

# Define the database models
class Review(db.Model):
    id           = db.Column(db.Integer, primary_key=True, autoincrement=True)
    date         = db.Column(db.Text, nullable=False)
    uuidCookie   = db.Column(db.Text, nullable=False)
    exerciseUUID = db.Column(db.Text, nullable=False)
    interactType = db.Column(db.Text)
    interactLine = db.Column(db.Text)
    interactText = db.Column(db.Text)
    interactTime = db.Column(db.Integer)
    solved       = db.Column(db.Boolean, default=False)
    sol_user     = db.Column(db.Text)
class Exercise(db.Model):
    exerciseUUID  = db.Column(db.Text, primary_key=True)
    solution_str  = db.Column(db.Text, nullable=False)

class Solution(db.Model):
    id             = db.Column(db.Integer, primary_key=True, autoincrement=True)
    exerciseUUID   = db.Column(db.Text, db.ForeignKey('exercise.exerciseUUID'), nullable=False)
    line_number    = db.Column(db.Integer, nullable=False)
    comment        = db.Column(db.Text, nullable=False)
    tags           = db.Column(db.Text)
    nums           = db.Column(db.Text)
    kwords         = db.Column(db.Text)

class QuizAnswer(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    userID = db.Column(db.Text, nullable=False)
    quizID = db.Column(db.Text, nullable=False)
    questionID = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.Integer, nullable=False)
    answer = db.Column(db.Text, nullable=False)

# Define the Survey Responses model
class Response(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    survey_id = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Text, nullable=False)
    question_id = db.Column(db.String(50), nullable=False)
    sub_question_id = db.Column(db.String(50), nullable=True)
    answer = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.now())    


with app.app_context():
    # Always refresh static tables
    try:
        Exercise.__table__.drop(db.engine)
        Solution.__table__.drop(db.engine)
    except:
        pass
    # Create the database tables
    db.create_all()
    # And populate them.
    # #TODO - issue#13: Also update stuff in the /dev/ endpoints as needed.
    try:
        for exerciseUUID, exercise in exercises.items():
                
                exerciseFolder = utils.find_exercise_folder(exerciseUUID)
                solutionFile   = exercise['source']
                solutionFile   = f'{exerciseFolder}/{solutionFile}.solution'
                try:
                    with open(solutionFile, 'r') as file:
                        solution_str = file.read()
                        solution = yaml.safe_load(solution_str)
                except FileNotFoundError as e:
                    print(f"[INFO] -- No solution for {exerciseUUID}")
                    solution = {1: "No solution here yet.", 2: "a.k.a", 3: "the dev slacked off."}
                    solution_str = "MISSING."
                
                # print(f"[EXE]{exerciseUUID}")
                
                new_object = Exercise(exerciseUUID=exerciseUUID,
                                      solution_str=solution_str
                                     )
                db.session.add(new_object)
                
                expandedSolution=expand_solution(solution)
                for lineNumber, solutionComment_asDict in expandedSolution.items():
                    new_object = Solution(exerciseUUID = exerciseUUID,
                                          line_number  = lineNumber,
                                          comment      = solutionComment_asDict.get('comment', None),
                                          tags         = str(solutionComment_asDict.get('tags'   , None)),
                                          nums         = str(solutionComment_asDict.get('nums'   , None)),
                                          kwords       = str(solutionComment_asDict.get('kwords' , None)) 
                                         )
                    db.session.add(new_object)
                # print(f"[SOL]{exerciseUUID}")
    except Exception as e:
        db.session.rollback()
        # Handle any exceptions that may occur
        print("Error:", e)
    finally:
        db.session.commit()
        db.session.close()
        print(f"[DB] Initialisation ok.")
## --- /DB ---

@app.route('/static/<path:path>')
def send_js(path):
    return send_from_directory('static', path)

@app.route('/', methods=['GET'])
def root_page():
    # deprecated the base URL, we're redirecting to /start
    return redirect(url_for('landing_page'))

#  ----------[ QUIZ STUFF ]-----------  # TODO: move this into some quizzes.py 
@app.route('/quiz/<quizUUID>/', defaults={'questionUUID': None}, methods=['GET', 'POST'])
@app.route('/quiz/<quizUUID>/<questionUUID>', methods=['GET', 'POST'])
def quiz(quizUUID, questionUUID):
    # Find the quiz
    try:
        quiz = utils.quiz_UUID2quiz(quizUUID)
        store_answers = quiz.get("store_answers", False)
        #print(f"QUIZ\n\n{quiz}\n")
    except:
        return jsonify({"error": "Quiz not found"}), 404

    # If questionUUID is None, redirect to the first question
    if questionUUID is None:
        first_question_id = quiz['questions'][0]['id']
        return redirect(url_for('quiz', quizUUID=quizUUID, questionUUID=first_question_id))

    # Find the question
    try:
        question = utils.quiz_UUID2question(questionUUID, quiz)
        if quiz.get("total_questions", None) and question.get("question_index", None):
            question["relative_index"] = f"[{question.get('question_index', 0)}/{quiz.get('total_questions', None)}]. "
        #print(f"QUESTION\n\n{question}")
    except:
        return jsonify({"error": "Question not found"}), 404

    if request.method == 'POST':

        # Expecting a list of answers
        selected_answers = request.json.get('answers', None)
       
        # we can choose to store an individual question answer
        store_answer = question.get('store_answer', False)

        # (store_answers is a quiz-wide setting, overrides store_answer)
        # (store_answer  is a per-question setting, gets overriden)
        if store_answers or store_answer:
            userID = request.cookies.get('uuid')
            timestamp = int(datetime.now().timestamp())
            quiz_answer = QuizAnswer(
                userID=userID,
                quizID=quizUUID,
                questionID=questionUUID,
                timestamp=timestamp,
                answer=json.dumps(selected_answers)
            )
            #print(f"\n\n {'!'*20}\n.storing {quiz_answer}\n\n")
            db.session.add(quiz_answer)
            db.session.commit()

        
        # Answer structure
        response_POST = {"is_correct": False, # determines overall answer correctfulness.
                         "info": {},          # Feedback on answers. info={<ans_key>:{true_answer: <T/F>, info: <feedback>}}
                         "message": ""        # Overall feedback message.
                         # next_question_uuid <-- optional field for navigating the quiz
                         # "quiz_done"        <-- optional, is True after answering last question
                        }
        
        any_answer = question.get('any_answer', False)
        # key to turn question into survey: any and all answers are correct
        # and skip the evaluation of the answer below
        if any_answer:
            #print("Any Answer!")
            response_POST["is_correct"] = True
            message = "Answer accepted."
            # correct answer = next question in quiz unlocked (if exists)
            next_question_index = quiz['questions'].index(question) + 1
            if next_question_index < len(quiz['questions']):
                next_question_uuid = quiz['questions'][next_question_index]['id']
                response_POST['next_question_uuid'] = next_question_uuid
                message += f" Onto the next question."
            elif next_question_index == len(quiz['questions']):
                message += f" Flag: {quiz['flag']}"
                response_POST['quiz_done'] = True
            response_POST['message'] = message
            #print(response_POST)
            return jsonify(response_POST), 200
        
        # No feedback if user: 1. checks all answers or 2. checks NO answers
        elif len(selected_answers) > 0 \
              and \
             len(selected_answers) < len(list(question['answers'].keys())):
            
            intended_answers = utils.quiz_get_answers_TF(question)
            is_correct = utils.quiz_assess_user_answers(intended_answers, selected_answers)
            response_POST['is_correct'] = is_correct

            # now we build the 'info' field
            if is_correct:
                # When right: give feedback on ALL answer choices
                message = "Well done!"
                info = { key: {"true_answer": question['answers'][key]['correct'],
                              "info": f"<b>{'✓' if question['answers'][key]['correct'] else '✗'}</b> {question['answers'][key]['info']}"
                             } for key in question['answers'].keys() }
                
                # correct answer = next question in quiz unlocked (if exists)
                next_question_index = quiz['questions'].index(question) + 1
                if next_question_index < len(quiz['questions']):
                    next_question_uuid = quiz['questions'][next_question_index]['id']
                    response_POST['next_question_uuid'] = next_question_uuid
                    message += f" Onto the next question."
                elif next_question_index == len(quiz['questions']):
                    message += f" Flag: {quiz['flag']}"
                    response_POST['quiz_done'] = True
            else:
                # When wrong: only give feedback on the user-ticked answers
                info = {key: {"true_answer": question['answers'][key]['correct'],
                              "info": f"<b>{'✓' if question['answers'][key]['correct'] else '✗'}</b> {question['answers'][key]['info']}"
                             } for key in selected_answers }
                message = f"Try again. {utils.random_encouragement()}"
            
            response_POST['info']    = info
            response_POST['message'] = message
    
            return jsonify(response_POST), 200
        
        else: # in case user screwed around: none/all answers provided
            response_POST['message'] = utils.random_mockery()
            return jsonify(response_POST), 200

    #  GET request, render the question template with the initial data
    if not BACKENDONLY:
        return render_template('quiz.html', quiz_uuid=quizUUID, question_uuid=questionUUID, question=question)
    else:
        return jsonify({'quiz_uuid':quizUUID, 'question_uuid':questionUUID, 'question':question}), 200

@app.route('/api/get_exercises', methods=['GET'])
def get_exercises():
    type_filter     = request.args.get('type')
    language_filter = request.args.get('language')

    if type_filter == 'all':
        type_filter = None
    if language_filter == 'all':
        language_filter = None
    
    filtered_exercises = {k: v for k, v in exercises.items() 
                          if (not v.get('disabled', False) and 
                              (not type_filter or v.get('type') == type_filter) and 
                              (not language_filter or v.get('language') == language_filter))}
    
    filtered_quizzes   = {k: v for k, v in utils.quizzes.items() 
                          if (not v.get('disabled', False) and 
                              (not type_filter or v.get('type') == type_filter) and 
                              (not language_filter or v.get('language', None) in [language_filter, None]))}
    

    filtered_exercises = removeKeysFromDict(filtered_exercises)
    filtered_quizzes   = removeKeysFromDict(filtered_quizzes)
    return jsonify({
        # Note: key has to match the enpdoints
        #       of that exercis type
        'review': filtered_exercises,
        'quiz'  : filtered_quizzes, 
    })

@app.route('/start', methods=['GET'])
def landing_page():
    if not BACKENDONLY:
        return render_template('start.html', exercises=utils.exercises, quizzes=utils.quizzes, utils=utils)
    else:
        _exercises = removeKeysFromDict(exercises)
        quizzes   = removeKeysFromDict(utils.quizzes)
        return jsonify({'exercises':_exercises, 'quizzes':quizzes}), 200

@app.route('/review/<exerciseUUID>', methods=['GET'])
def exercise(exerciseUUID):
    exercise            = exercises[exerciseUUID]
    exerciseFolder      = utils.find_exercise_folder(exerciseUUID)
    if not exerciseFolder: # If someone tries forced browsing, we'll teach them not to :)
        print(f"[main-app][ERROR] No corresponding exercise folder.")
        # TODO: look into message flashing
        return redirect(url_for('start'))
    print(f"{exercise=}")
    exerciseDisplayName = utils.get_exercise_displayName(exerciseFolder)
    exerciseExtension   = utils.getExtension(exercise['source'])
    exerciseCss         = f"static/style.{exerciseExtension}.css"
    
    print(f"\n\n\n\n{'-'*80}\n{exercise}\n{'-'*80}\n\n\n")

    # SAST files start with 'sast_'
    files = [f for f in os.listdir(exerciseFolder) if f.startswith('sast')]
    toolFindings = []
    for file in files:
        # file is <sast.tool.html> i.e. sast.bandit.html
        tool = file.split('.')[-2]
        try:
            with open(f'{exerciseFolder}/{file}', 'r') as f:
                content = f.read()
            toolFindings.append({'tool': tool, 'content': content})
        except Exception as e:
            print(f"[MAIN-APP][ERROR] {e}\n" + \
                  f" >>>>>>>>>>>>>>>> Missing '{exerciseFolder}/{file}'")
            toolFindings.append({'tool': tool, 'content': ''})

    rendered_code = utils.getFileContents(f"{exerciseFolder}/{exercise['source']}.rendered")
    if not BACKENDONLY:
        return render_template('reviewPage.html',
                                exerciseUUID  = exerciseUUID,
                                cssFile       = exerciseCss,
                                displayName   = exerciseDisplayName,
                                rendered_code = rendered_code,
                                toolFindings  = toolFindings
                            )
    else:
        return jsonify({    'exerciseUUID'   : exerciseUUID,
                            'cssFile'        : exerciseCss,
                            'displayName'    : exerciseDisplayName,
                            'rendered_code'  : rendered_code,
                            'toolFindings'   : toolFindings
                        }), 200
    
@app.route('/review_api', methods=['POST'])
def submit_review():
    try:
        # Get the JSON data from the POST request
        data = request.get_json()
        print(data)
        # Extract individual fields from the data
        uuidCookie    = data.get('uuidCookie', None)
        interactions  = data.get('interactions', None)
        solution_user = data.get('user_solution', None) # This word switcheroo killed me twice already :)
        exerciseUUID  = data.get('exerciseUUID', None)
        
        if not uuidCookie or not exerciseUUID or not interactions:
            return jsonify({'message': 'Missing required data'}), 400
        if not solution_user or not sum(len(v) for v in solution_user.values()):
                return jsonify({'message': 'Comment something first lol.'}), 400

        # Print the received data to stdout
        print(f"\n{'>'*10}[ Received POST request data: ]{'<'*10}")
        #print(f"{uuidCookie=}, {exerciseUUID=}\n---Interactions:")
        #pprint(interactions)
        print(f"\n---User Solution:")
        pprint(solution_user)

        exerciseFolder = utils.find_exercise_folder(exerciseUUID)
        solutionFile   = exercises[exerciseUUID]['source']
        solutionFile   = f'{exerciseFolder}/{solutionFile}.solution'

        try:
            with open(solutionFile, 'r') as file:
                solution_yaml = file.read()
            solution_intended = yaml.safe_load(solution_yaml)
            print(f"1. {solution_intended}")
        except FileNotFoundError as e:
            solution_intended = {1: "No solution here yet.", 2: "a.k.a", 3: "the dev slacked off."}
        finally:
            # Percentage of findings that users need to find
            # Customizable for more difficult / easier challenges
            threshold = exercises[exerciseUUID].get('threshold', None)
            if not threshold:
                threshold = 0.5 # powered by Science(TM).

            sol_user, sol_intended, findingPercentage = diffAnswers(solution_user,
                                                                    solution_intended,
                                                                    threshold,
                                                                    method='naive-multiple-correct'
                                                                    )

            
            if findingPercentage >= threshold:
                solved = True
                try:
                    flag = exercises[exerciseUUID]["flag"]
                except:
                    flag = "[Error.. Ask the trainers]"
                message = f"Good job! {findingPercentage*100:.2f}% Find Rate - FLAG: <b>{flag}</b>"
            else:
                solved = False
                message = f"{utils.random_mockery()} | {findingPercentage*100:.2f}% Find Rate |"
                # still return what the user found. Mad typecasting required.
                solution_intended = {key: solution_intended[int(key)]
                                     for key in solution_user.keys() if
                                            int(key) in solution_intended.keys()
                                                and
                                            solution_user[str(key)].strip() # discard space/empty strings
                                    }
                print(f"2. {solution_intended}")
            
            
        
        for interaction in interactions:
            new_object = Review(date=datetime.now().strftime("%Y%m%d"),
                                uuidCookie=uuidCookie,
                                exerciseUUID=exerciseUUID,
                                interactType=interaction.get("type", None),
                                interactLine=interaction.get("lineNumber", None),
                                interactText=interaction.get("updatedCommentText", None),
                                interactTime=interaction.get("timestamp", None),
                                solved=solved,
                                sol_user=json.dumps(solution_user) # save full solution now
                                )

            db.session.add(new_object)
        db.session.commit()
        
        # remove fields from solution before displaying it to the user.
        print(f"3. below")
        pprint(solution_intended)
        for k,v in solution_intended.items():
            pprint(parse_solution_comment(k, v))
            solution_intended[k]=v.split('@@')[0].strip()
        
        return jsonify({'message': f'{message}', 'solution': solution_intended, 'solved': solved}), 201  # 201 indicates "Created" status code
    
    except Exception as e:
        db.session.rollback()
        # Handle any exceptions that may occur
        print("Error:", e)
        return jsonify({'Error': e}), 500
    finally:
        db.session.close()

@app.route('/report/<exerciseUUID>', methods=['GET', 'POST'])
def report_problem(exerciseUUID):
    if request.method == 'POST':
        report_content = request.form['problemReport']
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        directory = "reports"
        filename = f"{exerciseUUID}_{timestamp}.txt"

        # Ensure the 'reports' directory exists
        if not os.path.exists(directory):
            os.makedirs(directory)

        # Write the report content to a file
        file_path = os.path.join(directory, filename)
        with open(file_path, 'w') as file:
            file.write(report_content)

        return f"Report saved. Thank you for helping to make the platform better!"
    return render_template('report.html', exerciseUUID=exerciseUUID)

@app.route('/scorecard/test_api', methods=['GET'])
def get_cookie_interactions():
    # Retrieve the value of 'uuidCookie' cookie
    uuidCookie = request.cookies.get('uuidCookie')

    if uuidCookie:
        interactions = scorecard.get_uuidCookie_interactions(uuidCookie).to_json(orient='records')[1:-1].replace('},{', '} {')
        if interactions:
            return interactions, 200
        else:
            jsonify({"error": "Interactions not found"}), 404
    else:
        return jsonify({"error": "Cookie 'uuidcookie' not found"}), 404

@app.route('/scorecard_api/userscorecard/<uuidCookie>', defaults={'scoreCardType': 'defaultType'}, methods=['GET'])
@app.route('/scorecard_api/userscorecard/<uuidCookie>/<scoreCardType>', methods=['GET'])
def generateScoreCard(uuidCookie, scoreCardType):
    if not uuidCookie:
        return jsonify({"error": "Cookie 'uuidcookie' not found"}), 404
    
    # Filter DB on uuidCookie
    cwe_1400_statistics, cwe_1000_statistics = scorecard.get_cwe_statistics(uuidCookie)

    if scoreCardType == 'defaultType':
        cwe_statistics_all = {
            "cwe1000": cwe_1000_statistics.fillna("").to_dict(orient='records'),
            "cwe1400": cwe_1400_statistics.fillna("").to_dict(orient='records')
        }
        return jsonify(cwe_statistics_all), 200
    elif scoreCardType == "cwe1000":
        return jsonify(cwe_1000_statistics.fillna("").to_dict(orient='records')), 200
    elif scoreCardType == "cwe1400":
        return jsonify(cwe_1400_statistics.fillna("").to_dict(orient='records')), 200
    else:
        return jsonify({"error": "Scorecard type not found"}), 404

@app.route('/scorecard_api/groupstatistics/<password>', methods=['GET'])
def generateGroupStatistics(password):
    if password == "supersecretkeyword":
        # consider all players
        cwe_1400_statistics, cwe_1000_statistics = scorecard.get_cwe_statistics()
        cwe_statistics_all = {
            "cwe1000": cwe_1000_statistics.fillna("").to_dict(orient='records'),
            "cwe1400": cwe_1400_statistics.fillna("").to_dict(orient='records')
        }
        return jsonify(cwe_statistics_all), 200
    else:
        return jsonify({"error": "Forbidden."}), 403

if DEVELOPMENT:
    @app.route('/dev/get_source_code/<_file>', methods=['GET'])
    def get_source(_file):
        source = "IF YOU SEE THIS< THE BACKEND SCREWED UP."
        with open (f'snippets/{_file}', 'r') as f:
            source = f.read()
        print(source)
        return jsonify({
            'source' : source
            })


    @app.route('/dev/edit', methods=['GET'])
    def dev_edit():
        available_exercises = [f'{v["source"]} {uuid}' for uuid, v in exercises.items()]
        print(available_exercises)
        if not BACKENDONLY:
            return render_template('dev_editPage.html',
                                available_exercises=available_exercises,
                                extensions=utils.ext2lang.keys())
        else:
            return jsonify({'available_exercises': available_exercises,
                            'extensions'         : utils.ext2lang.keys()}), 200
    
    @app.route('/dev/submit', methods=['POST'])
    def dev_submit():
        data = request.get_json()
        mode = data.get('mode', None)
        
        
        message = None
        # Validation and data parsing
        if mode=='new':
            filename    = data.get('filename'   , None)
            extension   = data.get('extension'  , None)
            sourceCode  = data.get('sourceCode' , None)
            displayName = data.get('displayName', None)

            full_filename = f'{filename}.{extension}'
            if not all([filename, extension, sourceCode, displayName]):
                message = f'[{mode=}] Missing filename/extension/sourceCode/displayName.'
            if os.path.exists(f'snippets/{full_filename}'):
                message = f'[{mode=}] Given filename exists. Use "update" mode instead.'

        elif mode=='update':
            sourceCode          = data.get('sourceCode'    , None)
            chosenExercise      = data.get('chosenExercise', None)
            full_filename, uuid = chosenExercise.split()           
            if not chosenExercise:
                message = f'[{mode=}] Missing chosenExercise. How!?'
        
        else: # idk how we can end up here.
            message = f'[{mode=}] B0rkde.'

        if message: # if this was set, WE'VE FAILED VALIDATION.
            return jsonify({'message': message,
                            'stdout': '',
                            'stderr': ''})

        
        try:
            with open(f'snippets/{full_filename}', 'w') as f:
                f.write(sourceCode)
        except:
            return jsonify({'message': f'snippets/{full_filename} somehow unwriteable.',
                            'stdout': '',
                            'stderr': 'b0rked'})

        
        try:
            if mode == 'new':
                cmd = f'cd utils && ./genChalYaml.py {full_filename} "{displayName}"'
            else:
                cmd = f'cd utils && ./genChalYaml.py {full_filename} {uuid} --update'

            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            with open('exercises.yaml', 'r') as f:
                global exercises # dev hax. don't use this if you care about thread safety.
                exercises = yaml.safe_load(f)
            return jsonify({'message': f"",
                            'stdout': result.stdout,
                            'stderr': result.stderr
                        })
        except Exception as e:
            return jsonify({'message': f"",
                            'stdout': '',
                            'stderr': str(e)})

#######################
### --- SURVEYS --- ### 
#######################



# Mock survey data
survey_data = {
    "survey_id_1": {
        "flag": "Survey Complete!",
        "questions": {
            "q1": {
                "question_text": "What is your favorite color?",
                "b_multi_answer": False,
                "b_sub_questions": False,
                "answers": {
                    "q1_a": "Red",
                    "q1_b": "Blue"
                }
            },
            "q2": {
                "question_text": "Choose your favorite fruits:",
                "b_multi_answer": True,
                "b_sub_questions": True,
                "sub_questions": {
                    "q21": {
                        "question_text": "Tropical fruits",
                        "b_multi_answer": True,
                        "answers": {
                            "q21_a": "Mango",
                            "q21_b": "Pineapple"
                        }
                    },
                    "q22": {
                        "question_text": "Berries",
                        "b_multi_answer": False,
                        "answers": {
                            "q22_a": "Strawberry",
                            "q22_b": "Blueberry"
                        }
                    }
                }
            },
            "q3": {
                "question_text": "What is your favorite activity?",
                "b_other_answer": True,
                "b_sub_questions": False,
                "answers": {
                    "q3_a": "Reading",
                    "q3_b": "Sports",
                    "q3_c": "Traveling"
                }
            },
            "q4": {
                "question_text": "Rate your preferences for different cuisines:",
                "b_sub_questions": True,
                "sub_questions": {
                    "q41": {
                        "question_text": "Do you enjoy Italian food?",
                        "b_other_answer": True,
                        "b_multi_answer": False,
                        "answers": {
                            "q41_a": "Yes",
                            "q41_b": "No"
                        }
                    },
                    "q42": {
                        "question_text": "How often do you eat Mexican food?",
                        "b_other_answer": False,
                        "b_multi_answer": False,
                        "answers": {
                            "q42_a": "Often",
                            "q42_b": "Rarely",
                            "q42_c": "Never"
                        }
                    },
                    "q43": {
                        "question_text": "What's your opinion on Japanese food?",
                        "b_other_answer": True,
                        "b_multi_answer": True,
                        "answers": {
                            "q43_a": "Love it",
                            "q43_b": "It's okay",
                            "q43_c": "Dislike it"
                        }
                    }
                }
            }
        }
    }
}

with open ("surveys.yaml", "r") as f:
    survey_data = yaml.safe_load(f)


@app.route("/survey/<survey_id>/<question_id>", methods=["GET", "POST"])
def survey(survey_id, question_id):
    # Validate survey and question
    survey = survey_data.get(survey_id)
    if not survey:
        return "Survey not found", 404

    question = survey["questions"].get(question_id)
    if not question:
        return "Question not found", 404

    # Handle form submission
    if request.method == "POST":
        user_id = request.cookies.get('uuid')
        print(f"\n!!!!{user_id}!!!\n")
        answers = request.form.to_dict(flat=False)  # Allow multiple values for the same key
        print(f"\n{answers=}\n")
        for key, values in answers.items():
            if key.endswith("_other"):
                # Handle custom "Other" answers
                sub_question_id = key.replace("_other", "")
                if answers.get(f"{sub_question_id}_other_toggle") or values[0].strip():
                    response = Response(
                        survey_id=survey_id,
                        user_id=user_id,
                        question_id=question_id,
                        sub_question_id=sub_question_id,
                        answer=values[0]  # Store custom "Other" answer
                    )
                    db.session.add(response)
            elif key.endswith("_other_toggle"):
                continue  # Skip toggle checkboxes, they are handled with the text box
            else:
                sub_question_id = key if "_" in key else None
                for value in values:  # Iterate through all selected values
                    response = Response(
                        survey_id=survey_id,
                        user_id=user_id,
                        question_id=question_id,
                        sub_question_id=sub_question_id,
                        answer=value
                    )
                    db.session.add(response)
        db.session.commit()


        # Redirect to the next question or show the flag if it's the last question
        question_keys = list(survey["questions"].keys())
        next_index = question_keys.index(question_id) + 1
        if next_index < len(question_keys):
            return redirect(url_for("survey", survey_id=survey_id, question_id=question_keys[next_index]))
        else:
            return render_template("survey_complete.html", flag=survey["flag"])

    # Render the question page
    return render_template("survey_question.html", survey_id=survey_id, question_id=question_id, question=question)


if __name__ == '__main__':
    

    if DEVELOPMENT:
        # refreshing the exercises.yaml file gets handled in code.
        extra_files=['quizzes.yaml'] 
    else:
        extra_files=["exercises.yaml", "quizzes.yaml"]

    if not BACKENDONLY:
        _port = 5000
    else:
        _port = 8000
    if DEPLOYMENT:
        _port = 8001
        DEBUG = False


    app.run('0.0.0.0', port=_port, debug=DEBUG,
            extra_files=extra_files,
            exclude_patterns=["snippets/*",
                              "snippets/_testing/*",
                              "snippets/backburner/*"
                              "utils/tmp/*"])
