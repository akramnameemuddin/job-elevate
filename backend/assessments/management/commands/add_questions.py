"""
Management command to add sample questions to existing skills
"""
from django.core.management.base import BaseCommand
from assessments.models import Skill, QuestionBank


class Command(BaseCommand):
    help = 'Adds sample questions to existing skills'

    def handle(self, *args, **kwargs):
        self.stdout.write('Adding questions to existing skills...')
        
        # Map skill names to questions
        skill_questions = {
            'Python': [
                # Easy questions (8 needed)
                {'question': 'What is the output of: print(type([]))?', 'options': ["<class 'list'>", "<class 'array'>", "<class 'tuple'>", "<class 'dict'>"], 'correct': "<class 'list'>", 'difficulty': 'easy', 'points': 5},
                {'question': 'Which keyword is used to define a function in Python?', 'options': ['function', 'def', 'func', 'define'], 'correct': 'def', 'difficulty': 'easy', 'points': 5},
                {'question': 'What does the len() function do?', 'options': ['Returns length of object', 'Converts to lowercase', 'Returns type', 'Checks if empty'], 'correct': 'Returns length of object', 'difficulty': 'easy', 'points': 5},
                {'question': 'Which of these is a valid variable name?', 'options': ['my_var', '2var', 'var-name', 'var name'], 'correct': 'my_var', 'difficulty': 'easy', 'points': 5},
                {'question': 'What is the correct way to create a list?', 'options': ['[]', '{}', '()', '<>'], 'correct': '[]', 'difficulty': 'easy', 'points': 5},
                {'question': 'Which operator is used for exponentiation?', 'options': ['**', '^', 'exp', 'pow'], 'correct': '**', 'difficulty': 'easy', 'points': 5},
                {'question': 'What does print() function do?', 'options': ['Displays output', 'Returns value', 'Calculates result', 'Stores data'], 'correct': 'Displays output', 'difficulty': 'easy', 'points': 5},
                {'question': 'Which is the correct file extension for Python?', 'options': ['.py', '.python', '.pt', '.pyt'], 'correct': '.py', 'difficulty': 'easy', 'points': 5},
                # Medium questions (6 needed)
                {'question': 'What is list comprehension in Python?', 'options': ['Concise way to create lists', 'Method to compress lists', 'List sorting technique', 'List memory optimization'], 'correct': 'Concise way to create lists', 'difficulty': 'medium', 'points': 10},
                {'question': 'What is the difference between append() and extend()?', 'options': ['append adds one item, extend adds multiple', 'append is faster', 'extend is deprecated', 'No difference'], 'correct': 'append adds one item, extend adds multiple', 'difficulty': 'medium', 'points': 10},
                {'question': 'What is a lambda function?', 'options': ['Anonymous function', 'Named function', 'Class method', 'Loop construct'], 'correct': 'Anonymous function', 'difficulty': 'medium', 'points': 10},
                {'question': 'What does the pass statement do?', 'options': ['Does nothing, placeholder', 'Passes value to function', 'Skips iteration', 'Exits loop'], 'correct': 'Does nothing, placeholder', 'difficulty': 'medium', 'points': 10},
                {'question': 'What is the purpose of __init__?', 'options': ['Initialize object', 'Delete object', 'Call object', 'Copy object'], 'correct': 'Initialize object', 'difficulty': 'medium', 'points': 10},
                {'question': 'What is the difference between is and ==?', 'options': ['is checks identity, == checks value', 'is is faster', 'No difference', 'is is deprecated'], 'correct': 'is checks identity, == checks value', 'difficulty': 'medium', 'points': 10},
                # Hard questions (6 needed)
                {'question': 'What is a decorator in Python?', 'options': ['Function that modifies another function', 'Class that adds styling', 'Variable type', 'Loop construct'], 'correct': 'Function that modifies another function', 'difficulty': 'hard', 'points': 15},
                {'question': 'What is a generator?', 'options': ['Function that yields values', 'Random number creator', 'Loop type', 'Data structure'], 'correct': 'Function that yields values', 'difficulty': 'hard', 'points': 15},
                {'question': 'What is the GIL?', 'options': ['Global Interpreter Lock', 'General Import Library', 'Graph Interface Layer', 'Generic Input Loop'], 'correct': 'Global Interpreter Lock', 'difficulty': 'hard', 'points': 15},
                {'question': 'What is metaclass?', 'options': ['Class of a class', 'Parent class', 'Abstract class', 'Interface'], 'correct': 'Class of a class', 'difficulty': 'hard', 'points': 15},
                {'question': 'What is the purpose of *args and **kwargs?', 'options': ['Variable length arguments', 'Pointer operations', 'Mathematical operations', 'String formatting'], 'correct': 'Variable length arguments', 'difficulty': 'hard', 'points': 15},
                {'question': 'What is monkey patching?', 'options': ['Dynamic modification of class/module', 'Bug fixing technique', 'Testing method', 'Code optimization'], 'correct': 'Dynamic modification of class/module', 'difficulty': 'hard', 'points': 15},
            ],
            'JavaScript': [
                # Easy questions (8 needed)
                {'question': 'What is the correct way to declare a variable in modern JavaScript?', 'options': ['var x = 5;', 'let x = 5;', 'int x = 5;', 'variable x = 5;'], 'correct': 'let x = 5;', 'difficulty': 'easy', 'points': 5},
                {'question': 'What does console.log() do?', 'options': ['Prints to console', 'Creates variable', 'Returns value', 'Stops execution'], 'correct': 'Prints to console', 'difficulty': 'easy', 'points': 5},
                {'question': 'How do you create an array?', 'options': ['[]', '{}', '()', '<>'], 'correct': '[]', 'difficulty': 'easy', 'points': 5},
                {'question': 'What does typeof do?', 'options': ['Returns type of variable', 'Converts type', 'Checks if defined', 'Creates type'], 'correct': 'Returns type of variable', 'difficulty': 'easy', 'points': 5},
                {'question': 'Which is a comment in JavaScript?', 'options': ['// comment', '# comment', '< !-- comment', '-- comment'], 'correct': '// comment', 'difficulty': 'easy', 'points': 5},
                {'question': 'What does return do?', 'options': ['Returns value from function', 'Repeats loop', 'Restarts program', 'Removes variable'], 'correct': 'Returns value from function', 'difficulty': 'easy', 'points': 5},
                {'question': 'Which keyword declares a constant?', 'options': ['const', 'constant', 'final', 'static'], 'correct': 'const', 'difficulty': 'easy', 'points': 5},
                {'question': 'What is the correct syntax for a function?', 'options': ['function myFunc() {}', 'func myFunc() {}', 'def myFunc() {}', 'function: myFunc() {}'], 'correct': 'function myFunc() {}', 'difficulty': 'easy', 'points': 5},
                # Medium questions (6 needed)
                {'question': 'What does === operator do?', 'options': ['Checks value and type', 'Assigns value', 'Checks only value', 'Compares references'], 'correct': 'Checks value and type', 'difficulty': 'medium', 'points': 10},
                {'question': 'What is closure in JavaScript?', 'options': ['Function accessing outer scope', 'Closing browser', 'Ending program', 'Loop termination'], 'correct': 'Function accessing outer scope', 'difficulty': 'medium', 'points': 10},
                {'question': 'What is the difference between let and var?', 'options': ['let is block-scoped, var is function-scoped', 'let is faster', 'var is deprecated', 'No difference'], 'correct': 'let is block-scoped, var is function-scoped', 'difficulty': 'medium', 'points': 10},
                {'question': 'What is an arrow function?', 'options': ['Shorter function syntax', 'Pointer function', 'Direction indicator', 'Symbol operator'], 'correct': 'Shorter function syntax', 'difficulty': 'medium', 'points': 10},
                {'question': 'What does async/await do?', 'options': ['Handles asynchronous operations', 'Waits for user input', 'Pauses execution', 'Delays function'], 'correct': 'Handles asynchronous operations', 'difficulty': 'medium', 'points': 10},
                {'question': 'What is event bubbling?', 'options': ['Event propagation from child to parent', 'Creating events', 'Event deletion', 'Event sorting'], 'correct': 'Event propagation from child to parent', 'difficulty': 'medium', 'points': 10},
                # Hard questions (6 needed)
                {'question': 'What is a Promise in JavaScript?', 'options': ['Object representing eventual completion of async operation', 'Variable declaration', 'Loop type', 'Error handler'], 'correct': 'Object representing eventual completion of async operation', 'difficulty': 'hard', 'points': 15},
                {'question': 'What is event loop?', 'options': ['Mechanism for handling async code', 'Loop for events', 'Event creator', 'Event handler'], 'correct': 'Mechanism for handling async code', 'difficulty': 'hard', 'points': 15},
                {'question': 'What is prototype inheritance?', 'options': ['Objects inherit from other objects', 'Class inheritance', 'Variable inheritance', 'Function inheritance'], 'correct': 'Objects inherit from other objects', 'difficulty': 'hard', 'points': 15},
                {'question': 'What is hoisting?', 'options': ['Moving declarations to top', 'Raising errors', 'Variable elevation', 'Function priority'], 'correct': 'Moving declarations to top', 'difficulty': 'hard', 'points': 15},
                {'question': 'What is the difference between call and apply?', 'options': ['call takes args separately, apply takes array', 'call is faster', 'apply is deprecated', 'No difference'], 'correct': 'call takes args separately, apply takes array', 'difficulty': 'hard', 'points': 15},
                {'question': 'What is memoization?', 'options': ['Caching function results', 'Memory allocation', 'Variable storage', 'Data serialization'], 'correct': 'Caching function results', 'difficulty': 'hard', 'points': 15},
            ],
            'Java': [
                # Easy questions (8 needed)
                {'question': 'What is the entry point of a Java application?', 'options': ['main() method', 'start() method', 'run() method', 'init() method'], 'correct': 'main() method', 'difficulty': 'easy', 'points': 5},
                {'question': 'What does JVM stand for?', 'options': ['Java Virtual Machine', 'Java Variable Method', 'Java Version Manager', 'Java Value Model'], 'correct': 'Java Virtual Machine', 'difficulty': 'easy', 'points': 5},
                {'question': 'Which is a valid data type in Java?', 'options': ['int', 'integer', 'number', 'num'], 'correct': 'int', 'difficulty': 'easy', 'points': 5},
                {'question': 'What is the correct file extension for Java?', 'options': ['.java', '.jav', '.j', '.class'], 'correct': '.java', 'difficulty': 'easy', 'points': 5},
                {'question': 'Which keyword is used for inheritance?', 'options': ['extends', 'inherits', 'implements', 'inherit'], 'correct': 'extends', 'difficulty': 'easy', 'points': 5},
                {'question': 'What is the size of int in Java?', 'options': ['32 bits', '16 bits', '64 bits', '8 bits'], 'correct': '32 bits', 'difficulty': 'easy', 'points': 5},
                {'question': 'Which access modifier is most restrictive?', 'options': ['private', 'public', 'protected', 'default'], 'correct': 'private', 'difficulty': 'easy', 'points': 5},
                {'question': 'What does the new keyword do?', 'options': ['Creates object', 'Declares variable', 'Imports package', 'Starts program'], 'correct': 'Creates object', 'difficulty': 'easy', 'points': 5},
                # Medium questions (6 needed)
                {'question': 'What is polymorphism in Java?', 'options': ['Ability of object to take many forms', 'Multiple inheritance', 'Variable type', 'Loop structure'], 'correct': 'Ability of object to take many forms', 'difficulty': 'medium', 'points': 10},
                {'question': 'What is the difference between == and equals()?', 'options': ['== checks reference, equals() checks value', '== is faster', 'No difference', 'equals() is deprecated'], 'correct': '== checks reference, equals() checks value', 'difficulty': 'medium', 'points': 10},
                {'question': 'What is an interface?', 'options': ['Abstract type that defines behavior', 'Class type', 'Variable type', 'Loop construct'], 'correct': 'Abstract type that defines behavior', 'difficulty': 'medium', 'points': 10},
                {'question': 'What is method overloading?', 'options': ['Same name, different parameters', 'Same parameters, different name', 'Multiple classes', 'Multiple returns'], 'correct': 'Same name, different parameters', 'difficulty': 'medium', 'points': 10},
                {'question': 'What is encapsulation?', 'options': ['Bundling data and methods', 'Inheritance', 'Polymorphism', 'Abstraction'], 'correct': 'Bundling data and methods', 'difficulty': 'medium', 'points': 10},
                {'question': 'What is static keyword?', 'options': ['Belongs to class, not instance', 'Cannot change', 'Private access', 'Final variable'], 'correct': 'Belongs to class, not instance', 'difficulty': 'medium', 'points': 10},
                # Hard questions (6 needed)
                {'question': 'What is garbage collection?', 'options': ['Automatic memory management', 'Deleting files', 'Removing variables', 'Code optimization'], 'correct': 'Automatic memory management', 'difficulty': 'hard', 'points': 15},
                {'question': 'What is the difference between abstract class and interface?', 'options': ['Abstract class can have implementation', 'Interface is faster', 'No difference', 'Interface is deprecated'], 'correct': 'Abstract class can have implementation', 'difficulty': 'hard', 'points': 15},
                {'question': 'What is serialization?', 'options': ['Converting object to byte stream', 'Sorting data', 'Parallel processing', 'Thread synchronization'], 'correct': 'Converting object to byte stream', 'difficulty': 'hard', 'points': 15},
                {'question': 'What is multithreading?', 'options': ['Concurrent execution of threads', 'Multiple programs', 'Multiple classes', 'Multiple methods'], 'correct': 'Concurrent execution of threads', 'difficulty': 'hard', 'points': 15},
                {'question': 'What is the purpose of finalize()?', 'options': ['Cleanup before garbage collection', 'End program', 'Close file', 'Return value'], 'correct': 'Cleanup before garbage collection', 'difficulty': 'hard', 'points': 15},
                {'question': 'What is reflection?', 'options': ['Examining and modifying runtime behavior', 'Mirroring data', 'Code review', 'Error handling'], 'correct': 'Examining and modifying runtime behavior', 'difficulty': 'hard', 'points': 15},
            ],
            'SQL': [
                # Easy questions (8 needed)
                {'question': 'What does SQL stand for?', 'options': ['Structured Query Language', 'Simple Question Language', 'Standard Query Library', 'System Query Logic'], 'correct': 'Structured Query Language', 'difficulty': 'easy', 'points': 5},
                {'question': 'Which command is used to retrieve data from a database?', 'options': ['SELECT', 'GET', 'RETRIEVE', 'FETCH'], 'correct': 'SELECT', 'difficulty': 'easy', 'points': 5},
                {'question': 'Which clause filters results?', 'options': ['WHERE', 'FILTER', 'HAVING', 'IF'], 'correct': 'WHERE', 'difficulty': 'easy', 'points': 5},
                {'question': 'What command adds new data?', 'options': ['INSERT', 'ADD', 'CREATE', 'PUT'], 'correct': 'INSERT', 'difficulty': 'easy', 'points': 5},
                {'question': 'What command modifies existing data?', 'options': ['UPDATE', 'MODIFY', 'CHANGE', 'ALTER'], 'correct': 'UPDATE', 'difficulty': 'easy', 'points': 5},
                {'question': 'What command removes data?', 'options': ['DELETE', 'REMOVE', 'DROP', 'CLEAR'], 'correct': 'DELETE', 'difficulty': 'easy', 'points': 5},
                {'question': 'Which clause sorts results?', 'options': ['ORDER BY', 'SORT BY', 'ARRANGE BY', 'GROUP BY'], 'correct': 'ORDER BY', 'difficulty': 'easy', 'points': 5},
                {'question': 'What does DISTINCT do?', 'options': ['Removes duplicates', 'Separates columns', 'Deletes rows', 'Creates index'], 'correct': 'Removes duplicates', 'difficulty': 'easy', 'points': 5},
                # Medium questions (6 needed)
                {'question': 'What is a PRIMARY KEY?', 'options': ['Unique identifier for table row', 'Most important column', 'First column in table', 'Encrypted field'], 'correct': 'Unique identifier for table row', 'difficulty': 'medium', 'points': 10},
                {'question': 'What is a FOREIGN KEY?', 'options': ['References primary key in another table', 'External database key', 'Encrypted key', 'Temporary key'], 'correct': 'References primary key in another table', 'difficulty': 'medium', 'points': 10},
                {'question': 'What is JOIN used for?', 'options': ['Combining rows from multiple tables', 'Merging databases', 'Adding columns', 'Creating relationships'], 'correct': 'Combining rows from multiple tables', 'difficulty': 'medium', 'points': 10},
                {'question': 'What is the difference between INNER JOIN and LEFT JOIN?', 'options': ['INNER returns matches only, LEFT returns all left rows', 'INNER is faster', 'No difference', 'LEFT is deprecated'], 'correct': 'INNER returns matches only, LEFT returns all left rows', 'difficulty': 'medium', 'points': 10},
                {'question': 'What does GROUP BY do?', 'options': ['Groups rows with same values', 'Sorts rows', 'Filters rows', 'Counts rows'], 'correct': 'Groups rows with same values', 'difficulty': 'medium', 'points': 10},
                {'question': 'What is an INDEX?', 'options': ['Improves query performance', 'Primary key', 'Column order', 'Row number'], 'correct': 'Improves query performance', 'difficulty': 'medium', 'points': 10},
                # Hard questions (6 needed)
                {'question': 'What is a subquery?', 'options': ['Query nested within another query', 'Secondary database', 'Backup query', 'Query template'], 'correct': 'Query nested within another query', 'difficulty': 'hard', 'points': 15},
                {'question': 'What is normalization?', 'options': ['Organizing data to reduce redundancy', 'Data backup', 'Data encryption', 'Data compression'], 'correct': 'Organizing data to reduce redundancy', 'difficulty': 'hard', 'points': 15},
                {'question': 'What is a transaction?', 'options': ['Sequence of operations as single unit', 'Data transfer', 'Query execution', 'Table operation'], 'correct': 'Sequence of operations as single unit', 'difficulty': 'hard', 'points': 15},
                {'question': 'What does ACID stand for?', 'options': ['Atomicity Consistency Isolation Durability', 'Advanced Computer Data Interface', 'Automatic Database Indexing', 'Access Control Identity'], 'correct': 'Atomicity Consistency Isolation Durability', 'difficulty': 'hard', 'points': 15},
                {'question': 'What is a stored procedure?', 'options': ['Precompiled SQL statements', 'Backup procedure', 'Query template', 'Data validation'], 'correct': 'Precompiled SQL statements', 'difficulty': 'hard', 'points': 15},
                {'question': 'What is the purpose of HAVING clause?', 'options': ['Filters grouped results', 'Filters before grouping', 'Sorts results', 'Joins tables'], 'correct': 'Filters grouped results', 'difficulty': 'hard', 'points': 15},
            ],
            'Git': [
                # Easy questions (8 needed)
                {'question': 'What command creates a new Git repository?', 'options': ['git init', 'git create', 'git new', 'git start'], 'correct': 'git init', 'difficulty': 'easy', 'points': 5},
                {'question': 'What does git clone do?', 'options': ['Creates local copy of remote repository', 'Duplicates current branch', 'Copies files to clipboard', 'Merges branches'], 'correct': 'Creates local copy of remote repository', 'difficulty': 'easy', 'points': 5},
                {'question': 'What command stages files for commit?', 'options': ['git add', 'git stage', 'git commit', 'git push'], 'correct': 'git add', 'difficulty': 'easy', 'points': 5},
                {'question': 'What command saves changes?', 'options': ['git commit', 'git save', 'git store', 'git push'], 'correct': 'git commit', 'difficulty': 'easy', 'points': 5},
                {'question': 'What command uploads changes?', 'options': ['git push', 'git upload', 'git send', 'git deploy'], 'correct': 'git push', 'difficulty': 'easy', 'points': 5},
                {'question': 'What command downloads changes?', 'options': ['git pull', 'git download', 'git fetch', 'git get'], 'correct': 'git pull', 'difficulty': 'easy', 'points': 5},
                {'question': 'What command creates a new branch?', 'options': ['git branch', 'git new-branch', 'git create', 'git checkout'], 'correct': 'git branch', 'difficulty': 'easy', 'points': 5},
                {'question': 'What command shows commit history?', 'options': ['git log', 'git history', 'git show', 'git list'], 'correct': 'git log', 'difficulty': 'easy', 'points': 5},
                # Medium questions (6 needed)
                {'question': 'What is a merge conflict?', 'options': ['Conflicting changes in branches', 'Error in commit message', 'Invalid file type', 'Network connection issue'], 'correct': 'Conflicting changes in branches', 'difficulty': 'medium', 'points': 10},
                {'question': 'What is the difference between merge and rebase?', 'options': ['Merge creates new commit, rebase rewrites history', 'Merge is faster', 'No difference', 'Rebase is deprecated'], 'correct': 'Merge creates new commit, rebase rewrites history', 'difficulty': 'medium', 'points': 10},
                {'question': 'What is a remote repository?', 'options': ['Repository hosted on server', 'Local backup', 'Branch type', 'Commit type'], 'correct': 'Repository hosted on server', 'difficulty': 'medium', 'points': 10},
                {'question': 'What does git stash do?', 'options': ['Temporarily saves changes', 'Deletes changes', 'Commits changes', 'Pushes changes'], 'correct': 'Temporarily saves changes', 'difficulty': 'medium', 'points': 10},
                {'question': 'What is a pull request?', 'options': ['Request to merge changes', 'Download request', 'Branch request', 'Commit request'], 'correct': 'Request to merge changes', 'difficulty': 'medium', 'points': 10},
                {'question': 'What does git reset do?', 'options': ['Undoes commits', 'Resets password', 'Clears repository', 'Restarts server'], 'correct': 'Undoes commits', 'difficulty': 'medium', 'points': 10},
                # Hard questions (6 needed)
                {'question': 'What is git cherry-pick?', 'options': ['Applies specific commit to current branch', 'Selects files', 'Removes commits', 'Creates branch'], 'correct': 'Applies specific commit to current branch', 'difficulty': 'hard', 'points': 15},
                {'question': 'What is the difference between fetch and pull?', 'options': ['Fetch downloads without merging, pull merges', 'Fetch is faster', 'No difference', 'Pull is deprecated'], 'correct': 'Fetch downloads without merging, pull merges', 'difficulty': 'hard', 'points': 15},
                {'question': 'What is git bisect?', 'options': ['Binary search for bug-introducing commit', 'Splits repository', 'Divides branches', 'Separates files'], 'correct': 'Binary search for bug-introducing commit', 'difficulty': 'hard', 'points': 15},
                {'question': 'What is a detached HEAD?', 'options': ['Checked out commit instead of branch', 'Broken repository', 'Missing files', 'Network error'], 'correct': 'Checked out commit instead of branch', 'difficulty': 'hard', 'points': 15},
                {'question': 'What does git reflog do?', 'options': ['Shows history of HEAD references', 'Logs remote changes', 'Records file changes', 'Tracks branches'], 'correct': 'Shows history of HEAD references', 'difficulty': 'hard', 'points': 15},
                {'question': 'What is the purpose of .gitignore?', 'options': ['Specifies files to exclude from tracking', 'Lists ignored users', 'Blocks commands', 'Hides branches'], 'correct': 'Specifies files to exclude from tracking', 'difficulty': 'hard', 'points': 15},
            ],
            'REST APIs': [
                {
                    'question': 'What does REST stand for?',
                    'options': [
                        'Representational State Transfer',
                        'Remote Execution Service Technology',
                        'Rapid Event Stream Transfer',
                        'Resource Exchange State Transaction'
                    ],
                    'correct': 'Representational State Transfer',
                    'difficulty': 'easy',
                    'points': 5,
                },
                {
                    'question': 'Which HTTP method is used to retrieve data?',
                    'options': ['GET', 'POST', 'PUT', 'DELETE'],
                    'correct': 'GET',
                    'difficulty': 'easy',
                    'points': 5,
                },
                {
                    'question': 'What HTTP status code indicates success?',
                    'options': ['200', '404', '500', '301'],
                    'correct': '200',
                    'difficulty': 'easy',
                    'points': 5,
                },
            ],
            'Django': [
                {
                    'question': 'What is Django?',
                    'options': [
                        'Python web framework',
                        'JavaScript library',
                        'Database system',
                        'Version control tool'
                    ],
                    'correct': 'Python web framework',
                    'difficulty': 'easy',
                    'points': 5,
                },
                {
                    'question': 'What is an ORM in Django?',
                    'options': [
                        'Object-Relational Mapper',
                        'Online Resource Manager',
                        'Output Rendering Module',
                        'Open Request Method'
                    ],
                    'correct': 'Object-Relational Mapper',
                    'difficulty': 'medium',
                    'points': 10,
                },
            ],
            'React': [
                {
                    'question': 'What is React?',
                    'options': [
                        'JavaScript library for building UIs',
                        'Python framework',
                        'Database system',
                        'CSS framework'
                    ],
                    'correct': 'JavaScript library for building UIs',
                    'difficulty': 'easy',
                    'points': 5,
                },
                {
                    'question': 'What is JSX?',
                    'options': [
                        'JavaScript XML syntax extension',
                        'Java Syntax Extension',
                        'JSON Export',
                        'JavaScript Extra'
                    ],
                    'correct': 'JavaScript XML syntax extension',
                    'difficulty': 'medium',
                    'points': 10,
                },
            ],
            'Data Analysis': [
                # Easy questions (8 needed)
                {'question': 'What is data cleaning?', 'options': ['Removing errors and inconsistencies', 'Deleting old data', 'Compressing data', 'Encrypting data'], 'correct': 'Removing errors and inconsistencies', 'difficulty': 'easy', 'points': 5},
                {'question': 'What is a dataset?', 'options': ['Collection of data', 'Database type', 'Analysis tool', 'Chart type'], 'correct': 'Collection of data', 'difficulty': 'easy', 'points': 5},
                {'question': 'What is the purpose of data visualization?', 'options': ['Present data graphically', 'Store data', 'Clean data', 'Encrypt data'], 'correct': 'Present data graphically', 'difficulty': 'easy', 'points': 5},
                {'question': 'What does mean represent?', 'options': ['Average value', 'Middle value', 'Most common value', 'Range'], 'correct': 'Average value', 'difficulty': 'easy', 'points': 5},
                {'question': 'What is a histogram?', 'options': ['Bar chart showing distribution', 'Line chart', 'Pie chart', 'Scatter plot'], 'correct': 'Bar chart showing distribution', 'difficulty': 'easy', 'points': 5},
                {'question': 'What is correlation?', 'options': ['Relationship between variables', 'Data cleaning', 'Data storage', 'Data type'], 'correct': 'Relationship between variables', 'difficulty': 'easy', 'points': 5},
                {'question': 'What is a CSV file?', 'options': ['Comma-separated values', 'Compressed system values', 'Computer storage volume', 'Central server values'], 'correct': 'Comma-separated values', 'difficulty': 'easy', 'points': 5},
                {'question': 'What does outlier mean?', 'options': ['Data point significantly different', 'Missing data', 'Average data', 'Normal data'], 'correct': 'Data point significantly different', 'difficulty': 'easy', 'points': 5},
                # Medium questions (6 needed)
                {'question': 'What is exploratory data analysis?', 'options': ['Initial investigation of data', 'Final report', 'Data collection', 'Data storage'], 'correct': 'Initial investigation of data', 'difficulty': 'medium', 'points': 10},
                {'question': 'What is the difference between median and mean?', 'options': ['Median is middle value, mean is average', 'Median is faster', 'No difference', 'Mean is deprecated'], 'correct': 'Median is middle value, mean is average', 'difficulty': 'medium', 'points': 10},
                {'question': 'What is data normalization?', 'options': ['Scaling data to standard range', 'Removing duplicates', 'Sorting data', 'Filtering data'], 'correct': 'Scaling data to standard range', 'difficulty': 'medium', 'points': 10},
                {'question': 'What is a pivot table?', 'options': ['Summarizes data in table format', 'Rotates table', 'Merges tables', 'Deletes table'], 'correct': 'Summarizes data in table format', 'difficulty': 'medium', 'points': 10},
                {'question': 'What is regression analysis?', 'options': ['Modeling relationship between variables', 'Going backwards', 'Data deletion', 'Error checking'], 'correct': 'Modeling relationship between variables', 'difficulty': 'medium', 'points': 10},
                {'question': 'What is time series analysis?', 'options': ['Analyzing data over time', 'Clock data', 'Timestamp creation', 'Time zone conversion'], 'correct': 'Analyzing data over time', 'difficulty': 'medium', 'points': 10},
                # Hard questions (6 needed)
                {'question': 'What is p-value in statistics?', 'options': ['Probability of observing results by chance', 'Primary value', 'Prediction value', 'Point value'], 'correct': 'Probability of observing results by chance', 'difficulty': 'hard', 'points': 15},
                {'question': 'What is dimensionality reduction?', 'options': ['Reducing number of variables', 'Shrinking data size', 'Lowering resolution', 'Decreasing accuracy'], 'correct': 'Reducing number of variables', 'difficulty': 'hard', 'points': 15},
                {'question': 'What is A/B testing?', 'options': ['Comparing two versions', 'Testing alphabets', 'Binary testing', 'Automated testing'], 'correct': 'Comparing two versions', 'difficulty': 'hard', 'points': 15},
                {'question': 'What is feature engineering?', 'options': ['Creating new features from existing data', 'Software engineering', 'Product features', 'Data collection'], 'correct': 'Creating new features from existing data', 'difficulty': 'hard', 'points': 15},
                {'question': 'What is the purpose of cross-validation?', 'options': ['Assess model performance', 'Validate users', 'Check data quality', 'Verify calculations'], 'correct': 'Assess model performance', 'difficulty': 'hard', 'points': 15},
                {'question': 'What is bootstrapping in statistics?', 'options': ['Resampling method for estimation', 'Starting program', 'Loading data', 'Initial setup'], 'correct': 'Resampling method for estimation', 'difficulty': 'hard', 'points': 15},
            ],
            'Machine Learning': [
                # Easy questions (8 needed)
                {'question': 'What is machine learning?', 'options': ['Computer learning from data', 'Robot assembly', 'Computer hardware', 'Software installation'], 'correct': 'Computer learning from data', 'difficulty': 'easy', 'points': 5},
                {'question': 'What is a model in ML?', 'options': ['Trained algorithm', 'Data structure', 'Database schema', 'User interface'], 'correct': 'Trained algorithm', 'difficulty': 'easy', 'points': 5},
                {'question': 'What is training data?', 'options': ['Data used to train model', 'Educational content', 'Test cases', 'Documentation'], 'correct': 'Data used to train model', 'difficulty': 'easy', 'points': 5},
                {'question': 'What is a feature?', 'options': ['Input variable', 'Program capability', 'Output result', 'Error type'], 'correct': 'Input variable', 'difficulty': 'easy', 'points': 5},
                {'question': 'What is a label?', 'options': ['Output/target variable', 'Name tag', 'Variable name', 'Code comment'], 'correct': 'Output/target variable', 'difficulty': 'easy', 'points': 5},
                {'question': 'What is classification?', 'options': ['Predicting categories', 'Organizing files', 'Sorting data', 'Data type'], 'correct': 'Predicting categories', 'difficulty': 'easy', 'points': 5},
                {'question': 'What is regression in ML?', 'options': ['Predicting continuous values', 'Going backwards', 'Error handling', 'Data cleaning'], 'correct': 'Predicting continuous values', 'difficulty': 'easy', 'points': 5},
                {'question': 'What is accuracy?', 'options': ['Percentage of correct predictions', 'Speed of algorithm', 'Data quality', 'Memory usage'], 'correct': 'Percentage of correct predictions', 'difficulty': 'easy', 'points': 5},
                # Medium questions (6 needed)
                {'question': 'What is supervised learning?', 'options': ['Learning with labeled data', 'Learning without teacher', 'Learning by observation', 'Learning with feedback'], 'correct': 'Learning with labeled data', 'difficulty': 'medium', 'points': 10},
                {'question': 'What is unsupervised learning?', 'options': ['Learning without labeled data', 'Automatic learning', 'Independent learning', 'Random learning'], 'correct': 'Learning without labeled data', 'difficulty': 'medium', 'points': 10},
                {'question': 'What is overfitting?', 'options': ['Model too specific to training data', 'Too much data', 'High accuracy', 'Fast training'], 'correct': 'Model too specific to training data', 'difficulty': 'medium', 'points': 10},
                {'question': 'What is a neural network?', 'options': ['Network of interconnected nodes', 'Computer network', 'Data structure', 'Database system'], 'correct': 'Network of interconnected nodes', 'difficulty': 'medium', 'points': 10},
                {'question': 'What is cross-validation?', 'options': ['Technique to assess model performance', 'Data validation', 'User authentication', 'Error checking'], 'correct': 'Technique to assess model performance', 'difficulty': 'medium', 'points': 10},
                {'question': 'What is feature selection?', 'options': ['Choosing relevant features', 'Selecting products', 'User preferences', 'Data filtering'], 'correct': 'Choosing relevant features', 'difficulty': 'medium', 'points': 10},
                # Hard questions (6 needed)
                {'question': 'What is gradient descent?', 'options': ['Optimization algorithm', 'Going downhill', 'Data decrease', 'Error rate'], 'correct': 'Optimization algorithm', 'difficulty': 'hard', 'points': 15},
                {'question': 'What is backpropagation?', 'options': ['Algorithm for training neural networks', 'Backward iteration', 'Error recovery', 'Data backup'], 'correct': 'Algorithm for training neural networks', 'difficulty': 'hard', 'points': 15},
                {'question': 'What is regularization?', 'options': ['Technique to prevent overfitting', 'Making patterns regular', 'Data normalization', 'Rule enforcement'], 'correct': 'Technique to prevent overfitting', 'difficulty': 'hard', 'points': 15},
                {'question': 'What is the difference between precision and recall?', 'options': ['Precision: correct positives/all positives, Recall: correct positives/actual positives', 'Precision is faster', 'No difference', 'Recall is deprecated'], 'correct': 'Precision: correct positives/all positives, Recall: correct positives/actual positives', 'difficulty': 'hard', 'points': 15},
                {'question': 'What is ensemble learning?', 'options': ['Combining multiple models', 'Group learning', 'Parallel training', 'Data aggregation'], 'correct': 'Combining multiple models', 'difficulty': 'hard', 'points': 15},
                {'question': 'What is transfer learning?', 'options': ['Using pre-trained model for new task', 'Moving data', 'Transferring files', 'Learning transfer'], 'correct': 'Using pre-trained model for new task', 'difficulty': 'hard', 'points': 15},
            ],
            'aws': [
                # Easy questions (8 needed)
                {'question': 'What does AWS stand for?', 'options': ['Amazon Web Services', 'Advanced Web System', 'Automated Web Server', 'Application Web Services'], 'correct': 'Amazon Web Services', 'difficulty': 'easy', 'points': 5},
                {'question': 'What is EC2?', 'options': ['Virtual server in cloud', 'Storage service', 'Database service', 'Network service'], 'correct': 'Virtual server in cloud', 'difficulty': 'easy', 'points': 5},
                {'question': 'What is S3?', 'options': ['Object storage service', 'Computing service', 'Database service', 'Networking service'], 'correct': 'Object storage service', 'difficulty': 'easy', 'points': 5},
                {'question': 'What is IAM?', 'options': ['Identity and Access Management', 'Internet Application Manager', 'Integrated Access Module', 'Instance Administration Module'], 'correct': 'Identity and Access Management', 'difficulty': 'easy', 'points': 5},
                {'question': 'What is RDS?', 'options': ['Relational Database Service', 'Remote Data Storage', 'Real-time Data System', 'Resource Distribution Service'], 'correct': 'Relational Database Service', 'difficulty': 'easy', 'points': 5},
                {'question': 'What is a region in AWS?', 'options': ['Geographic area with data centers', 'User group', 'Service type', 'Network zone'], 'correct': 'Geographic area with data centers', 'difficulty': 'easy', 'points': 5},
                {'question': 'What is Lambda?', 'options': ['Serverless compute service', 'Storage service', 'Database service', 'Network service'], 'correct': 'Serverless compute service', 'difficulty': 'easy', 'points': 5},
                {'question': 'What is CloudWatch?', 'options': ['Monitoring service', 'Storage service', 'Computing service', 'Security service'], 'correct': 'Monitoring service', 'difficulty': 'easy', 'points': 5},
                # Medium questions (6 needed)
                {'question': 'What is the difference between S3 and EBS?', 'options': ['S3 is object storage, EBS is block storage', 'S3 is faster', 'No difference', 'EBS is deprecated'], 'correct': 'S3 is object storage, EBS is block storage', 'difficulty': 'medium', 'points': 10},
                {'question': 'What is Auto Scaling?', 'options': ['Automatically adjusts capacity', 'Manual scaling', 'Fixed capacity', 'Load balancing'], 'correct': 'Automatically adjusts capacity', 'difficulty': 'medium', 'points': 10},
                {'question': 'What is VPC?', 'options': ['Virtual Private Cloud', 'Virtual Public Cloud', 'Virtual Processing Center', 'Variable Private Connection'], 'correct': 'Virtual Private Cloud', 'difficulty': 'medium', 'points': 10},
                {'question': 'What is Elastic Beanstalk?', 'options': ['PaaS for deploying applications', 'Storage service', 'Database service', 'Monitoring service'], 'correct': 'PaaS for deploying applications', 'difficulty': 'medium', 'points': 10},
                {'question': 'What is CloudFront?', 'options': ['Content delivery network', 'Weather service', 'Storage service', 'Computing service'], 'correct': 'Content delivery network', 'difficulty': 'medium', 'points': 10},
                {'question': 'What is SNS?', 'options': ['Simple Notification Service', 'Simple Network Service', 'Secure Network System', 'Server Naming Service'], 'correct': 'Simple Notification Service', 'difficulty': 'medium', 'points': 10},
                # Hard questions (6 needed)
                {'question': 'What is the difference between ECS and EKS?', 'options': ['ECS uses Docker, EKS uses Kubernetes', 'ECS is faster', 'No difference', 'EKS is deprecated'], 'correct': 'ECS uses Docker, EKS uses Kubernetes', 'difficulty': 'hard', 'points': 15},
                {'question': 'What is AWS Global Accelerator?', 'options': ['Improves global application availability', 'Makes queries faster', 'Speeds up uploads', 'Accelerates downloads'], 'correct': 'Improves global application availability', 'difficulty': 'hard', 'points': 15},
                {'question': 'What is DynamoDB?', 'options': ['NoSQL database service', 'Relational database', 'File storage', 'Cache service'], 'correct': 'NoSQL database service', 'difficulty': 'hard', 'points': 15},
                {'question': 'What is the AWS Well-Architected Framework?', 'options': ['Best practices for cloud architecture', 'Building design tool', 'Network architecture', 'Security framework'], 'correct': 'Best practices for cloud architecture', 'difficulty': 'hard', 'points': 15},
                {'question': 'What is AWS Organizations?', 'options': ['Centrally manage multiple AWS accounts', 'User groups', 'Resource organization', 'Company directory'], 'correct': 'Centrally manage multiple AWS accounts', 'difficulty': 'hard', 'points': 15},
                {'question': 'What is the purpose of AWS Shield?', 'options': ['DDoS protection', 'Data encryption', 'Firewall service', 'Antivirus protection'], 'correct': 'DDoS protection', 'difficulty': 'hard', 'points': 15},
            ],
            'docker': [
                # Easy questions (8 needed)
                {'question': 'What is Docker?', 'options': ['Containerization platform', 'Virtual machine', 'Programming language', 'Database system'], 'correct': 'Containerization platform', 'difficulty': 'easy', 'points': 5},
                {'question': 'What is a container?', 'options': ['Lightweight executable package', 'Virtual machine', 'Storage unit', 'Network device'], 'correct': 'Lightweight executable package', 'difficulty': 'easy', 'points': 5},
                {'question': 'What is a Docker image?', 'options': ['Template for containers', 'Picture file', 'Virtual machine snapshot', 'Backup file'], 'correct': 'Template for containers', 'difficulty': 'easy', 'points': 5},
                {'question': 'What is Dockerfile?', 'options': ['Script to build Docker image', 'Configuration file', 'Log file', 'Data file'], 'correct': 'Script to build Docker image', 'difficulty': 'easy', 'points': 5},
                {'question': 'What command runs a container?', 'options': ['docker run', 'docker start', 'docker execute', 'docker launch'], 'correct': 'docker run', 'difficulty': 'easy', 'points': 5},
                {'question': 'What is Docker Hub?', 'options': ['Repository for Docker images', 'Development tool', 'Monitoring service', 'Network hub'], 'correct': 'Repository for Docker images', 'difficulty': 'easy', 'points': 5},
                {'question': 'What command lists running containers?', 'options': ['docker ps', 'docker list', 'docker show', 'docker containers'], 'correct': 'docker ps', 'difficulty': 'easy', 'points': 5},
                {'question': 'What command builds an image?', 'options': ['docker build', 'docker create', 'docker make', 'docker compile'], 'correct': 'docker build', 'difficulty': 'easy', 'points': 5},
                # Medium questions (6 needed)
                {'question': 'What is the difference between container and image?', 'options': ['Image is template, container is running instance', 'Container is faster', 'No difference', 'Image is deprecated'], 'correct': 'Image is template, container is running instance', 'difficulty': 'medium', 'points': 10},
                {'question': 'What is Docker Compose?', 'options': ['Tool for multi-container applications', 'Music tool', 'File compression', 'Image builder'], 'correct': 'Tool for multi-container applications', 'difficulty': 'medium', 'points': 10},
                {'question': 'What is a volume in Docker?', 'options': ['Persistent data storage', 'Sound control', 'Size measurement', 'Network volume'], 'correct': 'Persistent data storage', 'difficulty': 'medium', 'points': 10},
                {'question': 'What is port mapping?', 'options': ['Mapping container ports to host', 'Network routing', 'Data transformation', 'File mapping'], 'correct': 'Mapping container ports to host', 'difficulty': 'medium', 'points': 10},
                {'question': 'What is a Docker registry?', 'options': ['Storage for Docker images', 'System registry', 'Configuration database', 'User directory'], 'correct': 'Storage for Docker images', 'difficulty': 'medium', 'points': 10},
                {'question': 'What does docker exec do?', 'options': ['Runs command in running container', 'Executes file', 'Stops container', 'Deletes container'], 'correct': 'Runs command in running container', 'difficulty': 'medium', 'points': 10},
                # Hard questions (6 needed)
                {'question': 'What is the difference between CMD and ENTRYPOINT?', 'options': ['CMD can be overridden, ENTRYPOINT cannot', 'CMD is faster', 'No difference', 'ENTRYPOINT is deprecated'], 'correct': 'CMD can be overridden, ENTRYPOINT cannot', 'difficulty': 'hard', 'points': 15},
                {'question': 'What is multi-stage build?', 'options': ['Multiple FROM statements in Dockerfile', 'Building multiple images', 'Parallel compilation', 'Sequential deployment'], 'correct': 'Multiple FROM statements in Dockerfile', 'difficulty': 'hard', 'points': 15},
                {'question': 'What is Docker Swarm?', 'options': ['Native clustering for Docker', 'Group of containers', 'Bee management', 'Load balancer'], 'correct': 'Native clustering for Docker', 'difficulty': 'hard', 'points': 15},
                {'question': 'What is the purpose of .dockerignore?', 'options': ['Excludes files from build context', 'Ignores containers', 'Blocks commands', 'Hides images'], 'correct': 'Excludes files from build context', 'difficulty': 'hard', 'points': 15},
                {'question': 'What is container orchestration?', 'options': ['Managing multiple containers', 'Music arrangement', 'Data organization', 'File sorting'], 'correct': 'Managing multiple containers', 'difficulty': 'hard', 'points': 15},
                {'question': 'What is the difference between COPY and ADD?', 'options': ['ADD can extract archives and fetch URLs', 'COPY is faster', 'No difference', 'ADD is deprecated'], 'correct': 'ADD can extract archives and fetch URLs', 'difficulty': 'hard', 'points': 15},
            ],
        }
        
        # Add questions to skills
        questions_added = 0
        for skill_name, questions_data in skill_questions.items():
            # Find all skills with this name
            skills = Skill.objects.filter(name=skill_name)
            if not skills.exists():
                self.stdout.write(self.style.WARNING(f'  Skill "{skill_name}" not found'))
                continue
            
            for skill in skills:
                # Only add if skill has no questions
                if QuestionBank.objects.filter(skill=skill).exists():
                    self.stdout.write(f'  Skipping {skill.category.name} - {skill.name} (already has questions)')
                    continue
                
                self.stdout.write(f'  Adding questions to {skill.category.name} - {skill.name}...')
                for q in questions_data:
                    QuestionBank.objects.create(
                        skill=skill,
                        question_text=q['question'],
                        options=q['options'],
                        correct_answer=q['correct'],
                        difficulty=q['difficulty'],
                        points=q['points'],
                        created_by_ai=False,
                    )
                    questions_added += 1
        
        self.stdout.write(self.style.SUCCESS(
            f'✓ Successfully added {questions_added} questions to existing skills'
        ))
