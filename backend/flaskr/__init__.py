import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

# helper method to put 10 questions per page
def paginate_questions(request, selection):
    page = request.args.get("page", 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE
    
    questions = [question.format() for question in selection]
    current_questions = questions[start:end]

    return current_questions

# create and configure the app
def create_app(test_config=None):
    app = Flask(__name__)
    setup_db(app)
    # setup CORS
    CORS(app, resources={"/": {"origins": "*"}})
    
    # setup CORS headers
    @app.after_request
    def after_request(response):
        response.headers.add(
            "Access-Control-Allow-Headers", "Content-Type,Authorization,true"
        )
        response.headers.add(
            "Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS"
        )
        return response

    # return all categories
    @app.route('/categories')
    def get_categories():
        categories = Category.query.all()
        
         # fix for error of Category not JSON serializable
        cat_dict = {}
        for cat in categories:
            cat_dict[cat.id] = cat.type
        
        # if no categories are found - send to error
        if (len(cat_dict) == 0):
            abort(404)
        
        result = {'success': True,
                 'categories': cat_dict,
                 'total_categories': len(cat_dict)}
            
        return jsonify(result)


# Endpoint to handle GET requests for questions,including pagination (every 10 questions).
# This endpoint returns a list of questions, number of total questions, current category, categories.

    @app.route('/questions')
    def get_questions():
        
        questions = Question.query.all()
        question_format = [question.format() for question in questions]
        total_questions = len(questions)
        
        # gets 10 questions/page
        current_questions = paginate_questions(request, questions)
        
        # fix for error of Category not JSON serializable
        cat_dict = {}
        categories = Category.query.all()
        for cat in categories:
            cat_dict[cat.id] = cat.type
        
        # check for error of empty DBs
        if ((len(current_questions) == 0) or (len(cat_dict) == 0)):
            abort(404)
        
        result = {'success': True,
                 'categories': cat_dict,
                 'total_questions': total_questions,
                 'questions': question_format}
            
        return jsonify(result)  


# When you click the trash icon next to a question, the question will be removed. 
# This removal will persist in the database and when you refresh the page.
    
    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        try:
            # selecting question - if ID not found, vqriable question is set to None
            question = Question.query.filter(Question.id == question_id).one_or_none()
            
            if question is None:
                # bad request
                abort(400)
            
            # delete question from DB
            question.delete()
            
            # getting all reamining questions for display
            selection = Question.query.order_by(Question.id).all()
            current_questions = paginate_questions(request, selection)
            question_format = [question.format() for question in selection]

            result = {
                'success': True,
                'question_deleted': question_id,
                'total_questions': len(Question.query.all()),
                'questions': question_format
            }
            
            return jsonify(result)
        
        except:
            # unprocessible request
            abort(422)
        
# Endpoint to POST a new question, which will require the question and answer text, category, and difficulty score.

# POST endpoint to get questions based on a search term. It should return any questions for whom the search term is a substring of the question.

    @app.route('/questions', methods=['POST'])
    def post_or_search_question():
        
        # get form body
        body = request.get_json()
        
        # variables will either have the value from the form OR None, which is what we will filter on to determine if it's a valid ADD
        
        new_question = body.get('question', None)
        new_answer =  body.get('answer', None)
        new_difficulty = body.get('difficulty', None)
        new_category = body.get('category', None)
        
        # set search term from body - if there is no search term, set to None
        search_term = body.get('searchTerm', None)
        
        try:
            # if there's a search term, enter this 'if' block
            if search_term:
                
                # get all questions with search term
                selection = Question.query.order_by(Question.id).filter(Question.question.ilike(f'%{search_term}%')).all()
                # paginate found questions with search term
                current_questions = paginate_questions(request, selection)
                
                # if there  are questions with search term
                if current_questions:
                    result = {
                        'success': True,
                        'questions': selection,
                        'total questions in search': len(selection)
                    }
                    
                    return jsonify(result)
                
                else:
                    #no results found
                    abort(404)
                    
            # no search term, create new question
            else:
                
                # check if any create sections of form are blank and abort if blank sections are found
                if ((new_question is None) or (new_answer is None) or (new_difficulty is None) or (new_category is None)):
                    abort(422)
                
                # if valid fields are populated, create new question
                created_question = Question(new_question, new_answer, new_difficulty, new_category)

                # adds to DB
                created_question.insert()

                #reload questions on page
                selection = Question.query.order_by(Question.id).all()
                current_questions = paginate_questions(request, selection)

                result = {
                    'success': True,
                    'created': created_question.id,
                    'total_questions': len(Question.query.all()),
                    'questions': selection
                }
                return jsonify(result)
            
        except:
            abort(422)
    

    # GET endpoint to get questions based on category
    
    @app.route('/categories/<int:cat_id>/questions')
    def list_questions_by_category(cat_id):
        
        # gets category requested
        current_category = Category.query.filter_by(id=cat_id).one_or_none()
        
        if current_category is None:
            abort(422)
        
        # gets questions from requested category
        selection = Question.query.filter_by(category=current_category.id).all()
        current_questions = paginate_questions(request, selection)
        
        result = {
            'success': True,
            'current category': current_category.type,
            'total questions': len(current_questions),
            'questions': selection
        }
        
        return jsonify(result)
        

    #POST endpoint to get questions to play the quiz. 
    #This endpoint takes a category and previous question parameters and returns a random question
    
    @app.route('/quizzes', methods=['POST'])
    def quiz():
        try:
            body = request.get_json()

            # 'All' is id 0 AND this is a dictionary
            category = body.get('quiz_category')

            # looks like this is an array of questions
            previous_questions = body.get('previous_questions')

            # check for 'All' category or specific category and get all available questions
            if (category['id']== 0):
                questions = Question.query.filter(Question.id.notin_(previous_questions)).all()
                
            # else grab only questions from selected category that are not in previously used
            else:
                questions = Question.query.filter_by(category = category['id']).filter(Question.id.notin_(previous_questions)).all()
                
        # 1. checks if there are remaining questions
        # 2. if so, makes the current question a question from remaining questions with a random index
        # 3. else, makes the current question - None to end the game
        # 4. returns: success is true and the current question
            
            # helper method to get random index number
            def random_index():
                return random.randrange(0, len(questions))
            
            if len(questions) > 0:
                current_question = questions[random_index()].format() 
            else:
                current_question = None
            
            return jsonify({
                'success':True,
                'question': current_question
            })
            
        
        except:
            abort(422)
                 
    
    # error handlers
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify ({
            'success': False,
            'error': 400,
            'message': 'Cannot handle this request'
        }), 400
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify ({
            'success': False,
            'error': 404,
            'message': 'Cannot find resource for this request'
        }), 404
    
    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify ({
            'success': False,
            'error': 422,
            'message': 'Cannot process this request'
        }), 422
    
    @app.errorhandler(500)
    def internal_server_error(error):
        return jsonify ({
            'success': False,
            'error': 500,
            'message': 'Internal server error - cannot process request'
        }), 500

    return app
