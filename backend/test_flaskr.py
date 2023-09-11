import os
import unittest
import json
from flask_sqlalchemy import SQLAlchemy

from flaskr import create_app
from models import setup_db, Question, Category


class TriviaTestCase(unittest.TestCase):
    """This class represents the trivia test case"""

    def setUp(self):
        """Define test variables and initialize app."""
        self.app = create_app()
        self.client = self.app.test_client
        self.database_name = "trivia_test"
        self.database_path ="postgres://{}:{}@{}/{}".format('student', 'student','localhost:5432', self.database_name)
        setup_db(self.app, self.database_path)

        # binds the app to the current context
        with self.app.app_context():
            self.db = SQLAlchemy()
            self.db.init_app(self.app)
            # create all tables
            self.db.create_all()
    
    def tearDown(self):
        """Executed after reach test"""
        pass

    # GET Categories tests
    def get_categories(self):
        res = self.client().get('/categories')
        data = json.loads(res.data)
        
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(len(data['categories']))
        self.assertTrue(data['total_categories'])
        
    def test_404_error_get_category_not_in_db(self):
        res = self.client().get('/categories/100')
        data = json.loads(res.data)
        
        self.assertEqual(res.status_code, 404)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'Cannot find resource for this request')
        
    # GET paginated questions tests
    def test_get_questions_paginated(self):
        res = self.client().get("/questions")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['total_questions'])
        self.assertTrue(len(data["questions"]))
    
    def test_404_error_get_questions_paginated_no_page_exists(self):
        res = self.client().get('/questions?page=9999999')
        data = json.loads(res.data)
        
        self.assertEqual(res.status_code, 404)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'Cannot find resource for this request')
    
    # DELETE question tests
    def test_delete_question(self):
        
        
        
        #add question
        q = Question(question="what is love?", answer="baby, don't hurt me no more", category=1, difficulty=3)
       
        q.insert()
        
        # before delete
        before = len(Question.query.all())
        
        q_id = q.id
        
        # res is going to the path with the created question id
        res = self.client().delete('/questions/{}'.format(q_id))
        data = json.loads(res.data)
        
        question = Question.query.filter(Question.id == q_id).one_or_none()
        
        after = len(Question.query.all())
        
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertEqual(data['question_deleted'], q_id)
        self.assertEqual(question, None)
        self.assertTrue(data['total_questions'])
        self.assertTrue(after < before)
    
    def test_422_error_delete_question_not_in_db(self):
        res = self.client().delete('/questions/100')
        data = json.loads(res.data)
        
        self.assertEqual(res.status_code, 422)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'Cannot process this request')
    
    
    # POST create question tests
    def test_create_question(self):
        
        new_question = {
            'question': 'why?',
            'answer':'because I said so',
            'difficulty': 1,
            'category':3
        }
        
        before = len(Question.query.all())
        
        res = self.client().post('/questions', json=new_question)
        data = json.loads(res.data)
        
        after = len(Question.query.all())
        
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(after > before)
    
    def test_422_error_incomplete_form_data(self):
        
        new_question = {
            'question': 'why?',
            'difficulty': 1,
            'category':3
        }
        
        res = self.client().post('/questions', json=new_question)
        data = json.loads(res.data)
        
        self.assertEqual(res.status_code, 422)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'Cannot process this request')
        
    # POST search question tests
    def test_get_question_search_with_results(self):
        res = self.client().post('/questions', json={'searchTerm': 'title'})
        data = json.loads(res.data)
        
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertEqual(len(data['questions']), 2)
        
    def test_422_error_no_search_results(self):
        res = self.client().post('/questions', json={'searchTerm': 'butterbeer'})
        data = json.loads(res.data)
        
        self.assertEqual(res.status_code, 422)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'Cannot process this request')
    
    # GET questions by category tests
    def test_get_questions_by_category(self):
        res = self.client().get('/categories/1/questions')
        data = json.loads(res.data)
        
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertNotEqual(len(data['questions']), 0)
        
    def test_422_error_bad_category(self):
        res = self.client().get('/categories/100/questions')
        data = json.loads(res.data)
        
        self.assertEqual(res.status_code, 422)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'Cannot process this request')
    
    # POST play quiz tests
    def test_play_quiz(self):
        
        test_quiz = {
            'previous_questions':[],
            'quiz_category': {
                'type': 'Science',
                'id': 1
            }}
        
        res = self.client().post('/quizzes', json=test_quiz)
        data = json.loads(res.data)
        
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['question'], True)
        
    def test_422_play_quiz_fails(self):
        # removed 'previous_questions'
        test_quiz = {
            'quiz_category': {
                'type': 'Science',
                'id': 1
            }}
        
        res = self.client().post('/quizzes', json=test_quiz)
        data = json.loads(res.data)
        
        self.assertEqual(res.status_code, 422)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'Cannot process this request')
  

# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()