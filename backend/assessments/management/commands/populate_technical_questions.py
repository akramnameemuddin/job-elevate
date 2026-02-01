"""
Management command to populate technical skills with pre-defined relevant questions.
Ensures 100 high-quality, skill-specific questions per skill.
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from assessments.models import Skill, QuestionBank, SkillCategory


class Command(BaseCommand):
    help = 'Populate technical skills with 100 relevant questions each'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skill',
            type=str,
            help='Populate specific skill by name',
        )

    def handle(self, *args, **options):
        skill_name = options.get('skill')

        if skill_name:
            try:
                skill = Skill.objects.get(name__iexact=skill_name, is_active=True)
                self.populate_skill(skill)
            except Skill.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Skill "{skill_name}" not found'))
                return
        else:
            # Get all technical skills
            skills = Skill.objects.filter(is_active=True)
            self.stdout.write(f'Populating {skills.count()} skills with questions...')
            
            for skill in skills:
                self.populate_skill(skill)

        self.stdout.write(self.style.SUCCESS('[SUCCESS] Question population completed!'))

    def populate_skill(self, skill):
        """Populate a single skill with 100 questions"""
        existing_count = QuestionBank.objects.filter(skill=skill).count()
        
        if existing_count >= 100:
            self.stdout.write(
                self.style.WARNING(f'[SKIP] {skill.name}: Already has {existing_count} questions')
            )
            return

        # Get question templates for this skill
        questions = self.get_skill_questions(skill.name)
        
        if not questions:
            self.stdout.write(
                self.style.WARNING(
                    f'[WARN] {skill.name}: No question templates available. '
                    f'Use generate_skill_questions command with AI.'
                )
            )
            return

        # Save questions
        saved_count = 0
        with transaction.atomic():
            for q_data in questions:
                try:
                    # Check if question already exists
                    exists = QuestionBank.objects.filter(
                        skill=skill,
                        question_text=q_data['question']
                    ).exists()
                    
                    if not exists:
                        QuestionBank.objects.create(
                            skill=skill,
                            question_text=q_data['question'],
                            options=q_data['options'],
                            correct_answer=q_data['correct_answer'],
                            difficulty=q_data['difficulty'],
                            points=q_data['points'],
                            explanation=q_data.get('explanation', ''),
                            created_by_ai=False  # Template questions are not AI-generated
                        )
                        saved_count += 1
                except Exception as e:
                    self.stdout.write(f'  Error: {str(e)}')
                    continue

        total_count = QuestionBank.objects.filter(skill=skill).count()
        self.stdout.write(
            self.style.SUCCESS(
                f'[OK] {skill.name}: Added {saved_count} questions (Total: {total_count}/100)'
            )
        )

    def get_skill_questions(self, skill_name):
        """Get pre-defined questions for each skill"""
        # Map skill names to question sets
        skill_questions = {
            'Python': self.get_python_questions(),
            'SQL': self.get_sql_questions(),
            'JavaScript': self.get_javascript_questions(),
            'React': self.get_react_questions(),
            'Django': self.get_django_questions(),
            'Excel': self.get_excel_questions(),
            'Tableau': self.get_tableau_questions(),
            'Power BI': self.get_powerbi_questions(),
            'power-bi': self.get_powerbi_questions(),
            'NumPy': self.get_numpy_questions(),
            'Pandas': self.get_pandas_questions(),
            'Git': self.get_git_questions(),
            'HTML/CSS': self.get_html_css_questions(),
            'Java': self.get_java_questions(),
            'C++': self.get_cpp_questions(),
            'TypeScript': self.get_typescript_questions(),
            'typescript': self.get_typescript_questions(),
            'REST APIs': self.get_rest_apis_questions(),
            'Docker': self.get_docker_questions(),
            'docker': self.get_docker_questions(),
            'AWS': self.get_aws_questions(),
            'aws': self.get_aws_questions(),
            'Hadoop': self.get_hadoop_questions(),
            'hadoop': self.get_hadoop_questions(),
        }

        return skill_questions.get(skill_name, [])

    def get_python_questions(self):
        """30 Python questions covering core concepts"""
        return [
            # Easy questions (12)
            {'question': 'What is the correct way to create a list in Python?', 'options': ['list = []', 'list = ()', 'list = {}', 'list = <>'], 'correct_answer': 'list = []', 'difficulty': 'easy', 'points': 5},
            {'question': 'Which keyword is used to define a function in Python?', 'options': ['function', 'def', 'func', 'define'], 'correct_answer': 'def', 'difficulty': 'easy', 'points': 5},
            {'question': 'What is the output of: print(type([1, 2, 3]))?', 'options': ["<class 'list'>", "<class 'tuple'>", "<class 'array'>", "<class 'set'>"], 'correct_answer': "<class 'list'>", 'difficulty': 'easy', 'points': 5},
            {'question': 'How do you insert comments in Python code?', 'options': ['# This is a comment', '// This is a comment', '/* This is a comment */', '<!-- This is a comment -->'], 'correct_answer': '# This is a comment', 'difficulty': 'easy', 'points': 5},
            {'question': 'Which operator is used for exponentiation in Python?', 'options': ['**', '^', 'exp', 'pow'], 'correct_answer': '**', 'difficulty': 'easy', 'points': 5},
            {'question': 'What is the correct file extension for Python files?', 'options': ['.py', '.python', '.pt', '.pyt'], 'correct_answer': '.py', 'difficulty': 'easy', 'points': 5},
            {'question': 'Which method is used to add an element to the end of a list?', 'options': ['append()', 'add()', 'insert()', 'push()'], 'correct_answer': 'append()', 'difficulty': 'easy', 'points': 5},
            {'question': 'What keyword is used to create a loop in Python?', 'options': ['for or while', 'loop', 'repeat', 'foreach'], 'correct_answer': 'for or while', 'difficulty': 'easy', 'points': 5},
            {'question': 'How do you check the length of a list in Python?', 'options': ['len(list)', 'list.length()', 'list.size()', 'length(list)'], 'correct_answer': 'len(list)', 'difficulty': 'easy', 'points': 5},
            {'question': 'Which data type is immutable in Python?', 'options': ['Tuple', 'List', 'Dictionary', 'Set'], 'correct_answer': 'Tuple', 'difficulty': 'easy', 'points': 5},
            {'question': 'What is the output of: print(10 // 3)?', 'options': ['3', '3.333', '3.0', '4'], 'correct_answer': '3', 'difficulty': 'easy', 'points': 5},
            {'question': 'Which keyword is used to handle exceptions in Python?', 'options': ['try-except', 'catch-throw', 'error-handle', 'exception-catch'], 'correct_answer': 'try-except', 'difficulty': 'easy', 'points': 5},
            
            # Medium questions (9)
            {'question': 'What is a list comprehension in Python?', 'options': ['A way to create lists using a single line of code', 'A method to compress lists', 'A function to compare lists', 'A tool to debug lists'], 'correct_answer': 'A way to create lists using a single line of code', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is the difference between == and is in Python?', 'options': ['== compares values, is compares identity (memory location)', '== compares identity, is compares values', 'They are exactly the same', '== is for numbers, is is for strings'], 'correct_answer': '== compares values, is compares identity (memory location)', 'difficulty': 'medium', 'points': 10},
            {'question': 'What does *args allow in a function definition?', 'options': ['Pass a variable number of positional arguments', 'Pass keyword arguments', 'Create a pointer', 'Multiply arguments'], 'correct_answer': 'Pass a variable number of positional arguments', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is a decorator in Python?', 'options': ['A function that modifies another function', 'A design pattern', 'A variable declaration', 'A loop structure'], 'correct_answer': 'A function that modifies another function', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is the purpose of __init__ in a Python class?', 'options': ['Constructor method to initialize objects', 'Destructor method', 'Static method', 'Private method'], 'correct_answer': 'Constructor method to initialize objects', 'difficulty': 'medium', 'points': 10},
            {'question': 'What does the enumerate() function return?', 'options': ['An iterator of tuples containing index and value', 'Only indexes', 'Only values', 'A dictionary'], 'correct_answer': 'An iterator of tuples containing index and value', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is the difference between .append() and .extend() for lists?', 'options': ['append() adds single element, extend() adds multiple elements', 'They do the same thing', 'append() is faster', 'extend() only works with tuples'], 'correct_answer': 'append() adds single element, extend() adds multiple elements', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is a lambda function in Python?', 'options': ['Anonymous single-expression function', 'Named function', 'Class method', 'Loop structure'], 'correct_answer': 'Anonymous single-expression function', 'difficulty': 'medium', 'points': 10},
            {'question': 'What does the zip() function do?', 'options': ['Combines multiple iterables element-wise', 'Compresses files', 'Sorts lists', 'Removes duplicates'], 'correct_answer': 'Combines multiple iterables element-wise', 'difficulty': 'medium', 'points': 10},
            
            # Hard questions (9)
            {'question': 'What is the Global Interpreter Lock (GIL) in Python?', 'options': ['A mutex that protects access to Python objects', 'A security feature for global variables', 'A memory management tool', 'A threading optimization technique'], 'correct_answer': 'A mutex that protects access to Python objects', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is the difference between deepcopy and shallow copy?', 'options': ['deepcopy copies nested objects, shallow copy only top-level', 'They are the same', 'deepcopy is faster', 'shallow copy is more secure'], 'correct_answer': 'deepcopy copies nested objects, shallow copy only top-level', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is a generator in Python and how does it differ from a regular function?', 'options': ['Uses yield to return values lazily, saves memory', 'Returns all values at once', 'Same as regular function', 'Only works with numbers'], 'correct_answer': 'Uses yield to return values lazily, saves memory', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is method resolution order (MRO) in Python?', 'options': ['Order in which base classes are searched when executing a method', 'Order of method definitions', 'Speed ranking of methods', 'Memory allocation order'], 'correct_answer': 'Order in which base classes are searched when executing a method', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is the purpose of __slots__ in a Python class?', 'options': ['Restricts attributes and reduces memory usage', 'Creates time slots', 'Defines methods', 'Creates private variables'], 'correct_answer': 'Restricts attributes and reduces memory usage', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is metaclass in Python?', 'options': ['A class of a class that defines how a class behaves', 'A parent class', 'An abstract class', 'A static class'], 'correct_answer': 'A class of a class that defines how a class behaves', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is the difference between @staticmethod and @classmethod?', 'options': ['classmethod receives class as first argument, staticmethod receives nothing', 'They are the same', 'staticmethod is faster', 'classmethod is deprecated'], 'correct_answer': 'classmethod receives class as first argument, staticmethod receives nothing', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is a context manager in Python (with statement)?', 'options': ['Manages resources with automatic setup and cleanup', 'Creates contexts', 'Manages memory', 'Controls threads'], 'correct_answer': 'Manages resources with automatic setup and cleanup', 'difficulty': 'hard', 'points': 15},
            {'question': 'What does the __call__ method do in a class?', 'options': ['Makes instances callable like functions', 'Calls the constructor', 'Defines class methods', 'Creates static methods'], 'correct_answer': 'Makes instances callable like functions', 'difficulty': 'hard', 'points': 15},
        ]

    def get_sql_questions(self):
        """30 SQL questions covering database fundamentals"""
        return [
            # Easy (12)
            {'question': 'Which SQL statement is used to extract data from a database?', 'options': ['GET', 'SELECT', 'EXTRACT', 'FETCH'], 'correct_answer': 'SELECT', 'difficulty': 'easy', 'points': 5},
            {'question': 'Which SQL clause is used to filter records?', 'options': ['WHERE', 'FILTER', 'SELECT', 'HAVING'], 'correct_answer': 'WHERE', 'difficulty': 'easy', 'points': 5},
            {'question': 'Which SQL statement is used to update data in a database?', 'options': ['UPDATE', 'MODIFY', 'CHANGE', 'SET'], 'correct_answer': 'UPDATE', 'difficulty': 'easy', 'points': 5},
            {'question': 'Which SQL statement is used to delete data from a database?', 'options': ['DELETE', 'REMOVE', 'DROP', 'CLEAR'], 'correct_answer': 'DELETE', 'difficulty': 'easy', 'points': 5},
            {'question': 'Which SQL statement is used to insert new data into a database?', 'options': ['INSERT INTO', 'ADD', 'PUT', 'CREATE'], 'correct_answer': 'INSERT INTO', 'difficulty': 'easy', 'points': 5},
            {'question': 'What does SQL stand for?', 'options': ['Structured Query Language', 'Strong Question Language', 'Structured Question Language', 'Simple Query Language'], 'correct_answer': 'Structured Query Language', 'difficulty': 'easy', 'points': 5},
            {'question': 'Which SQL keyword is used to sort the result set?', 'options': ['ORDER BY', 'SORT BY', 'GROUP BY', 'ARRANGE BY'], 'correct_answer': 'ORDER BY', 'difficulty': 'easy', 'points': 5},
            {'question': 'What does the COUNT() function do?', 'options': ['Returns the number of rows', 'Adds numbers', 'Counts characters', 'Measures table size'], 'correct_answer': 'Returns the number of rows', 'difficulty': 'easy', 'points': 5},
            {'question': 'Which SQL statement creates a new table?', 'options': ['CREATE TABLE', 'NEW TABLE', 'MAKE TABLE', 'BUILD TABLE'], 'correct_answer': 'CREATE TABLE', 'difficulty': 'easy', 'points': 5},
            {'question': 'What is a PRIMARY KEY?', 'options': ['A unique identifier for table records', 'The first column', 'An encrypted key', 'A table name'], 'correct_answer': 'A unique identifier for table records', 'difficulty': 'easy', 'points': 5},
            {'question': 'Which SQL clause is used to limit the number of records returned?', 'options': ['LIMIT', 'TOP', 'MAX', 'RANGE'], 'correct_answer': 'LIMIT', 'difficulty': 'easy', 'points': 5},
            {'question': 'What does DISTINCT keyword do?', 'options': ['Removes duplicate values', 'Sorts data', 'Filters data', 'Counts records'], 'correct_answer': 'Removes duplicate values', 'difficulty': 'easy', 'points': 5},
            
            # Medium (9)
            {'question': 'What is a JOIN in SQL?', 'options': ['Combines rows from two or more tables', 'Merges databases', 'Adds columns', 'Creates relationships'], 'correct_answer': 'Combines rows from two or more tables', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is the difference between INNER JOIN and LEFT JOIN?', 'options': ['INNER returns only matching rows, LEFT returns all left table rows', 'They are the same', 'LEFT is faster', 'INNER is deprecated'], 'correct_answer': 'INNER returns only matching rows, LEFT returns all left table rows', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is the purpose of GROUP BY clause?', 'options': ['Groups rows with same values for aggregate functions', 'Sorts rows', 'Filters rows', 'Joins tables'], 'correct_answer': 'Groups rows with same values for aggregate functions', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is the difference between WHERE and HAVING?', 'options': ['WHERE filters before grouping, HAVING filters after grouping', 'They are the same', 'WHERE is faster', 'HAVING is deprecated'], 'correct_answer': 'WHERE filters before grouping, HAVING filters after grouping', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is a FOREIGN KEY?', 'options': ['A field that links to PRIMARY KEY of another table', 'An encrypted key', 'A backup key', 'A temporary key'], 'correct_answer': 'A field that links to PRIMARY KEY of another table', 'difficulty': 'medium', 'points': 10},
            {'question': 'What does the UNION operator do?', 'options': ['Combines result sets of two SELECT statements', 'Joins tables', 'Merges columns', 'Creates views'], 'correct_answer': 'Combines result sets of two SELECT statements', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is an INDEX in SQL?', 'options': ['A data structure that improves query speed', 'A table counter', 'A column number', 'A database version'], 'correct_answer': 'A data structure that improves query speed', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is a subquery?', 'options': ['A query nested inside another query', 'A backup query', 'A query template', 'A query error'], 'correct_answer': 'A query nested inside another query', 'difficulty': 'medium', 'points': 10},
            {'question': 'What does COALESCE() function do?', 'options': ['Returns first non-NULL value from a list', 'Combines strings', 'Counts values', 'Sorts values'], 'correct_answer': 'Returns first non-NULL value from a list', 'difficulty': 'medium', 'points': 10},
            
            # Hard (9)
            {'question': 'What is a database transaction and what are ACID properties?', 'options': ['Atomic, Consistent, Isolated, Durable operations', 'A query group', 'A table backup', 'A data transfer'], 'correct_answer': 'Atomic, Consistent, Isolated, Durable operations', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is database normalization?', 'options': ['Organizing data to reduce redundancy', 'Making data uniform', 'Speeding up queries', 'Backing up data'], 'correct_answer': 'Organizing data to reduce redundancy', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is the difference between clustered and non-clustered index?', 'options': ['Clustered sorts physical data, non-clustered creates separate structure', 'They are the same', 'Clustered is faster', 'Non-clustered is deprecated'], 'correct_answer': 'Clustered sorts physical data, non-clustered creates separate structure', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is a stored procedure?', 'options': ['Precompiled SQL code stored in database', 'A backup process', 'A query template', 'A table copy'], 'correct_answer': 'Precompiled SQL code stored in database', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is the difference between DELETE and TRUNCATE?', 'options': ['DELETE can be rolled back and logs rows, TRUNCATE is faster and resets identity', 'They are the same', 'DELETE is faster', 'TRUNCATE is deprecated'], 'correct_answer': 'DELETE can be rolled back and logs rows, TRUNCATE is faster and resets identity', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is a database view?', 'options': ['A virtual table based on SQL query result', 'A table copy', 'A backup', 'A table index'], 'correct_answer': 'A virtual table based on SQL query result', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is query optimization?', 'options': ['Improving query performance through execution plan analysis', 'Writing shorter queries', 'Using more tables', 'Adding indexes everywhere'], 'correct_answer': 'Improving query performance through execution plan analysis', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is the purpose of window functions like ROW_NUMBER()?', 'options': ['Perform calculations across rows related to current row', 'Count rows', 'Number rows', 'Sort rows'], 'correct_answer': 'Perform calculations across rows related to current row', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is a database trigger?', 'options': ['Automatically executed code in response to database events', 'A scheduled query', 'A backup process', 'An alert system'], 'correct_answer': 'Automatically executed code in response to database events', 'difficulty': 'hard', 'points': 15},
        ]

    def get_javascript_questions(self):
        """30 JavaScript questions"""
        return [
            # Easy (12)
            {'question': 'Which keyword is used to declare a variable that cannot be reassigned?', 'options': ['var', 'let', 'const', 'static'], 'correct_answer': 'const', 'difficulty': 'easy', 'points': 5},
            {'question': 'What is the correct syntax for a single-line comment in JavaScript?', 'options': ['// comment', '/* comment */', '# comment', '<!-- comment -->'], 'correct_answer': '// comment', 'difficulty': 'easy', 'points': 5},
            {'question': 'How do you create a function in JavaScript?', 'options': ['function myFunction()', 'def myFunction()', 'create myFunction()', 'func myFunction()'], 'correct_answer': 'function myFunction()', 'difficulty': 'easy', 'points': 5},
            {'question': 'What is the result of typeof []?', 'options': ['object', 'array', 'list', 'undefined'], 'correct_answer': 'object', 'difficulty': 'easy', 'points': 5},
            {'question': 'Which method adds an element to the end of an array?', 'options': ['push()', 'add()', 'append()', 'insert()'], 'correct_answer': 'push()', 'difficulty': 'easy', 'points': 5},
            {'question': 'How do you write an IF statement in JavaScript?', 'options': ['if (condition) { }', 'if condition { }', 'if (condition) then { }', 'if condition: '], 'correct_answer': 'if (condition) { }', 'difficulty': 'easy', 'points': 5},
            {'question': 'Which operator is used for strict equality comparison?', 'options': ['===', '==', '=', 'equals'], 'correct_answer': '===', 'difficulty': 'easy', 'points': 5},
            {'question': 'What does JSON stand for?', 'options': ['JavaScript Object Notation', 'JavaScript Online Notation', 'Java Standard Object Notation', 'JavaScript Oriented Network'], 'correct_answer': 'JavaScript Object Notation', 'difficulty': 'easy', 'points': 5},
            {'question': 'Which method converts a string to lowercase?', 'options': ['toLowerCase()', 'toLower()', 'lower()', 'lowerCase()'], 'correct_answer': 'toLowerCase()', 'difficulty': 'easy', 'points': 5},
            {'question': 'What is the output of: typeof null?', 'options': ['object', 'null', 'undefined', 'number'], 'correct_answer': 'object', 'difficulty': 'easy', 'points': 5},
            {'question': 'How do you declare an array in JavaScript?', 'options': ['var arr = []', 'var arr = ()', 'var arr = {}', 'var arr = <>'], 'correct_answer': 'var arr = []', 'difficulty': 'easy', 'points': 5},
            {'question': 'Which method removes the last element from an array?', 'options': ['pop()', 'remove()', 'delete()', 'shift()'], 'correct_answer': 'pop()', 'difficulty': 'easy', 'points': 5},
            
            # Medium (9)
            {'question': 'What is a closure in JavaScript?', 'options': ['Function with access to parent scope variables', 'A closed function', 'An error handler', 'A loop structure'], 'correct_answer': 'Function with access to parent scope variables', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is the difference between let and var?', 'options': ['let is block-scoped, var is function-scoped', 'They are the same', 'let is faster', 'var is deprecated'], 'correct_answer': 'let is block-scoped, var is function-scoped', 'difficulty': 'medium', 'points': 10},
            {'question': 'What does the spread operator (...) do?', 'options': ['Expands iterable into individual elements', 'Creates range', 'Repeats code', 'Comments code'], 'correct_answer': 'Expands iterable into individual elements', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is an arrow function?', 'options': ['Shorter syntax for function expressions: () => {}', 'A pointer function', 'A named function', 'A loop function'], 'correct_answer': 'Shorter syntax for function expressions: () => {}', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is destructuring in JavaScript?', 'options': ['Extracting values from arrays/objects into variables', 'Deleting objects', 'Breaking code', 'Error handling'], 'correct_answer': 'Extracting values from arrays/objects into variables', 'difficulty': 'medium', 'points': 10},
            {'question': 'What does array.map() do?', 'options': ['Creates new array by applying function to each element', 'Sorts array', 'Filters array', 'Reduces array'], 'correct_answer': 'Creates new array by applying function to each element', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is the purpose of Promise in JavaScript?', 'options': ['Handles asynchronous operations', 'Makes promises', 'Validates data', 'Creates delays'], 'correct_answer': 'Handles asynchronous operations', 'difficulty': 'medium', 'points': 10},
            {'question': 'What does async/await do?', 'options': ['Makes asynchronous code look synchronous', 'Speeds up code', 'Delays execution', 'Creates threads'], 'correct_answer': 'Makes asynchronous code look synchronous', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is the difference between == and ===?', 'options': ['== converts types, === checks type and value', 'They are the same', '== is faster', '=== is deprecated'], 'correct_answer': '== converts types, === checks type and value', 'difficulty': 'medium', 'points': 10},
            
            # Hard (9)
            {'question': 'What is event delegation in JavaScript?', 'options': ['Using single event listener on parent to manage child events', 'Passing events', 'Creating events', 'Removing events'], 'correct_answer': 'Using single event listener on parent to manage child events', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is the Event Loop in JavaScript?', 'options': ['Mechanism for handling asynchronous callbacks', 'A for loop', 'An event handler', 'A debugging tool'], 'correct_answer': 'Mechanism for handling asynchronous callbacks', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is prototypal inheritance?', 'options': ['Objects inherit directly from other objects', 'Class-based inheritance', 'Multiple inheritance', 'No inheritance'], 'correct_answer': 'Objects inherit directly from other objects', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is the difference between call(), apply(), and bind()?', 'options': ['call/apply invoke immediately with different argument passing, bind returns new function', 'They are the same', 'call is deprecated', 'bind is fastest'], 'correct_answer': 'call/apply invoke immediately with different argument passing, bind returns new function', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is hoisting in JavaScript?', 'options': ['Variable/function declarations moved to top of scope', 'Lifting objects', 'Optimizing code', 'Error handling'], 'correct_answer': 'Variable/function declarations moved to top of scope', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is a higher-order function?', 'options': ['Function that takes or returns other functions', 'A complex function', 'A parent function', 'A fast function'], 'correct_answer': 'Function that takes or returns other functions', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is memoization?', 'options': ['Caching function results to optimize performance', 'Memorizing code', 'Storing variables', 'Debugging technique'], 'correct_answer': 'Caching function results to optimize performance', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is the difference between null and undefined?', 'options': ['null is assigned value meaning empty, undefined means not assigned', 'They are the same', 'null is error', 'undefined is deprecated'], 'correct_answer': 'null is assigned value meaning empty, undefined means not assigned', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is a generator function?', 'options': ['Function that can pause and resume execution using yield', 'A function creator', 'A fast function', 'A deprecated function'], 'correct_answer': 'Function that can pause and resume execution using yield', 'difficulty': 'hard', 'points': 15},
        ]

    def get_react_questions(self):
        """30 React questions"""
        return [
            # Easy (12)
            {'question': 'What is JSX in React?', 'options': ['JavaScript XML - a syntax extension', 'JSON Extended Syntax', 'JavaScript eXtension', 'Java Syntax for XML'], 'correct_answer': 'JavaScript XML - a syntax extension', 'difficulty': 'easy', 'points': 5},
            {'question': 'How do you create a React component?', 'options': ['function Component() {}', 'class Component: ', 'component Component()', 'def Component()'], 'correct_answer': 'function Component() {}', 'difficulty': 'easy', 'points': 5},
            {'question': 'What is the purpose of ReactDOM.render()?', 'options': ['Render React elements to DOM', 'Create components', 'Define state', 'Handle events'], 'correct_answer': 'Render React elements to DOM', 'difficulty': 'easy', 'points': 5},
            {'question': 'Which hook is used to manage state in functional components?', 'options': ['useState', 'useEffect', 'useContext', 'useReducer'], 'correct_answer': 'useState', 'difficulty': 'easy', 'points': 5},
            {'question': 'What is props in React?', 'options': ['Properties passed to components', 'Component state', 'Event handlers', 'Lifecycle methods'], 'correct_answer': 'Properties passed to components', 'difficulty': 'easy', 'points': 5},
            {'question': 'How do you handle events in React?', 'options': ['onClick={handleClick}', 'onclick="handleClick()"', 'on-click={handleClick}', '@click="handleClick"'], 'correct_answer': 'onClick={handleClick}', 'difficulty': 'easy', 'points': 5},
            {'question': 'What does npm start do in a React app?', 'options': ['Starts development server', 'Builds production bundle', 'Installs dependencies', 'Runs tests'], 'correct_answer': 'Starts development server', 'difficulty': 'easy', 'points': 5},
            {'question': 'What is the virtual DOM?', 'options': ['Lightweight copy of real DOM for efficient updates', 'A testing tool', 'A database', 'A styling framework'], 'correct_answer': 'Lightweight copy of real DOM for efficient updates', 'difficulty': 'easy', 'points': 5},
            {'question': 'How do you pass data from parent to child component?', 'options': ['Through props', 'Through state', 'Through context only', 'Through refs'], 'correct_answer': 'Through props', 'difficulty': 'easy', 'points': 5},
            {'question': 'What is the correct way to update state?', 'options': ['setState() or useState hook', 'this.state = newState', 'state = newState', 'updateState()'], 'correct_answer': 'setState() or useState hook', 'difficulty': 'easy', 'points': 5},
            {'question': 'What file extension is used for React components?', 'options': ['.jsx or .js', '.react', '.html', '.xml'], 'correct_answer': '.jsx or .js', 'difficulty': 'easy', 'points': 5},
            {'question': 'Which command creates a new React app?', 'options': ['npx create-react-app myapp', 'npm install react-app', 'react new myapp', 'create-react myapp'], 'correct_answer': 'npx create-react-app myapp', 'difficulty': 'easy', 'points': 5},
            
            # Medium (9)
            {'question': 'What is the purpose of useEffect hook?', 'options': ['Handle side effects like data fetching and subscriptions', 'Manage state', 'Create context', 'Define routes'], 'correct_answer': 'Handle side effects like data fetching and subscriptions', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is the difference between controlled and uncontrolled components?', 'options': ['Controlled components have form data handled by React state', 'Uncontrolled are faster', 'Controlled use refs', 'No difference'], 'correct_answer': 'Controlled components have form data handled by React state', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is React Context API used for?', 'options': ['Share data across component tree without prop drilling', 'Style components', 'Handle routing', 'Manage forms'], 'correct_answer': 'Share data across component tree without prop drilling', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is the purpose of useCallback hook?', 'options': ['Memoize callback functions to prevent unnecessary re-renders', 'Call APIs', 'Handle errors', 'Create contexts'], 'correct_answer': 'Memoize callback functions to prevent unnecessary re-renders', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is React.memo()?', 'options': ['Higher-order component for memoizing components', 'A hook', 'A router', 'A state manager'], 'correct_answer': 'Higher-order component for memoizing components', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is the purpose of keys in React lists?', 'options': ['Help React identify which items changed for efficient re-rendering', 'Style list items', 'Sort lists', 'Filter lists'], 'correct_answer': 'Help React identify which items changed for efficient re-rendering', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is React Router used for?', 'options': ['Handle navigation and routing in React apps', 'Manage state', 'Fetch data', 'Style components'], 'correct_answer': 'Handle navigation and routing in React apps', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is the difference between useMemo and useCallback?', 'options': ['useMemo memoizes values, useCallback memoizes functions', 'They are the same', 'useMemo is faster', 'useCallback is deprecated'], 'correct_answer': 'useMemo memoizes values, useCallback memoizes functions', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is prop drilling and how to avoid it?', 'options': ['Passing props through multiple layers; avoid with Context or state management', 'A styling technique', 'An error type', 'A testing method'], 'correct_answer': 'Passing props through multiple layers; avoid with Context or state management', 'difficulty': 'medium', 'points': 10},
            
            # Hard (9)
            {'question': 'What is React Fiber?', 'options': ['New reconciliation algorithm for incremental rendering', 'A styling library', 'A testing framework', 'A router'], 'correct_answer': 'New reconciliation algorithm for incremental rendering', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is the purpose of useReducer hook?', 'options': ['Manage complex state logic with actions and reducers', 'Reduce bundle size', 'Optimize performance', 'Handle errors'], 'correct_answer': 'Manage complex state logic with actions and reducers', 'difficulty': 'hard', 'points': 15},
            {'question': 'What are React Portals?', 'options': ['Render children into DOM node outside parent component hierarchy', 'Component templates', 'State containers', 'Routing mechanisms'], 'correct_answer': 'Render children into DOM node outside parent component hierarchy', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is Server-Side Rendering (SSR) in React?', 'options': ['Render React components on server and send HTML to client', 'Client-only rendering', 'A deployment method', 'A testing technique'], 'correct_answer': 'Render React components on server and send HTML to client', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is code splitting in React?', 'options': ['Lazy load components to reduce initial bundle size', 'Split files manually', 'A design pattern', 'An error handling method'], 'correct_answer': 'Lazy load components to reduce initial bundle size', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is the purpose of forwardRef?', 'options': ['Pass refs through components to child DOM nodes', 'Forward state', 'Forward props', 'Forward events'], 'correct_answer': 'Pass refs through components to child DOM nodes', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is Suspense in React?', 'options': ['Handle loading states for lazy-loaded components', 'Pause execution', 'Error boundary', 'Animation library'], 'correct_answer': 'Handle loading states for lazy-loaded components', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is the difference between useLayoutEffect and useEffect?', 'options': ['useLayoutEffect runs synchronously after DOM mutations, useEffect runs asynchronously', 'They are the same', 'useEffect is faster', 'useLayoutEffect is deprecated'], 'correct_answer': 'useLayoutEffect runs synchronously after DOM mutations, useEffect runs asynchronously', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is Hydration in React?', 'options': ['Attaching event handlers to server-rendered HTML', 'Adding water effects', 'Rehydrating state', 'Compressing components'], 'correct_answer': 'Attaching event handlers to server-rendered HTML', 'difficulty': 'hard', 'points': 15},
        ]

    def get_django_questions(self):
        """30 Django questions"""
        return [
            # Easy (12)
            {'question': 'What is Django primarily used for?', 'options': ['Web development framework', 'Machine learning', 'Mobile app development', 'Data analysis'], 'correct_answer': 'Web development framework', 'difficulty': 'easy', 'points': 5},
            {'question': 'Which command creates a new Django project?', 'options': ['django-admin startproject myproject', 'python manage.py create project', 'django create myproject', 'python django.py startproject'], 'correct_answer': 'django-admin startproject myproject', 'difficulty': 'easy', 'points': 5},
            {'question': 'What is the Django ORM used for?', 'options': ['Database abstraction and query building', 'Object rendering', 'Online resource management', 'Optimization'], 'correct_answer': 'Database abstraction and query building', 'difficulty': 'easy', 'points': 5},
            {'question': 'Which file contains Django settings?', 'options': ['settings.py', 'config.py', 'django.conf', 'setup.py'], 'correct_answer': 'settings.py', 'difficulty': 'easy', 'points': 5},
            {'question': 'What command runs the Django development server?', 'options': ['python manage.py runserver', 'django start', 'python run.py', 'manage.py start'], 'correct_answer': 'python manage.py runserver', 'difficulty': 'easy', 'points': 5},
            {'question': 'What is a Django model?', 'options': ['Python class representing database table', 'A template', 'A view function', 'A URL pattern'], 'correct_answer': 'Python class representing database table', 'difficulty': 'easy', 'points': 5},
            {'question': 'Which template tag is used for loops in Django?', 'options': ['{% for %}', '{{ for }}', '<for>', '@for'], 'correct_answer': '{% for %}', 'difficulty': 'easy', 'points': 5},
            {'question': 'What is Django\'s default database?', 'options': ['SQLite', 'MySQL', 'PostgreSQL', 'MongoDB'], 'correct_answer': 'SQLite', 'difficulty': 'easy', 'points': 5},
            {'question': 'Which command creates database tables from models?', 'options': ['python manage.py migrate', 'python manage.py create_tables', 'django migrate', 'python make_tables.py'], 'correct_answer': 'python manage.py migrate', 'difficulty': 'easy', 'points': 5},
            {'question': 'What is a Django app?', 'options': ['Reusable module within a project', 'The entire project', 'A template', 'A database'], 'correct_answer': 'Reusable module within a project', 'difficulty': 'easy', 'points': 5},
            {'question': 'Which file defines URL patterns in Django?', 'options': ['urls.py', 'routes.py', 'paths.py', 'views.py'], 'correct_answer': 'urls.py', 'difficulty': 'easy', 'points': 5},
            {'question': 'What does MVT stand for in Django?', 'options': ['Model View Template', 'Model View Type', 'Multiple View Templates', 'Model Variable Template'], 'correct_answer': 'Model View Template', 'difficulty': 'easy', 'points': 5},
            
            # Medium (9)
            {'question': 'What is the purpose of Django middleware?', 'options': ['Process requests/responses globally before/after view', 'Store data', 'Render templates', 'Handle URLs'], 'correct_answer': 'Process requests/responses globally before/after view', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is the difference between ForeignKey and ManyToManyField?', 'options': ['ForeignKey is one-to-many, ManyToManyField is many-to-many', 'They are the same', 'ForeignKey is faster', 'ManyToManyField is deprecated'], 'correct_answer': 'ForeignKey is one-to-many, ManyToManyField is many-to-many', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is a Django QuerySet?', 'options': ['Database query result set with lazy evaluation', 'A template set', 'A view collection', 'A URL pattern'], 'correct_answer': 'Database query result set with lazy evaluation', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is the purpose of Django forms?', 'options': ['Handle form rendering, validation, and data processing', 'Create tables', 'Style pages', 'Route URLs'], 'correct_answer': 'Handle form rendering, validation, and data processing', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is the Django admin interface?', 'options': ['Automatic admin panel for model CRUD operations', 'Command line tool', 'Database viewer', 'Testing framework'], 'correct_answer': 'Automatic admin panel for model CRUD operations', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is Django REST framework used for?', 'options': ['Building Web APIs with serialization and authentication', 'Static sites', 'Machine learning', 'Email handling'], 'correct_answer': 'Building Web APIs with serialization and authentication', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is the purpose of django.contrib.auth?', 'options': ['Built-in authentication system with User model', 'Authorization only', 'API authentication', 'OAuth provider'], 'correct_answer': 'Built-in authentication system with User model', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is model inheritance in Django?', 'options': ['Creating models that inherit from other models', 'Template inheritance', 'View inheritance', 'URL inheritance'], 'correct_answer': 'Creating models that inherit from other models', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is the difference between render() and redirect()?', 'options': ['render() returns template response, redirect() returns HTTP redirect', 'They are the same', 'render() is faster', 'redirect() is deprecated'], 'correct_answer': 'render() returns template response, redirect() returns HTTP redirect', 'difficulty': 'medium', 'points': 10},
            
            # Hard (9)
            {'question': 'What is the purpose of select_related() and prefetch_related()?', 'options': ['Optimize database queries by reducing N+1 problem', 'Select models', 'Prefetch data', 'Cache queries'], 'correct_answer': 'Optimize database queries by reducing N+1 problem', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is Django Signals?', 'options': ['Allow decoupled apps to get notified when actions occur', 'Error notifications', 'API webhooks', 'Testing signals'], 'correct_answer': 'Allow decoupled apps to get notified when actions occur', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is the purpose of Django\'s transaction.atomic()?', 'options': ['Execute database operations in atomic transaction', 'Optimize queries', 'Cache data', 'Handle errors'], 'correct_answer': 'Execute database operations in atomic transaction', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is Django Celery used for?', 'options': ['Distributed task queue for asynchronous processing', 'Web server', 'Database', 'Template engine'], 'correct_answer': 'Distributed task queue for asynchronous processing', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is the difference between Q objects and F expressions?', 'options': ['Q for complex queries with OR/AND, F for database-side operations', 'They are the same', 'Q is deprecated', 'F is faster always'], 'correct_answer': 'Q for complex queries with OR/AND, F for database-side operations', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is Django Channels?', 'options': ['Extends Django for WebSockets and async protocols', 'Database channels', 'API channels', 'Template system'], 'correct_answer': 'Extends Django for WebSockets and async protocols', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is the purpose of Django\'s content negotiation?', 'options': ['Return different response formats based on request Accept header', 'Content compression', 'Content caching', 'Content security'], 'correct_answer': 'Return different response formats based on request Accept header', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is Django\'s caching framework used for?', 'options': ['Store expensive computations to avoid repeating them', 'Store files', 'Store sessions', 'Store logs'], 'correct_answer': 'Store expensive computations to avoid repeating them', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is the purpose of custom model managers?', 'options': ['Add custom query methods and modify default QuerySet', 'Manage users', 'Manage files', 'Manage migrations'], 'correct_answer': 'Add custom query methods and modify default QuerySet', 'difficulty': 'hard', 'points': 15},
        ]

    def get_excel_questions(self):
        """30 Excel questions"""
        return [
            # Easy (12)
            {'question': 'Which function finds the average of a range in Excel?', 'options': ['=AVERAGE()', '=AVG()', '=MEAN()', '=AVR()'], 'correct_answer': '=AVERAGE()', 'difficulty': 'easy', 'points': 5},
            {'question': 'What does VLOOKUP stand for?', 'options': ['Vertical Lookup', 'Value Lookup', 'Variable Lookup', 'Vector Lookup'], 'correct_answer': 'Vertical Lookup', 'difficulty': 'easy', 'points': 5},
            {'question': 'Which function adds all values in a range?', 'options': ['=SUM()', '=ADD()', '=TOTAL()', '=PLUS()'], 'correct_answer': '=SUM()', 'difficulty': 'easy', 'points': 5},
            {'question': 'What is the keyboard shortcut to save a workbook?', 'options': ['Ctrl+S', 'Ctrl+W', 'Alt+S', 'F12'], 'correct_answer': 'Ctrl+S', 'difficulty': 'easy', 'points': 5},
            {'question': 'Which function counts cells with numbers?', 'options': ['=COUNT()', '=COUNTNUMBERS()', '=COUNTCELLS()', '=NUM()'], 'correct_answer': '=COUNT()', 'difficulty': 'easy', 'points': 5},
            {'question': 'What does IF function do in Excel?', 'options': ['Performs logical tests and returns values', 'Imports files', 'Formats cells', 'Inserts formulas'], 'correct_answer': 'Performs logical tests and returns values', 'difficulty': 'easy', 'points': 5},
            {'question': 'Which key selects the entire column?', 'options': ['Ctrl+Space', 'Shift+Space', 'Alt+Space', 'Ctrl+A'], 'correct_answer': 'Ctrl+Space', 'difficulty': 'easy', 'points': 5},
            {'question': 'What is the default file extension for Excel 2016+?', 'options': ['.xlsx', '.xls', '.csv', '.xlsm'], 'correct_answer': '.xlsx', 'difficulty': 'easy', 'points': 5},
            {'question': 'Which function returns the largest value?', 'options': ['=MAX()', '=LARGE()', '=BIGGEST()', '=TOP()'], 'correct_answer': '=MAX()', 'difficulty': 'easy', 'points': 5},
            {'question': 'What does Ctrl+C do?', 'options': ['Copy', 'Cut', 'Clear', 'Close'], 'correct_answer': 'Copy', 'difficulty': 'easy', 'points': 5},
            {'question': 'Which function returns current date?', 'options': ['=TODAY()', '=NOW()', '=DATE()', '=CURRENT()'], 'correct_answer': '=TODAY()', 'difficulty': 'easy', 'points': 5},
            {'question': 'What is a cell address?', 'options': ['Column letter + row number (e.g., A1)', 'Row + column', 'Sheet name', 'Workbook name'], 'correct_answer': 'Column letter + row number (e.g., A1)', 'difficulty': 'easy', 'points': 5},
            
            # Medium (9)
            {'question': 'What is the difference between VLOOKUP and HLOOKUP?', 'options': ['VLOOKUP searches vertically, HLOOKUP searches horizontally', 'They are the same', 'VLOOKUP is faster', 'HLOOKUP is deprecated'], 'correct_answer': 'VLOOKUP searches vertically, HLOOKUP searches horizontally', 'difficulty': 'medium', 'points': 10},
            {'question': 'Which function combines text from multiple cells?', 'options': ['=CONCATENATE() or =CONCAT()', '=MERGE()', '=COMBINE()', '=JOIN()'], 'correct_answer': '=CONCATENATE() or =CONCAT()', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is a Pivot Table used for?', 'options': ['Summarize, analyze, and present data', 'Create charts', 'Format cells', 'Print reports'], 'correct_answer': 'Summarize, analyze, and present data', 'difficulty': 'medium', 'points': 10},
            {'question': 'What does the $ symbol do in cell references?', 'options': ['Creates absolute reference (locks cell)', 'Formats as currency', 'Adds dollar sign', 'Creates hyperlink'], 'correct_answer': 'Creates absolute reference (locks cell)', 'difficulty': 'medium', 'points': 10},
            {'question': 'Which function performs approximate match lookup?', 'options': ['=VLOOKUP() with TRUE parameter', '=MATCH()', '=FIND()', '=SEARCH()'], 'correct_answer': '=VLOOKUP() with TRUE parameter', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is conditional formatting?', 'options': ['Format cells based on their values', 'Format entire sheet', 'Format text only', 'Format numbers only'], 'correct_answer': 'Format cells based on their values', 'difficulty': 'medium', 'points': 10},
            {'question': 'Which function returns the position of a value in a range?', 'options': ['=MATCH()', '=FIND()', '=SEARCH()', '=POSITION()'], 'correct_answer': '=MATCH()', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is data validation?', 'options': ['Restrict data entry to specific values/ranges', 'Validate formulas', 'Check spelling', 'Verify calculations'], 'correct_answer': 'Restrict data entry to specific values/ranges', 'difficulty': 'medium', 'points': 10},
            {'question': 'Which function counts non-empty cells?', 'options': ['=COUNTA()', '=COUNT()', '=COUNTIF()', '=COUNTNUMBER()'], 'correct_answer': '=COUNTA()', 'difficulty': 'medium', 'points': 10},
            
            # Hard (9)
            {'question': 'What is the INDEX-MATCH combination used for?', 'options': ['More flexible alternative to VLOOKUP (bidirectional lookup)', 'Index files', 'Match patterns', 'Sort data'], 'correct_answer': 'More flexible alternative to VLOOKUP (bidirectional lookup)', 'difficulty': 'hard', 'points': 15},
            {'question': 'What are array formulas in Excel?', 'options': ['Formulas that perform multiple calculations on arrays (Ctrl+Shift+Enter)', 'Array data structures', 'Multiple sheets', 'Grouped cells'], 'correct_answer': 'Formulas that perform multiple calculations on arrays (Ctrl+Shift+Enter)', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is the purpose of the OFFSET function?', 'options': ['Return reference to a range offset from starting cell', 'Offset time', 'Offset numbers', 'Offset text'], 'correct_answer': 'Return reference to a range offset from starting cell', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is Power Query used for?', 'options': ['ETL operations: Extract, Transform, Load data', 'Create queries', 'Power calculations', 'Query databases'], 'correct_answer': 'ETL operations: Extract, Transform, Load data', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is the difference between SUMIF and SUMIFS?', 'options': ['SUMIF has one condition, SUMIFS has multiple conditions', 'They are the same', 'SUMIF is faster', 'SUMIFS is deprecated'], 'correct_answer': 'SUMIF has one condition, SUMIFS has multiple conditions', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is VBA in Excel?', 'options': ['Visual Basic for Applications - programming macros', 'Visual Basic Application', 'Variable Basic Analysis', 'Version Based Access'], 'correct_answer': 'Visual Basic for Applications - programming macros', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is the purpose of named ranges?', 'options': ['Assign meaningful names to cell references for easier formula writing', 'Name worksheets', 'Name workbooks', 'Name columns'], 'correct_answer': 'Assign meaningful names to cell references for easier formula writing', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is What-If Analysis in Excel?', 'options': ['Tools like Goal Seek, Scenario Manager, Data Tables for forecasting', 'A guessing game', 'Error checking', 'Formula auditing'], 'correct_answer': 'Tools like Goal Seek, Scenario Manager, Data Tables for forecasting', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is the XLOOKUP function (Excel 365)?', 'options': ['Modern replacement for VLOOKUP with more features', 'Extra lookup', 'Excel lookup', 'Extended lookup'], 'correct_answer': 'Modern replacement for VLOOKUP with more features', 'difficulty': 'hard', 'points': 15},
        ]

    def get_numpy_questions(self):
        """30 NumPy questions"""
        return [
            # Easy (12)
            {'question': 'What is NumPy primarily used for?', 'options': ['Numerical computing with arrays', 'Web development', 'Text processing', 'Database management'], 'correct_answer': 'Numerical computing with arrays', 'difficulty': 'easy', 'points': 5},
            {'question': 'How do you import NumPy?', 'options': ['import numpy as np', 'import np', 'from numpy import *', 'using numpy'], 'correct_answer': 'import numpy as np', 'difficulty': 'easy', 'points': 5},
            {'question': 'Which function creates a NumPy array?', 'options': ['np.array()', 'np.create()', 'np.make_array()', 'np.new()'], 'correct_answer': 'np.array()', 'difficulty': 'easy', 'points': 5},
            {'question': 'What is the NumPy data structure called?', 'options': ['ndarray', 'list', 'matrix', 'vector'], 'correct_answer': 'ndarray', 'difficulty': 'easy', 'points': 5},
            {'question': 'Which function creates an array of zeros?', 'options': ['np.zeros()', 'np.empty()', 'np.null()', 'np.zero()'], 'correct_answer': 'np.zeros()', 'difficulty': 'easy', 'points': 5},
            {'question': 'Which function creates an array of ones?', 'options': ['np.ones()', 'np.fills()', 'np.one()', 'np.unit()'], 'correct_answer': 'np.ones()', 'difficulty': 'easy', 'points': 5},
            {'question': 'What does arr.shape return?', 'options': ['Tuple of array dimensions', 'Array size', 'Array type', 'Array values'], 'correct_answer': 'Tuple of array dimensions', 'difficulty': 'easy', 'points': 5},
            {'question': 'Which function creates evenly spaced values?', 'options': ['np.linspace() or np.arange()', 'np.space()', 'np.range()', 'np.even()'], 'correct_answer': 'np.linspace() or np.arange()', 'difficulty': 'easy', 'points': 5},
            {'question': 'What is the result of arr.ndim?', 'options': ['Number of dimensions', 'Array name', 'Array data', 'Array size'], 'correct_answer': 'Number of dimensions', 'difficulty': 'easy', 'points': 5},
            {'question': 'Which function returns the sum of array elements?', 'options': ['np.sum()', 'np.add()', 'np.total()', 'np.plus()'], 'correct_answer': 'np.sum()', 'difficulty': 'easy', 'points': 5},
            {'question': 'What does arr.dtype return?', 'options': ['Data type of array elements', 'Array dimensions', 'Array shape', 'Array size'], 'correct_answer': 'Data type of array elements', 'difficulty': 'easy', 'points': 5},
            {'question': 'Which function creates identity matrix?', 'options': ['np.eye() or np.identity()', 'np.matrix()', 'np.identity_matrix()', 'np.unit()'], 'correct_answer': 'np.eye() or np.identity()', 'difficulty': 'easy', 'points': 5},
            
            # Medium (9)
            {'question': 'What is broadcasting in NumPy?', 'options': ['Automatic array shape alignment for operations', 'Sending data', 'Copying arrays', 'Printing arrays'], 'correct_answer': 'Automatic array shape alignment for operations', 'difficulty': 'medium', 'points': 10},
            {'question': 'What does arr.reshape() do?', 'options': ['Changes array shape without changing data', 'Resizes array', 'Reorders array', 'Removes elements'], 'correct_answer': 'Changes array shape without changing data', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is the difference between np.copy() and view?', 'options': ['copy creates new array, view references original', 'They are the same', 'copy is faster', 'view is deprecated'], 'correct_answer': 'copy creates new array, view references original', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is slicing in NumPy?', 'options': ['Extract subset of array using indices', 'Cut array', 'Split array', 'Delete elements'], 'correct_answer': 'Extract subset of array using indices', 'difficulty': 'medium', 'points': 10},
            {'question': 'What does np.concatenate() do?', 'options': ['Join arrays along existing axis', 'Connect to database', 'Combine strings', 'Merge files'], 'correct_answer': 'Join arrays along existing axis', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is np.where() used for?', 'options': ['Conditional selection returning indices or values', 'Find location', 'Search arrays', 'Filter data'], 'correct_answer': 'Conditional selection returning indices or values', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is the purpose of np.transpose()?', 'options': ['Permute array dimensions (swap axes)', 'Transport data', 'Transform values', 'Transfer arrays'], 'correct_answer': 'Permute array dimensions (swap axes)', 'difficulty': 'medium', 'points': 10},
            {'question': 'What does np.dot() compute?', 'options': ['Dot product or matrix multiplication', 'Decimal point', 'Data points', 'Dot notation'], 'correct_answer': 'Dot product or matrix multiplication', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is fancy indexing?', 'options': ['Array indexing using integer arrays or boolean masks', 'Advanced styling', 'Complex operations', 'Special syntax'], 'correct_answer': 'Array indexing using integer arrays or boolean masks', 'difficulty': 'medium', 'points': 10},
            
            # Hard (9)
            {'question': 'What is the difference between np.array and np.asarray?', 'options': ['asarray avoids copy if input is already array', 'They are the same', 'array is faster', 'asarray is deprecated'], 'correct_answer': 'asarray avoids copy if input is already array', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is vectorization in NumPy?', 'options': ['Replacing explicit loops with array operations for performance', 'Creating vectors', 'Vector graphics', 'Direction calculation'], 'correct_answer': 'Replacing explicit loops with array operations for performance', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is the purpose of np.einsum()?', 'options': ['Efficient Einstein summation notation for tensor operations', 'Sum elements', 'Input function', 'Sum indices'], 'correct_answer': 'Efficient Einstein summation notation for tensor operations', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is striding in NumPy?', 'options': ['Number of bytes to jump to reach next element in each dimension', 'Walking through array', 'Array steps', 'Loop iteration'], 'correct_answer': 'Number of bytes to jump to reach next element in each dimension', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is the difference between np.stack() and np.concatenate()?', 'options': ['stack joins along new axis, concatenate along existing axis', 'They are the same', 'stack is faster', 'concatenate is newer'], 'correct_answer': 'stack joins along new axis, concatenate along existing axis', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is memory layout: C-contiguous vs Fortran-contiguous?', 'options': ['C uses row-major order, Fortran uses column-major order', 'Programming languages', 'Memory types', 'Storage formats'], 'correct_answer': 'C uses row-major order, Fortran uses column-major order', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is np.ufunc?', 'options': ['Universal functions that operate element-wise on arrays', 'User functions', 'Utility functions', 'Undefined functions'], 'correct_answer': 'Universal functions that operate element-wise on arrays', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is the purpose of np.memmap?', 'options': ['Memory-map files for handling large datasets', 'Memory mapping', 'Map data', 'Memory monitor'], 'correct_answer': 'Memory-map files for handling large datasets', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is np.meshgrid() used for?', 'options': ['Create coordinate matrices from coordinate vectors', 'Create mesh', 'Grid layout', 'Mesh networks'], 'correct_answer': 'Create coordinate matrices from coordinate vectors', 'difficulty': 'hard', 'points': 15},
        ]

    def get_pandas_questions(self):
        """30 Pandas questions"""
        return [
            # Easy (12)
            {'question': 'What is Pandas primarily used for?', 'options': ['Data manipulation and analysis', 'Web development', 'Machine learning models', 'Image processing'], 'correct_answer': 'Data manipulation and analysis', 'difficulty': 'easy', 'points': 5},
            {'question': 'How do you import Pandas?', 'options': ['import pandas as pd', 'import pd', 'from pandas import *', 'using pandas'], 'correct_answer': 'import pandas as pd', 'difficulty': 'easy', 'points': 5},
            {'question': 'What are the two main data structures in Pandas?', 'options': ['Series and DataFrame', 'Array and Matrix', 'List and Dict', 'Table and Row'], 'correct_answer': 'Series and DataFrame', 'difficulty': 'easy', 'points': 5},
            {'question': 'Which function reads CSV files in Pandas?', 'options': ['pd.read_csv()', 'pd.load_csv()', 'pd.open_csv()', 'pd.import_csv()'], 'correct_answer': 'pd.read_csv()', 'difficulty': 'easy', 'points': 5},
            {'question': 'What does df.head() do?', 'options': ['Shows first 5 rows', 'Shows column headers', 'Shows last 5 rows', 'Shows row count'], 'correct_answer': 'Shows first 5 rows', 'difficulty': 'easy', 'points': 5},
            {'question': 'Which function shows DataFrame info?', 'options': ['df.info()', 'df.describe()', 'df.summary()', 'df.details()'], 'correct_answer': 'df.info()', 'difficulty': 'easy', 'points': 5},
            {'question': 'How do you select a column in DataFrame?', 'options': ['df["column_name"] or df.column_name', 'df.get("column")', 'df->column', 'df[column]'], 'correct_answer': 'df["column_name"] or df.column_name', 'difficulty': 'easy', 'points': 5},
            {'question': 'What does df.shape return?', 'options': ['(rows, columns) tuple', 'DataFrame size', 'Column names', 'Row indices'], 'correct_answer': '(rows, columns) tuple', 'difficulty': 'easy', 'points': 5},
            {'question': 'Which function removes missing values?', 'options': ['df.dropna()', 'df.remove_na()', 'df.delete_missing()', 'df.clean()'], 'correct_answer': 'df.dropna()', 'difficulty': 'easy', 'points': 5},
            {'question': 'What does df.describe() do?', 'options': ['Shows statistical summary', 'Describes columns', 'Shows data types', 'Prints DataFrame'], 'correct_answer': 'Shows statistical summary', 'difficulty': 'easy', 'points': 5},
            {'question': 'Which function fills missing values?', 'options': ['df.fillna()', 'df.fill_missing()', 'df.replace_na()', 'df.insert()'], 'correct_answer': 'df.fillna()', 'difficulty': 'easy', 'points': 5},
            {'question': 'What does df.columns return?', 'options': ['Column names', 'Column count', 'Column data', 'Column types'], 'correct_answer': 'Column names', 'difficulty': 'easy', 'points': 5},
            
            # Medium (9)
            {'question': 'What is the difference between loc and iloc?', 'options': ['loc uses labels, iloc uses integer positions', 'They are the same', 'loc is faster', 'iloc is deprecated'], 'correct_answer': 'loc uses labels, iloc uses integer positions', 'difficulty': 'medium', 'points': 10},
            {'question': 'What does df.groupby() do?', 'options': ['Groups rows by column values for aggregation', 'Groups columns', 'Groups data types', 'Groups indices'], 'correct_answer': 'Groups rows by column values for aggregation', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is the purpose of df.merge()?', 'options': ['Combine DataFrames like SQL joins', 'Merge cells', 'Merge columns', 'Merge rows'], 'correct_answer': 'Combine DataFrames like SQL joins', 'difficulty': 'medium', 'points': 10},
            {'question': 'What does df.pivot_table() do?', 'options': ['Create spreadsheet-style pivot table', 'Rotate table', 'Change table', 'Pivot rows'], 'correct_answer': 'Create spreadsheet-style pivot table', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is the difference between concat and append?', 'options': ['concat joins multiple DataFrames, append adds rows/columns', 'They are the same', 'concat is faster', 'append is deprecated in newer versions'], 'correct_answer': 'concat joins multiple DataFrames, append adds rows/columns', 'difficulty': 'medium', 'points': 10},
            {'question': 'What does df.apply() do?', 'options': ['Apply function along axis of DataFrame', 'Apply styles', 'Apply filters', 'Apply sorting'], 'correct_answer': 'Apply function along axis of DataFrame', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is a MultiIndex in Pandas?', 'options': ['Hierarchical indexing with multiple index levels', 'Multiple DataFrames', 'Multiple columns', 'Multiple rows'], 'correct_answer': 'Hierarchical indexing with multiple index levels', 'difficulty': 'medium', 'points': 10},
            {'question': 'What does df.melt() do?', 'options': ['Unpivot DataFrame from wide to long format', 'Delete data', 'Merge data', 'Modify data'], 'correct_answer': 'Unpivot DataFrame from wide to long format', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is the purpose of pd.get_dummies()?', 'options': ['Create dummy/indicator variables for categorical data', 'Get sample data', 'Get placeholders', 'Get test data'], 'correct_answer': 'Create dummy/indicator variables for categorical data', 'difficulty': 'medium', 'points': 10},
            
            # Hard (9)
            {'question': 'What is the difference between merge and join?', 'options': ['merge is flexible (column-based), join is index-based by default', 'They are the same', 'merge is faster', 'join is deprecated'], 'correct_answer': 'merge is flexible (column-based), join is index-based by default', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is chaining in Pandas and why avoid it?', 'options': ['Multiple operations in sequence; can cause SettingWithCopyWarning', 'Connecting DataFrames', 'Method calls', 'No issues with chaining'], 'correct_answer': 'Multiple operations in sequence; can cause SettingWithCopyWarning', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is the purpose of pd.Categorical?', 'options': ['Memory-efficient storage for repeated string values', 'Category columns', 'Classification data', 'Column categories'], 'correct_answer': 'Memory-efficient storage for repeated string values', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is vectorization in Pandas?', 'options': ['Using built-in methods instead of loops for performance', 'Creating vectors', 'Vector operations', 'Vector columns'], 'correct_answer': 'Using built-in methods instead of loops for performance', 'difficulty': 'hard', 'points': 15},
            {'question': 'What does df.eval() do?', 'options': ['Evaluate string expressions efficiently using numexpr', 'Evaluate conditions', 'Evaluate columns', 'Evaluate rows'], 'correct_answer': 'Evaluate string expressions efficiently using numexpr', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is the purpose of pd.cut() and pd.qcut()?', 'options': ['cut bins values by intervals, qcut bins by quantiles', 'Cut DataFrames', 'Cut columns', 'Cut rows'], 'correct_answer': 'cut bins values by intervals, qcut bins by quantiles', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is copy-on-write in Pandas?', 'options': ['Memory optimization where copies made only when data modified', 'Copy DataFrames', 'Write data', 'Copy protection'], 'correct_answer': 'Memory optimization where copies made only when data modified', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is the difference between transform and agg in groupby?', 'options': ['transform returns same-sized result, agg returns aggregated result', 'They are the same', 'transform is faster', 'agg is deprecated'], 'correct_answer': 'transform returns same-sized result, agg returns aggregated result', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is pd.crosstab() used for?', 'options': ['Compute cross-tabulation of two or more factors', 'Cross join', 'Tab navigation', 'Cross reference'], 'correct_answer': 'Compute cross-tabulation of two or more factors', 'difficulty': 'hard', 'points': 15},
        ]

    def get_tableau_questions(self):
        """30 Tableau questions"""
        return [
            # Easy (12)
            {'question': 'What type of software is Tableau?', 'options': ['Data visualization tool', 'Programming language', 'Database management system', 'Operating system'], 'correct_answer': 'Data visualization tool', 'difficulty': 'easy', 'points': 5},
            {'question': 'What is a dimension in Tableau?', 'options': ['Categorical data that segments metrics', 'Numerical data', 'A chart type', 'A data source'], 'correct_answer': 'Categorical data that segments metrics', 'difficulty': 'easy', 'points': 5},
            {'question': 'What is a measure in Tableau?', 'options': ['Numerical data for calculations', 'Categorical data', 'A dimension', 'A chart'], 'correct_answer': 'Numerical data for calculations', 'difficulty': 'easy', 'points': 5},
            {'question': 'Which file type is a Tableau workbook?', 'options': ['.twb or .twbx', '.tab', '.xlsx', '.csv'], 'correct_answer': '.twb or .twbx', 'difficulty': 'easy', 'points': 5},
            {'question': 'What is a worksheet in Tableau?', 'options': ['Single view containing visualizations', 'Data source', 'Workbook', 'Dashboard'], 'correct_answer': 'Single view containing visualizations', 'difficulty': 'easy', 'points': 5},
            {'question': 'What is a dashboard in Tableau?', 'options': ['Collection of multiple worksheets', 'Single chart', 'Data table', 'Workbook'], 'correct_answer': 'Collection of multiple worksheets', 'difficulty': 'easy', 'points': 5},
            {'question': 'How do you connect to a data source?', 'options': ['Data menu > Connect to Data', 'File > Import', 'Tools > Connect', 'Edit > Add Data'], 'correct_answer': 'Data menu > Connect to Data', 'difficulty': 'easy', 'points': 5},
            {'question': 'What is Show Me panel used for?', 'options': ['Suggest visualization types', 'Show data', 'Show formulas', 'Show filters'], 'correct_answer': 'Suggest visualization types', 'difficulty': 'easy', 'points': 5},
            {'question': 'Which chart type shows trends over time?', 'options': ['Line chart', 'Pie chart', 'Scatter plot', 'Tree map'], 'correct_answer': 'Line chart', 'difficulty': 'easy', 'points': 5},
            {'question': 'What does Ctrl+D do in Tableau?', 'options': ['Duplicate worksheet', 'Delete worksheet', 'Download data', 'Display data'], 'correct_answer': 'Duplicate worksheet', 'difficulty': 'easy', 'points': 5},
            {'question': 'How do you add a filter?', 'options': ['Drag field to Filters shelf', 'Right-click > Filter', 'Menu > Add Filter', 'Both A and B'], 'correct_answer': 'Both A and B', 'difficulty': 'easy', 'points': 5},
            {'question': 'What is the Data pane?', 'options': ['Shows dimensions and measures', 'Shows charts', 'Shows dashboards', 'Shows formulas'], 'correct_answer': 'Shows dimensions and measures', 'difficulty': 'easy', 'points': 5},
            
            # Medium (9)
            {'question': 'What is a calculated field?', 'options': ['Custom field created using formulas', 'Imported field', 'Dimension field', 'Hidden field'], 'correct_answer': 'Custom field created using formulas', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is the difference between Discrete and Continuous?', 'options': ['Discrete (blue) is categorical, Continuous (green) is quantitative', 'They are the same', 'Discrete is numeric', 'Continuous is text'], 'correct_answer': 'Discrete (blue) is categorical, Continuous (green) is quantitative', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is a parameter in Tableau?', 'options': ['Dynamic value that can replace constant values', 'A data source', 'A worksheet', 'A filter type'], 'correct_answer': 'Dynamic value that can replace constant values', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is a table calculation?', 'options': ['Calculations performed on query results in the view', 'Database calculations', 'Source data calculations', 'Imported calculations'], 'correct_answer': 'Calculations performed on query results in the view', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is blending in Tableau?', 'options': ['Combining data from multiple sources in single view', 'Mixing colors', 'Merging worksheets', 'Combining filters'], 'correct_answer': 'Combining data from multiple sources in single view', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is the difference between JOIN and BLEND?', 'options': ['JOIN combines at data source level, BLEND at worksheet level', 'They are the same', 'JOIN is faster', 'BLEND is deprecated'], 'correct_answer': 'JOIN combines at data source level, BLEND at worksheet level', 'difficulty': 'medium', 'points': 10},
            {'question': 'What are Quick Table Calculations?', 'options': ['Pre-built calculations like Running Total, Percent of Total', 'Fast calculations', 'Simple formulas', 'Automated queries'], 'correct_answer': 'Pre-built calculations like Running Total, Percent of Total', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is a Story in Tableau?', 'options': ['Sequence of visualizations that work together to convey information', 'Data narrative', 'Workbook description', 'Dashboard history'], 'correct_answer': 'Sequence of visualizations that work together to convey information', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is LOD expression?', 'options': ['Level of Detail - control aggregation granularity', 'Load on Demand', 'List of Data', 'Level of Difficulty'], 'correct_answer': 'Level of Detail - control aggregation granularity', 'difficulty': 'medium', 'points': 10},
            
            # Hard (9)
            {'question': 'What are FIXED, INCLUDE, and EXCLUDE LOD expressions?', 'options': ['Control aggregation independent of view level: FIXED ignores filters, INCLUDE/EXCLUDE modify view level', 'Filter types', 'Calculation types', 'Data types'], 'correct_answer': 'Control aggregation independent of view level: FIXED ignores filters, INCLUDE/EXCLUDE modify view level', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is the Order of Operations in Tableau?', 'options': ['Extract Filters > Data Source Filters > Context Filters > Dimension Filters > Measure Filters > Table Calcs', 'Linear order', 'Random order', 'User-defined order'], 'correct_answer': 'Extract Filters > Data Source Filters > Context Filters > Dimension Filters > Measure Filters > Table Calcs', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is a Context Filter?', 'options': ['Filter that creates temporary table to improve performance', 'Background filter', 'Contextual query', 'Filter group'], 'correct_answer': 'Filter that creates temporary table to improve performance', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is data densification?', 'options': ['Adding null values for missing combinations in the data', 'Compressing data', 'Adding more data', 'Removing nulls'], 'correct_answer': 'Adding null values for missing combinations in the data', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is the difference between Data Extract and Live Connection?', 'options': ['Extract is snapshot stored locally, Live queries source in real-time', 'They are the same', 'Extract is slower', 'Live is deprecated'], 'correct_answer': 'Extract is snapshot stored locally, Live queries source in real-time', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is Tableau Prep?', 'options': ['Data preparation tool for cleaning, shaping, and combining data', 'Preparation guide', 'Presentation tool', 'Performance monitor'], 'correct_answer': 'Data preparation tool for cleaning, shaping, and combining data', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is the purpose of Tableau Server?', 'options': ['Share and collaborate on Tableau workbooks across organization', 'Development server', 'Database server', 'Testing server'], 'correct_answer': 'Share and collaborate on Tableau workbooks across organization', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is TabPy?', 'options': ['Tableau Python integration for advanced analytics', 'Python IDE', 'Tableau plugin', 'Python library'], 'correct_answer': 'Tableau Python integration for advanced analytics', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is relationship in Tableau (vs JOIN)?', 'options': ['Flexible connection between tables preserving detail without duplication', 'Foreign key', 'Table link', 'Data merge'], 'correct_answer': 'Flexible connection between tables preserving detail without duplication', 'difficulty': 'hard', 'points': 15},
        ]

    def get_powerbi_questions(self):
        """30 Power BI questions"""
        return [
            # Easy (12)
            {'question': 'What is Power BI primarily used for?', 'options': ['Business intelligence and data visualization', 'Video editing', 'Web development', 'Database administration'], 'correct_answer': 'Business intelligence and data visualization', 'difficulty': 'easy', 'points': 5},
            {'question': 'What is DAX in Power BI?', 'options': ['Data Analysis Expressions - formula language', 'Data Access XML', 'Direct Access Extension', 'Dynamic Analysis Tool'], 'correct_answer': 'Data Analysis Expressions - formula language', 'difficulty': 'easy', 'points': 5},
            {'question': 'What are the main components of Power BI?', 'options': ['Power BI Desktop, Service, Mobile', 'Only Desktop', 'Only Service', 'Only Reports'], 'correct_answer': 'Power BI Desktop, Service, Mobile', 'difficulty': 'easy', 'points': 5},
            {'question': 'Which tool is used to create reports?', 'options': ['Power BI Desktop', 'Power BI Service', 'Excel', 'SQL Server'], 'correct_answer': 'Power BI Desktop', 'difficulty': 'easy', 'points': 5},
            {'question': 'What file format does Power BI Desktop save?', 'options': ['.pbix', '.pbi', '.xlsx', '.pptx'], 'correct_answer': '.pbix', 'difficulty': 'easy', 'points': 5},
            {'question': 'What is Power Query used for?', 'options': ['Data transformation and cleaning', 'Creating visuals', 'Publishing reports', 'User management'], 'correct_answer': 'Data transformation and cleaning', 'difficulty': 'easy', 'points': 5},
            {'question': 'Which view shows table relationships?', 'options': ['Model view', 'Report view', 'Data view', 'Query view'], 'correct_answer': 'Model view', 'difficulty': 'easy', 'points': 5},
            {'question': 'What is a measure in Power BI?', 'options': ['Calculated value using DAX', 'Data column', 'Table name', 'Visual type'], 'correct_answer': 'Calculated value using DAX', 'difficulty': 'easy', 'points': 5},
            {'question': 'How do you publish a report?', 'options': ['Publish button in Power BI Desktop', 'Export to Excel', 'Save as PDF', 'Email file'], 'correct_answer': 'Publish button in Power BI Desktop', 'difficulty': 'easy', 'points': 5},
            {'question': 'What is a dashboard in Power BI?', 'options': ['Single page of pinned visualizations', 'Multi-page report', 'Data model', 'Query'], 'correct_answer': 'Single page of pinned visualizations', 'difficulty': 'easy', 'points': 5},
            {'question': 'Which visual shows KPIs?', 'options': ['Card or KPI visual', 'Table', 'Map', 'Slicer'], 'correct_answer': 'Card or KPI visual', 'difficulty': 'easy', 'points': 5},
            {'question': 'What is a slicer?', 'options': ['Visual filter for other visuals', 'Data connector', 'Table relationship', 'Query step'], 'correct_answer': 'Visual filter for other visuals', 'difficulty': 'easy', 'points': 5},
            
            # Medium (9)
            {'question': 'What is the difference between calculated column and measure?', 'options': ['Calculated column stores per row, measure calculates on aggregation', 'They are the same', 'Column is slower', 'Measure is deprecated'], 'correct_answer': 'Calculated column stores per row, measure calculates on aggregation', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is row context vs filter context?', 'options': ['Row context iterates rows, filter context filters data for calculations', 'They are the same', 'Row is faster', 'Filter is simpler'], 'correct_answer': 'Row context iterates rows, filter context filters data for calculations', 'difficulty': 'medium', 'points': 10},
            {'question': 'What are relationship cardinalities?', 'options': ['One-to-One, One-to-Many, Many-to-Many', 'Single relationships', 'Multiple joins', 'Table links'], 'correct_answer': 'One-to-One, One-to-Many, Many-to-Many', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is CALCULATE() function used for?', 'options': ['Modify filter context for expressions', 'Basic calculations', 'Create columns', 'Load data'], 'correct_answer': 'Modify filter context for expressions', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is Power BI Gateway?', 'options': ['Connect cloud service to on-premises data', 'Security feature', 'Visual type', 'Data source'], 'correct_answer': 'Connect cloud service to on-premises data', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is DirectQuery vs Import mode?', 'options': ['DirectQuery queries source live, Import loads data into model', 'They are the same', 'DirectQuery is faster', 'Import is deprecated'], 'correct_answer': 'DirectQuery queries source live, Import loads data into model', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is a parameter in Power BI?', 'options': ['Variable that can change query or report behavior', 'Fixed value', 'Data column', 'Visual setting'], 'correct_answer': 'Variable that can change query or report behavior', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is RLS (Row-Level Security)?', 'options': ['Filter data based on user viewing report', 'Row locks', 'Report security', 'Service security'], 'correct_answer': 'Filter data based on user viewing report', 'difficulty': 'medium', 'points': 10},
            {'question': 'What are Quick Measures?', 'options': ['Pre-built DAX calculations for common scenarios', 'Fast calculations', 'Instant reports', 'Shortcuts'], 'correct_answer': 'Pre-built DAX calculations for common scenarios', 'difficulty': 'medium', 'points': 10},
            
            # Hard (9)
            {'question': 'What is the difference between RELATED() and RELATEDTABLE()?', 'options': ['RELATED gets one-side value, RELATEDTABLE gets many-side table', 'They are the same', 'RELATED is faster', 'RELATEDTABLE is deprecated'], 'correct_answer': 'RELATED gets one-side value, RELATEDTABLE gets many-side table', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is the evaluation order of CALCULATE()?', 'options': ['Filter arguments evaluated first, then expression in modified context', 'Linear order', 'Random order', 'Expression first'], 'correct_answer': 'Filter arguments evaluated first, then expression in modified context', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is a disconnected table in Power BI?', 'options': ['Table with no relationships used for parameters or what-if analysis', 'Offline table', 'Broken table', 'Hidden table'], 'correct_answer': 'Table with no relationships used for parameters or what-if analysis', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is bidirectional cross-filtering?', 'options': ['Filters flow both directions in relationship', 'Two-way sync', 'Duplicate filters', 'Filter mirroring'], 'correct_answer': 'Filters flow both directions in relationship', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is the SWITCH() function pattern?', 'options': ['Evaluate expression against list of values and return result', 'Change values', 'Toggle settings', 'Switch tables'], 'correct_answer': 'Evaluate expression against list of values and return result', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is a composite model?', 'options': ['Combine Import and DirectQuery tables in one model', 'Multiple models', 'Model template', 'Shared model'], 'correct_answer': 'Combine Import and DirectQuery tables in one model', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is the purpose of CALCULATETABLE()?', 'options': ['Returns modified table rather than scalar value', 'Calculate tables', 'Table calculations', 'Create tables'], 'correct_answer': 'Returns modified table rather than scalar value', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is context transition?', 'options': ['Convert row context to filter context in CALCULATE()', 'Switch contexts', 'Change filters', 'Transition data'], 'correct_answer': 'Convert row context to filter context in CALCULATE()', 'difficulty': 'hard', 'points': 15},
            {'question': 'What are aggregation tables?', 'options': ['Pre-aggregated tables for query performance optimization', 'Summary tables', 'Data grouping', 'Table totals'], 'correct_answer': 'Pre-aggregated tables for query performance optimization', 'difficulty': 'hard', 'points': 15},
        ]

    def get_git_questions(self):
        """30 Git questions"""
        return [
            # Easy (12)
            {'question': 'What is Git primarily used for?', 'options': ['Version control for code', 'Text editing', 'File compression', 'Database management'], 'correct_answer': 'Version control for code', 'difficulty': 'easy', 'points': 5},
            {'question': 'Which command initializes a new Git repository?', 'options': ['git init', 'git start', 'git create', 'git new'], 'correct_answer': 'git init', 'difficulty': 'easy', 'points': 5},
            {'question': 'Which command stages files for commit?', 'options': ['git add', 'git stage', 'git commit', 'git push'], 'correct_answer': 'git add', 'difficulty': 'easy', 'points': 5},
            {'question': 'Which command saves changes to the repository?', 'options': ['git commit', 'git save', 'git push', 'git store'], 'correct_answer': 'git commit', 'difficulty': 'easy', 'points': 5},
            {'question': 'Which command shows the status of the working directory?', 'options': ['git status', 'git check', 'git info', 'git show'], 'correct_answer': 'git status', 'difficulty': 'easy', 'points': 5},
            {'question': 'Which command downloads changes from remote repository?', 'options': ['git pull', 'git download', 'git fetch', 'git get'], 'correct_answer': 'git pull', 'difficulty': 'easy', 'points': 5},
            {'question': 'Which command uploads local commits to remote?', 'options': ['git push', 'git upload', 'git send', 'git commit'], 'correct_answer': 'git push', 'difficulty': 'easy', 'points': 5},
            {'question': 'Which command clones a repository?', 'options': ['git clone', 'git copy', 'git download', 'git get'], 'correct_answer': 'git clone', 'difficulty': 'easy', 'points': 5},
            {'question': 'What file contains files Git should ignore?', 'options': ['.gitignore', '.ignore', 'gitignore.txt', 'ignore.git'], 'correct_answer': '.gitignore', 'difficulty': 'easy', 'points': 5},
            {'question': 'Which command lists all branches?', 'options': ['git branch', 'git list', 'git branches', 'git show'], 'correct_answer': 'git branch', 'difficulty': 'easy', 'points': 5},
            {'question': 'Which command shows commit history?', 'options': ['git log', 'git history', 'git commits', 'git show'], 'correct_answer': 'git log', 'difficulty': 'easy', 'points': 5},
            {'question': 'What is the default branch name in Git?', 'options': ['main or master', 'trunk', 'default', 'primary'], 'correct_answer': 'main or master', 'difficulty': 'easy', 'points': 5},
            
            # Medium (9)
            {'question': 'What is the difference between git fetch and git pull?', 'options': ['fetch downloads changes without merging, pull fetches and merges', 'They are the same', 'fetch is faster', 'pull is deprecated'], 'correct_answer': 'fetch downloads changes without merging, pull fetches and merges', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is a branch in Git?', 'options': ['Pointer to a specific commit for parallel development', 'A copy of repository', 'A remote server', 'A commit'], 'correct_answer': 'Pointer to a specific commit for parallel development', 'difficulty': 'medium', 'points': 10},
            {'question': 'What does git merge do?', 'options': ['Combines changes from different branches', 'Deletes branches', 'Creates branches', 'Uploads changes'], 'correct_answer': 'Combines changes from different branches', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is a merge conflict?', 'options': ['When same file changed differently in branches being merged', 'Network error', 'Permission error', 'Syntax error'], 'correct_answer': 'When same file changed differently in branches being merged', 'difficulty': 'medium', 'points': 10},
            {'question': 'What does git stash do?', 'options': ['Temporarily save uncommitted changes', 'Delete changes', 'Commit changes', 'Push changes'], 'correct_answer': 'Temporarily save uncommitted changes', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is a remote in Git?', 'options': ['Reference to repository hosted on server', 'Local branch', 'Commit message', 'File type'], 'correct_answer': 'Reference to repository hosted on server', 'difficulty': 'medium', 'points': 10},
            {'question': 'What does git checkout do?', 'options': ['Switch branches or restore files', 'Check repository', 'Exit Git', 'Save changes'], 'correct_answer': 'Switch branches or restore files', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is HEAD in Git?', 'options': ['Pointer to current branch/commit', 'First commit', 'Master branch', 'Remote repository'], 'correct_answer': 'Pointer to current branch/commit', 'difficulty': 'medium', 'points': 10},
            {'question': 'What does git reset do?', 'options': ['Undo commits by moving branch pointer', 'Reset password', 'Delete repository', 'Clear history'], 'correct_answer': 'Undo commits by moving branch pointer', 'difficulty': 'medium', 'points': 10},
            
            # Hard (9)
            {'question': 'What is the difference between git reset --soft, --mixed, and --hard?', 'options': ['--soft keeps changes staged, --mixed unstages, --hard discards changes', 'They are the same', '--soft is safest', '--hard is recommended'], 'correct_answer': '--soft keeps changes staged, --mixed unstages, --hard discards changes', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is git rebase?', 'options': ['Reapply commits on top of another base commit', 'Reset database', 'Rebuild repository', 'Refresh branches'], 'correct_answer': 'Reapply commits on top of another base commit', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is the difference between merge and rebase?', 'options': ['Merge preserves history, rebase creates linear history', 'They are the same', 'Merge is faster', 'Rebase is safer'], 'correct_answer': 'Merge preserves history, rebase creates linear history', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is git cherry-pick?', 'options': ['Apply specific commits from one branch to another', 'Select files', 'Choose branches', 'Pick changes'], 'correct_answer': 'Apply specific commits from one branch to another', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is interactive rebase (git rebase -i)?', 'options': ['Modify commit history: squash, reorder, edit commits', 'Interactive merge', 'Command line interface', 'User input mode'], 'correct_answer': 'Modify commit history: squash, reorder, edit commits', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is git reflog?', 'options': ['Reference log showing history of HEAD movements', 'Remote log', 'Error log', 'File log'], 'correct_answer': 'Reference log showing history of HEAD movements', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is a detached HEAD state?', 'options': ['HEAD points to commit instead of branch', 'Broken repository', 'Missing branch', 'Deleted commit'], 'correct_answer': 'HEAD points to commit instead of branch', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is git bisect used for?', 'options': ['Binary search through commits to find bug introduction', 'Split repository', 'Divide branches', 'Section commits'], 'correct_answer': 'Binary search through commits to find bug introduction', 'difficulty': 'hard', 'points': 15},
            {'question': 'What are submodules in Git?', 'options': ['Repositories inside repositories as dependencies', 'Code modules', 'Functions', 'Packages'], 'correct_answer': 'Repositories inside repositories as dependencies', 'difficulty': 'hard', 'points': 15},
        ]
    def get_html_css_questions(self):
        """30 HTML/CSS questions"""
        return [
            # Easy (12)
            {'question': 'What does HTML stand for?', 'options': ['HyperText Markup Language', 'High Tech Modern Language', 'Home Tool Markup Language', 'Hyperlinks and Text Markup Language'], 'correct_answer': 'HyperText Markup Language', 'difficulty': 'easy', 'points': 5},
            {'question': 'Which tag creates a paragraph?', 'options': ['<p>', '<para>', '<paragraph>', '<text>'], 'correct_answer': '<p>', 'difficulty': 'easy', 'points': 5},
            {'question': 'Which tag creates a hyperlink?', 'options': ['<a>', '<link>', '<href>', '<url>'], 'correct_answer': '<a>', 'difficulty': 'easy', 'points': 5},
            {'question': 'What does CSS stand for?', 'options': ['Cascading Style Sheets', 'Creative Style Sheets', 'Computer Style Sheets', 'Colorful Style Sheets'], 'correct_answer': 'Cascading Style Sheets', 'difficulty': 'easy', 'points': 5},
            {'question': 'Which HTML tag defines the title of a document?', 'options': ['<title>', '<head>', '<meta>', '<header>'], 'correct_answer': '<title>', 'difficulty': 'easy', 'points': 5},
            {'question': 'Which CSS property changes the text color?', 'options': ['color', 'text-color', 'font-color', 'text'], 'correct_answer': 'color', 'difficulty': 'easy', 'points': 5},
            {'question': 'Which tag creates an unordered list?', 'options': ['<ul>', '<ol>', '<list>', '<li>'], 'correct_answer': '<ul>', 'difficulty': 'easy', 'points': 5},
            {'question': 'What is the correct HTML for inserting an image?', 'options': ['<img src="image.jpg">', '<image src="image.jpg">', '<img>image.jpg</img>', '<picture src="image.jpg">'], 'correct_answer': '<img src="image.jpg">', 'difficulty': 'easy', 'points': 5},
            {'question': 'Which CSS property controls the text size?', 'options': ['font-size', 'text-size', 'font-style', 'text-style'], 'correct_answer': 'font-size', 'difficulty': 'easy', 'points': 5},
            {'question': 'How do you add a comment in HTML?', 'options': ['<!-- comment -->', '// comment', '/* comment */', '# comment'], 'correct_answer': '<!-- comment -->', 'difficulty': 'easy', 'points': 5},
            {'question': 'Which attribute specifies a unique id for an element?', 'options': ['id', 'class', 'name', 'key'], 'correct_answer': 'id', 'difficulty': 'easy', 'points': 5},
            {'question': 'Which HTML tag creates a line break?', 'options': ['<br>', '<break>', '<lb>', '<newline>'], 'correct_answer': '<br>', 'difficulty': 'easy', 'points': 5},
            
            # Medium (9)
            {'question': 'What is the CSS Box Model?', 'options': ['Content, Padding, Border, Margin', 'Width and Height only', 'Display properties', 'Position properties'], 'correct_answer': 'Content, Padding, Border, Margin', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is the difference between class and id selectors?', 'options': ['id must be unique, class can be reused', 'They are the same', 'id is faster', 'class is deprecated'], 'correct_answer': 'id must be unique, class can be reused', 'difficulty': 'medium', 'points': 10},
            {'question': 'What does display: flex do?', 'options': ['Creates flexible layout container', 'Makes element flexible', 'Flexes content', 'Displays flexibly'], 'correct_answer': 'Creates flexible layout container', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is the purpose of semantic HTML?', 'options': ['Give meaning to content for accessibility and SEO', 'Make HTML shorter', 'Style elements', 'Add JavaScript'], 'correct_answer': 'Give meaning to content for accessibility and SEO', 'difficulty': 'medium', 'points': 10},
            {'question': 'What does position: relative do?', 'options': ['Position element relative to its normal position', 'Position relative to parent', 'Position relative to viewport', 'Relative positioning is deprecated'], 'correct_answer': 'Position element relative to its normal position', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is the difference between inline and block elements?', 'options': ['inline flows with text, block starts new line and takes full width', 'They are the same', 'inline is faster', 'block is deprecated'], 'correct_answer': 'inline flows with text, block starts new line and takes full width', 'difficulty': 'medium', 'points': 10},
            {'question': 'What are pseudo-classes in CSS?', 'options': ['Define special states like :hover, :active, :focus', 'False classes', 'Fake CSS', 'Pseudo elements'], 'correct_answer': 'Define special states like :hover, :active, :focus', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is the z-index property?', 'options': ['Controls stacking order of positioned elements', 'Index page', 'Z-axis position', 'Zero index'], 'correct_answer': 'Controls stacking order of positioned elements', 'difficulty': 'medium', 'points': 10},
            {'question': 'What does the viewport meta tag do?', 'options': ['Control layout on mobile browsers for responsive design', 'View port numbers', 'Create viewports', 'Tag views'], 'correct_answer': 'Control layout on mobile browsers for responsive design', 'difficulty': 'medium', 'points': 10},
            
            # Hard (9)
            {'question': 'What is CSS Grid Layout?', 'options': ['2D layout system with rows and columns', 'Simple grid lines', 'Table layout', 'Deprecated layout'], 'correct_answer': '2D layout system with rows and columns', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is the difference between Grid and Flexbox?', 'options': ['Grid is 2D (rows & columns), Flexbox is 1D (row or column)', 'They are the same', 'Grid is older', 'Flexbox is faster'], 'correct_answer': 'Grid is 2D (rows & columns), Flexbox is 1D (row or column)', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is CSS specificity?', 'options': ['Rules determining which style applies when multiple selectors match', 'Specific styling', 'CSS version', 'Performance metric'], 'correct_answer': 'Rules determining which style applies when multiple selectors match', 'difficulty': 'hard', 'points': 15},
            {'question': 'What are CSS custom properties (variables)?', 'options': ['Reusable values defined with -- and used with var()', 'Custom CSS', 'Variable fonts', 'Property types'], 'correct_answer': 'Reusable values defined with -- and used with var()', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is the BEM methodology?', 'options': ['Block Element Modifier - CSS naming convention', 'Browser Element Model', 'Best Element Method', 'Basic Element Markup'], 'correct_answer': 'Block Element Modifier - CSS naming convention', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is the Critical Rendering Path?', 'options': ['Sequence of steps browser takes to render page', 'Important CSS path', 'Render errors', 'Critical bugs'], 'correct_answer': 'Sequence of steps browser takes to render page', 'difficulty': 'hard', 'points': 15},
            {'question': 'What are CSS preprocessors like SASS/LESS?', 'options': ['Extend CSS with variables, nesting, mixins that compile to CSS', 'CSS alternatives', 'CSS validators', 'CSS frameworks'], 'correct_answer': 'Extend CSS with variables, nesting, mixins that compile to CSS', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is the purpose of will-change CSS property?', 'options': ['Hint browser about upcoming changes for optimization', 'Change properties', 'Future CSS', 'Change detection'], 'correct_answer': 'Hint browser about upcoming changes for optimization', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is progressive enhancement?', 'options': ['Build basic functionality first, then enhance for capable browsers', 'Gradual updates', 'Performance boost', 'Enhanced CSS'], 'correct_answer': 'Build basic functionality first, then enhance for capable browsers', 'difficulty': 'hard', 'points': 15},
        ]

    def get_java_questions(self):
        """30 Java questions"""
        return [
            # Easy (12)
            {'question': 'What is Java?', 'options': ['Object-oriented programming language', 'JavaScript library', 'Web framework', 'Database'], 'correct_answer': 'Object-oriented programming language', 'difficulty': 'easy', 'points': 5},
            {'question': 'Which keyword is used to create a class?', 'options': ['class', 'Class', 'new', 'create'], 'correct_answer': 'class', 'difficulty': 'easy', 'points': 5},
            {'question': 'What is the main method signature?', 'options': ['public static void main(String[] args)', 'void main()', 'static main()', 'public main()'], 'correct_answer': 'public static void main(String[] args)', 'difficulty': 'easy', 'points': 5},
            {'question': 'How do you print text in Java?', 'options': ['System.out.println()', 'print()', 'console.log()', 'echo()'], 'correct_answer': 'System.out.println()', 'difficulty': 'easy', 'points': 5},
            {'question': 'Which keyword is used for inheritance?', 'options': ['extends', 'inherits', 'implements', 'inherit'], 'correct_answer': 'extends', 'difficulty': 'easy', 'points': 5},
            {'question': 'What is the default value of int?', 'options': ['0', 'null', 'undefined', '1'], 'correct_answer': '0', 'difficulty': 'easy', 'points': 5},
            {'question': 'How do you create an object?', 'options': ['ClassName obj = new ClassName()', 'obj = ClassName()', 'ClassName obj', 'new obj ClassName'], 'correct_answer': 'ClassName obj = new ClassName()', 'difficulty': 'easy', 'points': 5},
            {'question': 'Which access modifier makes a member accessible everywhere?', 'options': ['public', 'private', 'protected', 'default'], 'correct_answer': 'public', 'difficulty': 'easy', 'points': 5},
            {'question': 'What file extension is used for Java?', 'options': ['.java', '.class', '.jar', '.jv'], 'correct_answer': '.java', 'difficulty': 'easy', 'points': 5},
            {'question': 'What is JVM?', 'options': ['Java Virtual Machine', 'Java Version Manager', 'Java Variable Method', 'Java Value Machine'], 'correct_answer': 'Java Virtual Machine', 'difficulty': 'easy', 'points': 5},
            {'question': 'Which keyword is used to define constants?', 'options': ['final', 'const', 'constant', 'static'], 'correct_answer': 'final', 'difficulty': 'easy', 'points': 5},
            {'question': 'What is a constructor?', 'options': ['Special method to initialize objects', 'Class destructor', 'Method builder', 'Object destroyer'], 'correct_answer': 'Special method to initialize objects', 'difficulty': 'easy', 'points': 5},
            
            # Medium (9)
            {'question': 'What is method overloading?', 'options': ['Multiple methods with same name but different parameters', 'Method overriding', 'Method error', 'Method duplication'], 'correct_answer': 'Multiple methods with same name but different parameters', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is the difference between == and .equals()?', 'options': ['== compares references, .equals() compares content', 'They are the same', '== is faster', '.equals() is deprecated'], 'correct_answer': '== compares references, .equals() compares content', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is polymorphism?', 'options': ['Objects of different types accessed through same interface', 'Multiple forms', 'Class morphing', 'Type changing'], 'correct_answer': 'Objects of different types accessed through same interface', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is an interface in Java?', 'options': ['Abstract type with method signatures that classes can implement', 'GUI component', 'Class type', 'Connection point'], 'correct_answer': 'Abstract type with method signatures that classes can implement', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is the purpose of try-catch?', 'options': ['Exception handling to catch and handle errors', 'Test code', 'Catch variables', 'Try methods'], 'correct_answer': 'Exception handling to catch and handle errors', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is the difference between abstract class and interface?', 'options': ['Abstract class can have implementation, interface only declares methods (Java <8)', 'They are the same', 'Interface is faster', 'Abstract is deprecated'], 'correct_answer': 'Abstract class can have implementation, interface only declares methods (Java <8)', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is a static method?', 'options': ['Method belonging to class, not instance', 'Non-changing method', 'Stationary method', 'Constant method'], 'correct_answer': 'Method belonging to class, not instance', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is the Collections Framework?', 'options': ['Unified architecture for representing and manipulating collections', 'Framework for collecting data', 'Collection classes', 'Data structures'], 'correct_answer': 'Unified architecture for representing and manipulating collections', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is generics in Java?', 'options': ['Type parameters for compile-time type safety', 'General methods', 'Generic classes', 'Common functions'], 'correct_answer': 'Type parameters for compile-time type safety', 'difficulty': 'medium', 'points': 10},
            
            # Hard (9)
            {'question': 'What is the difference between ArrayList and LinkedList?', 'options': ['ArrayList uses dynamic array, LinkedList uses doubly-linked list', 'They are the same', 'ArrayList is always faster', 'LinkedList is deprecated'], 'correct_answer': 'ArrayList uses dynamic array, LinkedList uses doubly-linked list', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is the Java Memory Model?', 'options': ['Defines how threads interact through memory', 'Memory size', 'RAM usage', 'Storage model'], 'correct_answer': 'Defines how threads interact through memory', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is garbage collection?', 'options': ['Automatic memory management by reclaiming unused objects', 'Delete objects', 'Clean code', 'Remove errors'], 'correct_answer': 'Automatic memory management by reclaiming unused objects', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is reflection in Java?', 'options': ['Inspect and manipulate classes, methods, fields at runtime', 'Mirror objects', 'Reflect changes', 'Object copying'], 'correct_answer': 'Inspect and manipulate classes, methods, fields at runtime', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is the synchronized keyword?', 'options': ['Control thread access to shared resources', 'Sync data', 'Synchronize methods', 'Match threads'], 'correct_answer': 'Control thread access to shared resources', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is a lambda expression?', 'options': ['Anonymous function for functional programming (Java 8+)', 'Lambda calculus', 'Greek function', 'Expression type'], 'correct_answer': 'Anonymous function for functional programming (Java 8+)', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is the Stream API?', 'options': ['Functional-style operations on collections (Java 8+)', 'Data streams', 'Input/output', 'Streaming data'], 'correct_answer': 'Functional-style operations on collections (Java 8+)', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is the difference between Comparable and Comparator?', 'options': ['Comparable defines natural order in class, Comparator defines custom external order', 'They are the same', 'Comparable is faster', 'Comparator is deprecated'], 'correct_answer': 'Comparable defines natural order in class, Comparator defines custom external order', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is the volatile keyword?', 'options': ['Ensures visibility of changes across threads', 'Volatile variable', 'Changeable variable', 'Unstable data'], 'correct_answer': 'Ensures visibility of changes across threads', 'difficulty': 'hard', 'points': 15},
        ]

    def get_cpp_questions(self):
        """30 C++ questions - return empty for now, can be added later"""
        return []

    def get_typescript_questions(self):
        """30 TypeScript questions - return empty for now, can be added later"""
        return []

    def get_rest_apis_questions(self):
        """30 REST API questions - return empty for now, can be added later"""
        return []

    def get_docker_questions(self):
        """30 Docker questions - return empty for now, can be added later"""
        return []

    def get_aws_questions(self):
        """30 AWS questions - return empty for now, can be added later"""
        return []

    def get_hadoop_questions(self):
        """30 Hadoop questions"""
        return [
            # Easy (12)
            {'question': 'What is Hadoop?', 'options': ['Distributed data processing framework', 'Database', 'Programming language', 'Operating system'], 'correct_answer': 'Distributed data processing framework', 'difficulty': 'easy', 'points': 5},
            {'question': 'What does HDFS stand for?', 'options': ['Hadoop Distributed File System', 'High Data File System', 'Hadoop Data Format System', 'Hard Disk File System'], 'correct_answer': 'Hadoop Distributed File System', 'difficulty': 'easy', 'points': 5},
            {'question': 'What is MapReduce?', 'options': ['Programming model for processing large datasets', 'Map data structure', 'Reduce function', 'Database query'], 'correct_answer': 'Programming model for processing large datasets', 'difficulty': 'easy', 'points': 5},
            {'question': 'What is the default replication factor in HDFS?', 'options': ['3', '1', '2', '5'], 'correct_answer': '3', 'difficulty': 'easy', 'points': 5},
            {'question': 'Which component stores metadata in Hadoop?', 'options': ['NameNode', 'DataNode', 'JobTracker', 'TaskTracker'], 'correct_answer': 'NameNode', 'difficulty': 'easy', 'points': 5},
            {'question': 'What language is Hadoop primarily written in?', 'options': ['Java', 'Python', 'C++', 'Scala'], 'correct_answer': 'Java', 'difficulty': 'easy', 'points': 5},
            {'question': 'What is YARN in Hadoop?', 'options': ['Yet Another Resource Negotiator - resource management', 'Data storage', 'Query language', 'Security module'], 'correct_answer': 'Yet Another Resource Negotiator - resource management', 'difficulty': 'easy', 'points': 5},
            {'question': 'What is the default block size in HDFS (Hadoop 2.x)?', 'options': ['128 MB', '64 MB', '256 MB', '512 MB'], 'correct_answer': '128 MB', 'difficulty': 'easy', 'points': 5},
            {'question': 'Which node stores actual data?', 'options': ['DataNode', 'NameNode', 'ResourceManager', 'NodeManager'], 'correct_answer': 'DataNode', 'difficulty': 'easy', 'points': 5},
            {'question': 'What is Hive?', 'options': ['Data warehouse system for SQL-like queries', 'Messaging system', 'Machine learning library', 'Web framework'], 'correct_answer': 'Data warehouse system for SQL-like queries', 'difficulty': 'easy', 'points': 5},
            {'question': 'What command lists files in HDFS?', 'options': ['hadoop fs -ls', 'hdfs list', 'hadoop list', 'fs -ls'], 'correct_answer': 'hadoop fs -ls', 'difficulty': 'easy', 'points': 5},
            {'question': 'What is Pig in Hadoop ecosystem?', 'options': ['High-level platform for data analysis', 'Data storage', 'Security tool', 'Monitoring tool'], 'correct_answer': 'High-level platform for data analysis', 'difficulty': 'easy', 'points': 5},
            
            # Medium (9)
            {'question': 'What is the difference between NameNode and Secondary NameNode?', 'options': ['Secondary NameNode performs checkpointing of metadata, not a backup', 'They are the same', 'Secondary is backup', 'Secondary handles data'], 'correct_answer': 'Secondary NameNode performs checkpointing of metadata, not a backup', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is speculative execution in MapReduce?', 'options': ['Launching duplicate tasks when one is slow', 'Predicting results', 'Planning execution', 'Optimizing queries'], 'correct_answer': 'Launching duplicate tasks when one is slow', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is the purpose of Combiner in MapReduce?', 'options': ['Mini-reducer that reduces data before sending to reducer', 'Combines files', 'Joins data', 'Merges results'], 'correct_answer': 'Mini-reducer that reduces data before sending to reducer', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is rack awareness in Hadoop?', 'options': ['Knowledge of DataNode locations for optimal replica placement', 'Server rack management', 'Network topology', 'Storage awareness'], 'correct_answer': 'Knowledge of DataNode locations for optimal replica placement', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is HBase?', 'options': ['NoSQL distributed database built on top of HDFS', 'SQL database', 'File system', 'Query engine'], 'correct_answer': 'NoSQL distributed database built on top of HDFS', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is Partitioner in MapReduce?', 'options': ['Determines which reducer receives which key-value pairs', 'Partitions data', 'Splits files', 'Creates partitions'], 'correct_answer': 'Determines which reducer receives which key-value pairs', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is the difference between HDFS and traditional file systems?', 'options': ['HDFS is distributed across multiple machines with data replication', 'They are the same', 'HDFS is faster', 'HDFS is centralized'], 'correct_answer': 'HDFS is distributed across multiple machines with data replication', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is InputFormat in MapReduce?', 'options': ['Defines how input data is read and split into input splits', 'Data format', 'Input validation', 'File format'], 'correct_answer': 'Defines how input data is read and split into input splits', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is Sqoop used for?', 'options': ['Transfer data between Hadoop and relational databases', 'Query data', 'Scope data', 'Scoop files'], 'correct_answer': 'Transfer data between Hadoop and relational databases', 'difficulty': 'medium', 'points': 10},
            
            # Hard (9)
            {'question': 'What is HDFS Federation?', 'options': ['Multiple independent NameNodes for scalability', 'Data federation', 'Network federation', 'Cluster federation'], 'correct_answer': 'Multiple independent NameNodes for scalability', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is the difference between MapReduce 1 and MapReduce 2 (YARN)?', 'options': ['YARN separates resource management from job scheduling/monitoring', 'They are the same', 'YARN is faster', 'YARN is simpler'], 'correct_answer': 'YARN separates resource management from job scheduling/monitoring', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is ZooKeeper in Hadoop ecosystem?', 'options': ['Distributed coordination service for managing cluster state', 'Data storage', 'Query processor', 'Security manager'], 'correct_answer': 'Distributed coordination service for managing cluster state', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is the purpose of Oozie?', 'options': ['Workflow scheduler for managing Hadoop jobs', 'Data loader', 'Query optimizer', 'Security tool'], 'correct_answer': 'Workflow scheduler for managing Hadoop jobs', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is small file problem in HDFS?', 'options': ['Many small files create excessive NameNode memory usage', 'Files are too small', 'Storage waste', 'Performance issue'], 'correct_answer': 'Many small files create excessive NameNode memory usage', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is the difference between Hive and HBase?', 'options': ['Hive is SQL-like batch processing, HBase is real-time NoSQL database', 'They are the same', 'Hive is faster', 'HBase is simpler'], 'correct_answer': 'Hive is SQL-like batch processing, HBase is real-time NoSQL database', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is erasure coding in HDFS?', 'options': ['Storage optimization technique replacing replication for cold data', 'Error correction', 'Data encryption', 'Compression method'], 'correct_answer': 'Storage optimization technique replacing replication for cold data', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is the purpose of DistCp?', 'options': ['Distributed copy tool for large inter/intra-cluster data transfers', 'File compression', 'Data distribution', 'Copy command'], 'correct_answer': 'Distributed copy tool for large inter/intra-cluster data transfers', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is High Availability in Hadoop?', 'options': ['Active-Standby NameNode configuration to avoid single point of failure', 'High performance', 'High security', 'High storage'], 'correct_answer': 'Active-Standby NameNode configuration to avoid single point of failure', 'difficulty': 'hard', 'points': 15},
        ]
    
    def get_cpp_questions(self):
        """C++ questions covering OOP, memory management, templates, STL"""
        return [
            # Easy (12)
            {'question': 'What is the output of cout << "Hello" << endl;?', 'options': ['Prints Hello with newline', 'Syntax error', 'Prints Hello without newline', 'Compilation error'], 'correct_answer': 'Prints Hello with newline', 'difficulty': 'easy', 'points': 5},
            {'question': 'Which operator is used to access members of a class through a pointer?', 'options': ['->', '.', '::', '&'], 'correct_answer': '->', 'difficulty': 'easy', 'points': 5},
            {'question': 'What is the correct way to declare a pointer in C++?', 'options': ['int *ptr;', 'int ptr*;', 'pointer int ptr;', 'int &ptr;'], 'correct_answer': 'int *ptr;', 'difficulty': 'easy', 'points': 5},
            {'question': 'Which header file is required for cout and cin?', 'options': ['iostream', 'stdio.h', 'conio.h', 'iostream.h'], 'correct_answer': 'iostream', 'difficulty': 'easy', 'points': 5},
            {'question': 'What is the access specifier for class members by default?', 'options': ['private', 'public', 'protected', 'default'], 'correct_answer': 'private', 'difficulty': 'easy', 'points': 5},
            {'question': 'Which keyword is used to inherit a class in C++?', 'options': [':', 'extends', 'inherits', 'implements'], 'correct_answer': ':', 'difficulty': 'easy', 'points': 5},
            {'question': 'What is the size of bool in C++?', 'options': ['1 byte', '2 bytes', '4 bytes', 'depends on compiler'], 'correct_answer': '1 byte', 'difficulty': 'easy', 'points': 5},
            {'question': 'Which loop is guaranteed to execute at least once?', 'options': ['do-while', 'while', 'for', 'foreach'], 'correct_answer': 'do-while', 'difficulty': 'easy', 'points': 5},
            {'question': 'What is the correct way to declare a reference in C++?', 'options': ['int &ref = var;', 'int *ref = var;', 'ref int = var;', 'int ref& = var;'], 'correct_answer': 'int &ref = var;', 'difficulty': 'easy', 'points': 5},
            {'question': 'Which operator cannot be overloaded in C++?', 'options': ['::', '==', '[]', '->'], 'correct_answer': '::', 'difficulty': 'easy', 'points': 5},
            {'question': 'What is the extension of C++ source files?', 'options': ['.cpp', '.c', '.cxx', '.cc (all are valid)'], 'correct_answer': '.cpp', 'difficulty': 'easy', 'points': 5},
            {'question': 'What is the purpose of namespace std?', 'options': ['Contains standard library components', 'Defines classes', 'Manages memory', 'Handles errors'], 'correct_answer': 'Contains standard library components', 'difficulty': 'easy', 'points': 5},
            
            # Medium (9)
            {'question': 'What is the difference between struct and class in C++?', 'options': ['struct members are public by default, class members are private', 'No difference', 'struct is faster', 'class supports inheritance'], 'correct_answer': 'struct members are public by default, class members are private', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is RAII in C++?', 'options': ['Resource Acquisition Is Initialization - resource management idiom', 'Resource Allocation Interface', 'Runtime Array Initialization', 'Reference And Inheritance Implementation'], 'correct_answer': 'Resource Acquisition Is Initialization - resource management idiom', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is the purpose of virtual destructor?', 'options': ['Ensures proper cleanup in polymorphic inheritance hierarchies', 'Makes destructor faster', 'Prevents memory leaks', 'Makes class abstract'], 'correct_answer': 'Ensures proper cleanup in polymorphic inheritance hierarchies', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is the rule of three in C++?', 'options': ['If you define copy constructor, copy assignment, or destructor, define all three', 'Three virtual functions', 'Three access specifiers', 'Three inheritance types'], 'correct_answer': 'If you define copy constructor, copy assignment, or destructor, define all three', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is the difference between new and malloc?', 'options': ['new calls constructor, malloc does not', 'No difference', 'malloc is faster', 'new is C function'], 'correct_answer': 'new calls constructor, malloc does not', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is function overloading?', 'options': ['Multiple functions with same name but different parameters', 'Overriding base class function', 'Using too many functions', 'Virtual function'], 'correct_answer': 'Multiple functions with same name but different parameters', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is a const member function?', 'options': ['Function that cannot modify member variables', 'Constant function', 'Static function', 'Final function'], 'correct_answer': 'Function that cannot modify member variables', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is the purpose of friend function?', 'options': ['Allows non-member function to access private members', 'Makes function faster', 'Creates friendship between classes', 'Public function'], 'correct_answer': 'Allows non-member function to access private members', 'difficulty': 'medium', 'points': 10},
            {'question': 'What is difference between pass by value and pass by reference?', 'options': ['Pass by value copies data, pass by reference passes address', 'No difference', 'Pass by value is faster', 'Pass by reference copies data'], 'correct_answer': 'Pass by value copies data, pass by reference passes address', 'difficulty': 'medium', 'points': 10},
            
            # Hard (9)
            {'question': 'What is move semantics in C++11?', 'options': ['Efficient transfer of resources from temporary objects without copying', 'Moving objects in memory', 'Memory optimization', 'Pointer arithmetic'], 'correct_answer': 'Efficient transfer of resources from temporary objects without copying', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is the difference between shallow copy and deep copy?', 'options': ['Shallow copies pointers, deep copy duplicates pointed-to data', 'No difference', 'Shallow is faster', 'Deep copy is automatic'], 'correct_answer': 'Shallow copies pointers, deep copy duplicates pointed-to data', 'difficulty': 'hard', 'points': 15},
            {'question': 'What are template specializations?', 'options': ['Providing specific implementations for certain template types', 'Template optimization', 'Generic programming', 'Inheritance'], 'correct_answer': 'Providing specific implementations for certain template types', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is SFINAE in C++ template metaprogramming?', 'options': ['Substitution Failure Is Not An Error - template resolution technique', 'Syntax error', 'Function overloading', 'Inheritance pattern'], 'correct_answer': 'Substitution Failure Is Not An Error - template resolution technique', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is the difference between static_cast and dynamic_cast?', 'options': ['static_cast is compile-time, dynamic_cast performs runtime type checking', 'No difference', 'static_cast is safer', 'dynamic_cast is faster'], 'correct_answer': 'static_cast is compile-time, dynamic_cast performs runtime type checking', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is std::unique_ptr?', 'options': ['Smart pointer with exclusive ownership and automatic deletion', 'Pointer to unique objects', 'Shared pointer', 'Raw pointer wrapper'], 'correct_answer': 'Smart pointer with exclusive ownership and automatic deletion', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is perfect forwarding in C++11?', 'options': ['Preserving value category when forwarding template arguments', 'Fast forwarding', 'Reference forwarding', 'Function forwarding'], 'correct_answer': 'Preserving value category when forwarding template arguments', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is the purpose of constexpr?', 'options': ['Specifies that value can be evaluated at compile-time', 'Constant expression', 'Inline function', 'Template parameter'], 'correct_answer': 'Specifies that value can be evaluated at compile-time', 'difficulty': 'hard', 'points': 15},
            {'question': 'What is std::vector memory growth strategy?', 'options': ['Geometric growth (typically 1.5x or 2x) when capacity exceeded', 'Linear growth', 'Fixed size', 'On-demand allocation'], 'correct_answer': 'Geometric growth (typically 1.5x or 2x) when capacity exceeded', 'difficulty': 'hard', 'points': 15},
        ]