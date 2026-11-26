AI DATABASE QUERY ASSISTANT

Task ID: AI-SD-006
Student Code: DAS014552

1. Introduction

AI Database Query Assistant is a Python-based application that converts natural language questions into SQL queries. It allows users to interact with a database using simple English sentences instead of writing SQL commands manually.

2. Project Objective

The main objective is to develop a system that understands user questions, identifies the required information, generates SQL queries and displays database results.

3. Technologies Used

- Programming Language: Python
- Database: SQLite
- NLP Technique: Rule-based Natural Language Processing
- Text Processing: Regular Expressions
- Development Platform: Pydroid 3

4. System Modules

1. Schema Management: Manages database tables and columns.
2. Natural Language Processing: Processes English questions.
3. Intent Recognition: Identifies the user's intention.
4. Entity Extraction: Extracts details such as department, age and city.
5. SQL Query Generation: Converts questions into SQL statements.
6. Query Execution: Executes SQL queries using SQLite.
7. Query History: Stores previous user questions and generated queries.

5. Implementation

The application is developed using Python and SQLite. The system accepts English questions from users and processes them using regular expressions and predefined rules.

Based on the detected intent and extracted entities, the application generates parameterized SQL queries and executes them against the database.

The application supports student record management, filtering, sorting, aggregate functions and JOIN operations.

6. Testing

The following operations were tested successfully:

- Displaying all student records.
- Filtering students by department.
- Filtering students by city.
- Counting total students.
- Calculating average age.
- Filtering students by age.
- Performing JOIN operations.
- Displaying database schema.
- Viewing query history.
- Adding, updating and deleting student records.

7. Conclusion

The AI Database Query Assistant provides a simple interface for interacting with databases using natural language. It reduces the need for users to manually write SQL queries and demonstrates the practical use of Python, SQLite and rule-based NLP.

Future Enhancement: Integrating machine learning models and advanced NLP techniques can improve natural language understanding and SQL generation.
