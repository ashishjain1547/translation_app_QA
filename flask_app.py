from flask import Flask, redirect, render_template, request, url_for, make_response, session, flash
import json, requests
from flask_cors import CORS, cross_origin
from flask import Response, jsonify
import jwt
from datetime import datetime, timezone, timedelta
from functools import wraps
import sqlite3
from datetime import date
import os
import logging
from sqlalchemy.pool import NullPool
from logging.handlers import RotatingFileHandler
from sqlalchemy import create_engine, text
import mysql.connector

# /home/ashishjain1547/mysite/logs
logging.basicConfig(filename = os.path.join('logs', 'application.log'), level=logging.DEBUG)


app=Flask(__name__)
app.config['SECRET_KEY'] = 'Alpha'
app.secret_key = 'your_secret_key_here'  # Set a secret key for session management

cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'


@app.route('/')
def welcome():
    #return render_template("index.html")
    # if 'username' in session:
    #     # User is logged in, show the main page
    #     return render_template('index_mysql.html')
    # else:
    #     # User is not logged in, show the login form
    #     return render_template('login.html')

    return "<h1>Welcome</h1>"


@app.route('/logout')
def logout():
    session.pop('username', None)  # Remove username from session
    return redirect(url_for('welcome'))

def get_connection_sqlite():
    #conn = sqlite3.connect('hindi_to_english_v4.db')
    conn = sqlite3.connect(os.path.join('mysite', 'pythonsqlite.db'))
    return conn

#with open("/home/ashishjain1547/mysite/db_config.json") as f:
with open("./db_config.json") as f:
    DB_CONFIG = json.load(f)

def get_mysql_connection():
    conn = mysql.connector.connect(
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            database=DB_CONFIG["database"]
        )
    return conn


@app.route("/register_mysql", methods=["POST"])
@cross_origin()
def register_mysql():
    username = request.form["username"]
    password = request.form["password"]
    confirm_password = request.form["confirm_password"]

    if username != "" and password == confirm_password:
        conn = get_mysql_connection()  

        cursor = conn.cursor()
        print('Opened database successfully')

        # Queries to INSERT records.
        try:
            cursor.execute("INSERT INTO user_login (username, password) VALUES (%s, %s)", (username, password))
        except mysql.connector.IntegrityError as e:
            return jsonify({'error': 'Username is not unique'}), 4001

        try:
            pass  # init_questions_for_new_registered_user(conn, username);
        except Exception as e:
            print(e)
            return jsonify({'error': str(e)}), 4002

        conn.commit()
        conn.close()

        # In a real scenario, password should be securely hashed
        token = jwt.encode({'user': username, 'exp': datetime.now(timezone.utc) + timedelta(minutes=1)}, app.config['SECRET_KEY'])

        return jsonify({
            'username': username,
            'token': token
        })

    return make_response('Could not verify!', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})


@app.route("/register_sqlite", methods=["POST"])
@cross_origin()
def register_sqlite():
    username = request.form["username"]
    password = request.form["password"]
    confirm_password = request.form["confirm_password"]

    if username != "" and password == confirm_password:
        conn = get_connection_sqlite()

        # Creating a cursor object using the cursor() method
        cursor = conn.cursor()

        print('Opened database successfully')
        #print(request.form)

        # Creating table
        table = """CREATE TABLE IF NOT EXISTS user_login
        (
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        ) """

        cursor.execute(table)

        # Queries to INSERT records.
        try:
            cursor.execute("INSERT INTO user_login (username, password) VALUES (?, ?)", (username, password))
        except sqlite3.IntegrityError as e:
            return jsonify({'error': 'Username is not unique'}), 400


        try:
            pass
            # init_questions_for_new_registered_user(conn, username);
        except Exception as e:
            print(e)
            return make_response(str(e), 4002)

        conn.commit()
        conn.close()

        # In a real scenario, password should be securely hashed
        token = jwt.encode({'user': username, 'exp': datetime.now(timezone.utc) + timedelta(minutes=1)}, app.config['SECRET_KEY'])

        # Original ChatGPT code
        # return jsonify({'token': token.decode('UTF-8')})
        return jsonify({
            'username': username,
            'token': token
        })

    return make_response('Could not verify!', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})

# Decorator to check if the user is logged in (JWT token is present and valid)
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        except Exception as e:
            print(e)
            return jsonify({'message': 'Token is invalid!'}), 401

        return f(*args, **kwargs)

    return decorated

# Protected route that requires JWT token for access
@app.route('/protected')
@cross_origin()
@token_required
def protected():
    return jsonify({'message': 'This is a protected resource!'})

# Route to authenticate user and generate JWT token
@app.route('/login_mysql', methods=["POST"])
@cross_origin()
def login_mysql():
    username = request.form["username"]
    password = request.form["password"]

    conn = get_mysql_connection()  

    cursor = conn.cursor()
    print('Opened database successfully')

    cursor.execute("SELECT COUNT(*) FROM user_login WHERE username = %s AND password = %s", (username, password))
    temp_c = cursor.fetchone()[0]

    if temp_c > 0:  # In a real scenario, password should be securely hashed
        token = jwt.encode({'user': username, 'exp': datetime.now(timezone.utc) + timedelta(minutes=30)}, app.config['SECRET_KEY'])

        app.logger.info('token: ' + str(token))

        return jsonify({'username': username, 'token': token})

    return make_response('Could not verify!', 401)

@app.route('/login_sqlite', methods=["POST"])
@cross_origin()
def login_sqlite():
    username = request.form["username"]
    password = request.form["password"]



    conn = get_connection_sqlite()


    # Creating a cursor object using the cursor() method
    cursor = conn.cursor()

    print('Opened database successfully')
    #print(request.form)

    cnt_users = conn.execute("SELECT count(*) FROM user_login where username = ? and password = ?", (username, password))

    temp_c = 0
    for c in cnt_users:
        temp_c = c[0]



    if temp_c > 0:  # In a real scenario, password should be securely hashed
        token = jwt.encode({'user': username, 'exp': datetime.now(timezone.utc) + timedelta(minutes=30)}, app.config['SECRET_KEY'])

        app.logger.info('token: ' + str(token))

        return jsonify({'username': username, 'token': token})

    # return make_response('Could not verify!', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})
    return make_response('Could not verify!', 401)


def load_next_ques_mysql(conn, username):
    query = """SELECT pair_id, hindi, english FROM hindi_to_english_ques_bank WHERE pair_id IN (
        SELECT pair_id FROM attempted_hindi_to_eng_ques
        WHERE username = %s AND flag = 0
        ORDER BY RAND() LIMIT 1
    );"""

    app.logger.info("query: " + query)
    cursor = conn.cursor()
    cursor.execute(query, (username,))

    pair_id, hindi, english = (-1, -1, -1)

    for row in cursor:
        pair_id = row[0]
        hindi = row[1]
        english = row[2]

    return pair_id, hindi, english

def load_next_ques_sqlite(conn, username):
    query = """select pair_id, hindi, english from hindi_to_english_ques_bank where pair_id in (
        SELECT pair_id FROM attempted_hindi_to_eng_ques
        where username = '{}' and flag = 0
        ORDER BY RANDOM() LIMIT 1
    );""".format(username)

    app.logger.info("query: " + query)
    cursor = conn.execute(query)

    pair_id, hindi, english = (-1, -1, -1)

    for row in cursor:
        pair_id = row[0]
        hindi = row[1]
        english = row[2]

    return pair_id, hindi, english

def reset_attempted_questions_for_this_user_mysql(conn, username):
    cursor_insert = conn.cursor()

    update_query = """update attempted_hindi_to_eng_ques
        set flag = 0 where username = '%s'""" % username

    app.logger.info('reset_attempted_questions_for_this_user_mysql: update_query: ' + update_query)

    count = cursor_insert.execute(update_query)
    conn.commit()


def reset_attempted_questions_for_this_user_sqlite(conn, username):
    cursor_insert = conn.cursor()

    update_query = """update attempted_hindi_to_eng_ques
        set flag = 0 where username = '{}'""".format(username)

    app.logger.info('reset_attempted_questions_for_this_user_sqlite:  update_query: ' + update_query)

    count = cursor_insert.execute(update_query)
    conn.commit()



@app.route('/next_ques_mysql', methods=['GET', 'POST'])
@cross_origin()
def next_ques_mysql():
    d = str(request.get_data())[2:-1].split('&') # bytes to str
    e = {}
    for i in d:
        e[i.split("=")[0]] = i.split("=")[1]

    app.logger.info('e: ' + str(e))

    conn = get_mysql_connection()

    app.logger.info('Opened database successfully')

    # username = session.get('username', 'na')
    username = e['username']

    pair_id, hindi, english = load_next_ques_mysql(conn, username)

    if pair_id == -1:
        reset_attempted_questions_for_this_user_mysql(conn, username)
        pair_id, hindi, english = load_next_ques_mysql(conn, username)

    app.logger.info("username: " + str(username))
    app.logger.info("pair_id: " + str(pair_id))
    app.logger.info("hindi: " + str(hindi))
    app.logger.info("english: " + str(english))

    cursor_insert = conn.cursor()

    update_query = """update attempted_hindi_to_eng_ques
        set flag = 1
        where username = %s and pair_id = %s""" % (username, pair_id)

    app.logger.info('next_ques_mysql: update_query: ' + update_query)

    count = cursor_insert.execute(update_query)
    conn.commit()

    app.logger.info("Record update successful: " + str(cursor_insert.rowcount))

    return jsonify({
        'pair_id': pair_id,
        'hindi': hindi,
        'english': english
    })


@app.route('/next_ques_sqlite', methods=['GET', 'POST'])
@cross_origin()
def next_ques_sqlite():
    d = str(request.get_data())[2:-1].split('&') # bytes to str
    e = {}
    for i in d:
        e[i.split("=")[0]] = i.split("=")[1]

    app.logger.info('e: ' + str(e))

    conn = get_connection_sqlite()

    app.logger.info('Opened database successfully')

    # username = session.get('username', 'na')
    username = e['username']

    pair_id, hindi, english = load_next_ques_sqlite(conn, username)

    if pair_id == -1:
        reset_attempted_questions_for_this_user_sqlite(conn, username)
        pair_id, hindi, english = load_next_ques_sqlite(conn, username)

    app.logger.info("username: " + str(username))
    app.logger.info("pair_id: " + str(pair_id))
    app.logger.info("hindi: " + str(hindi))
    app.logger.info("english: " + str(english))

    cursor_insert = conn.cursor()

    update_query = """update attempted_hindi_to_eng_ques
        set flag = 1
        where username = '{}' and pair_id = {}""".format(username, pair_id)

    app.logger.info('next_ques_sqlite: update_query: ' + update_query)

    count = cursor_insert.execute(update_query)
    conn.commit()

    app.logger.info("Record update successful: " + str(cursor_insert.rowcount))

    app.logger.info('Operation done successfully')

    conn.close()

    rtnVal = {
        'hindi': hindi,
        'english': english
    }

    return jsonify(rtnVal)


def init_questions_chapter_wise_mysql(username, chapter):

    conn = get_mysql_connection()
    cursor = conn.cursor()  # Create a cursor from the connection

    cursor.execute("""SELECT pair_id FROM ques_info WHERE ROUND(chapter, 1) = %s""", (chapter,))
    # Use cursor.fetchall() if you need to retrieve the results
    pairids = cursor.fetchall()

    cursor.close()  # Don't forget to close the cursor

    app.logger.info("init_questions_chapter_wise_mysql:")
    app.logger.info("username: " + str(username))
    app.logger.info("chapter: " + str(chapter))
    app.logger.info("pairids: " + str(pairids))
     
    for row in pairids:
        cursor_insert = conn.cursor()

        delete_query = """DELETE FROM attempted_hindi_to_eng_ques
                            WHERE username = '%s' and pair_id = %s""" % (username, row[0])

        count = cursor_insert.execute(delete_query)
        conn.commit()

        insert_query = """INSERT INTO attempted_hindi_to_eng_ques
                            (username, pair_id, flag)
                            VALUES
                            ('%s', %s, 0)""" % (username, row[0])

        count = cursor_insert.execute(insert_query)
        conn.commit()

        print("Record inserted successfully into table: ", username, row[0], count)

        cursor_insert.close()

    conn.close()

def init_questions_chapter_wise_sqlite(username, chapter):
    conn = get_connection_sqlite()
    pairids = conn.execute("""select pair_id from ques_info where ROUND(chapter, 1) = {}""".format(chapter))
    print("From init_questions_chapter_wise(): Inserting records for chapter: ", chapter)

    for row in pairids:

        cursor_insert = conn.cursor()


        delete_query = """DELETE FROM attempted_hindi_to_eng_ques
                            WHERE username = '{}' and pair_id = {}""".format(username, row[0])

        count = cursor_insert.execute(delete_query)

        count = cursor_insert.execute(delete_query).rowcount
        print("Record deleted successfully from table: ", username, row[0], count)

        sqlite_insert_query = """INSERT INTO attempted_hindi_to_eng_ques
                            (username, pair_id, flag)
                            VALUES
                            ('{}', {}, 0)""".format(username, row[0])

        count = cursor_insert.execute(sqlite_insert_query)

        print("Record inserted successfully into table: ", username, row[0], count.rowcount)

        conn.commit()

        cursor_insert.close()
    conn.close()


def load_next_ques_chapter_wise_mysql(username, chapter):
    conn = get_mysql_connection()  # Use MySQL connection

    query = """
SELECT hq.pair_id, hq.hindi, hq.english
FROM hindi_to_english_ques_bank hq
JOIN (
    SELECT atq.pair_id
    FROM attempted_hindi_to_eng_ques atq
    JOIN ques_info qi ON atq.pair_id = qi.pair_id
    WHERE atq.username = '%s' AND atq.flag = 0 AND ROUND(qi.chapter, 1) = %s
    ORDER BY RAND()
    LIMIT 1
) subquery ON hq.pair_id = subquery.pair_id;
""" % (username, chapter)

    app.logger.info("load_next_ques_chapter_wise_mysql: query: " + query)
    app.logger.info("username: " + username)
    app.logger.info("chapter: " + str(chapter))


    # Execute the query using parameterized inputs
    cursor = conn.cursor()
    cursor.execute(query)

    row = cursor.fetchone()
    print(row)
    cursor.close()
    conn.close()

    if row:
        pair_id, hindi, english = row
    else:
        pair_id, hindi, english = -1, -1, -1

    return pair_id, hindi, english



def load_next_ques_chapter_wise_sqlite(username, chapter):
    conn = get_connection_sqlite()

    query = """
SELECT pair_id, hindi, english
FROM hindi_to_english_ques_bank
WHERE pair_id IN (
    SELECT pair_id
    FROM attempted_hindi_to_eng_ques
    WHERE username = ? AND flag = 0
      AND pair_id IN (SELECT pair_id FROM ques_info WHERE ROUND(chapter, 1) = ?)
    ORDER BY RANDOM()
    LIMIT 1
);
"""

    print("query: " + query)
    print(username)
    print(chapter)


    # Execute the query using parameterized inputs
    cursor = conn.execute(query, (username, chapter))

    row = cursor.fetchone()
    print(row)
    cursor.close()
    conn.close()

    if row:
        pair_id, hindi, english = row
    else:
        pair_id, hindi, english = -1, -1, -1

    return pair_id, hindi, english


@app.route('/next_ques_chapter_wise_mysql', methods=['GET', 'POST'])
@cross_origin()
def next_ques_chapter_wise_mysql():
    print("request.get_data(): " + str(request.get_data()))

    d = str(request.get_data())[2:-1].split('&') # bytes to str
    e = {}
    for i in d:
        e[i.split("=")[0]] = i.split("=")[1]

    print('e: ' + str(e))

    conn = get_mysql_connection()  # Use MySQL connection

    print('Database opened by next_ques_chapter_wise_mysql()')

    username = e['username']
    chapter = e['chapter']

    pair_id, hindi, english = load_next_ques_chapter_wise_mysql(username, chapter)

    if pair_id == -1:
        reset_attempted_questions_for_this_user_mysql(conn, username)
        pair_id, hindi, english = load_next_ques_chapter_wise_mysql(username, chapter)

    app.logger.info("pair_id: " + str(pair_id))
    app.logger.info("hindi: " + str(hindi))
    app.logger.info("english: " + str(english))

    if pair_id == -1 or pair_id == '-1':
        init_questions_chapter_wise_mysql(username, chapter)
        pair_id, hindi, english = load_next_ques_chapter_wise_mysql(username, chapter)

    app.logger.info("username: " + str(username))
    app.logger.info("pair_id: " + str(pair_id))
    app.logger.info("hindi: " + str(hindi))
    app.logger.info("english: " + str(english))

    cursor_insert = conn.cursor()


    update_query = """UPDATE attempted_hindi_to_eng_ques
        SET flag = 1
        WHERE username = '%s' AND pair_id = %s""" % (username, pair_id)

    app.logger.info('next_ques_chapter_wise_mysql: update_query: ' + update_query)

    count = cursor_insert.execute(update_query)
    conn.commit()

    print("Record update successful: " + str(cursor_insert.rowcount))

    print('Operation done successfully')

    conn.close()

    rtnVal = {
        'pair_id': pair_id,
        'hindi': hindi,
        'english': english
    }

    return jsonify(rtnVal)


@app.route('/next_ques_chapter_wise_sqlite', methods=['GET', 'POST'])
@cross_origin()
def next_ques_chapter_wise_sqlite():

    print("request.get_data(): " + str(request.get_data()))
    #app.logger.info("request.get_data(): " + str(request.get_data()))

    d = str(request.get_data())[2:-1].split('&') # bytes to str
    e = {}
    for i in d:
        e[i.split("=")[0]] = i.split("=")[1]

    print('e: ' + str(e))
    #app.logger.info('e: ' + str(e))


    conn = get_connection_sqlite()

    print('Database opened by next_ques_chapter_wise()')
    #app.logger.info('Database opened by next_ques_chapter_wise()')

    # username = session.get('username', 'na')
    username = e['username']
    chapter = e['chapter']

    pair_id, hindi, english = load_next_ques_chapter_wise_sqlite(username, chapter)

    if pair_id == -1:
        reset_attempted_questions_for_this_user_sqlite(conn, username)
        pair_id, hindi, english = load_next_ques_chapter_wise_sqlite(username, chapter)

    if pair_id == -1:
        init_questions_chapter_wise_sqlite(username, chapter)
        pair_id, hindi, english = load_next_ques_chapter_wise_sqlite(username, chapter)

    app.logger.info("username: " + str(username))
    app.logger.info("pair_id: " + str(pair_id))
    app.logger.info("hindi: " + str(hindi))
    app.logger.info("english: " + str(english))

    cursor_insert = conn.cursor()

    update_query = """update attempted_hindi_to_eng_ques
        set flag = 1
        where username = '{}' and pair_id = {}""".format(username, pair_id)

    app.logger.info('next_ques_chapter_wise_sqlite: update_query: ' + update_query)

    count = cursor_insert.execute(update_query)
    conn.commit()

    print("Record update successful: " + str(cursor_insert.rowcount))

    print('Operation done successfully')

    conn.close()

    rtnVal = {
        'pair_id': pair_id,
        'hindi': hindi,
        'english': english
    }

    return jsonify(rtnVal)


@app.route('/write_to_attempt_log_mysql', methods=['GET', 'POST'])
@cross_origin()
def write_to_attempt_log_mysql():
    app.logger.info("request.get_data(): " + str(request.get_data()))

    d = str(request.get_data())[2:-1].split('&') # bytes to str
    e = {}
    for i in d:
        e[i.split("=")[0]] = i.split("=")[1]

    app.logger.info('e: ' + str(e))

    conn = get_mysql_connection()  # Use MySQL connection

    app.logger.info('Opened database successfully')

    username = e['username']
    pair_id = e['pair_id']
    result = e['result']

    current_datetime = datetime.now()
    current_datetime = current_datetime.strftime("%Y-%m-%d %H:%M:%S") # MySQL Datetime Format

    app.logger.info("username: " + str(username))
    app.logger.info("pair_id: " + str(pair_id))
    app.logger.info("result: " + str(result))
    if(result == 'TRUE'):
        result = 1
    else:
        result = 0
    cursor_insert = conn.cursor()

    insert_query = """INSERT INTO attempt_log (attempt_time, username, pair_id, result)
        VALUES (%s, %s, %s, %s)"""

    app.logger.info('insert_query: ' + insert_query)

    count = cursor_insert.execute(insert_query, (current_datetime, username, pair_id, result))
    conn.commit()

    app.logger.info("Record insertion successful: " + str(cursor_insert.rowcount))

    app.logger.info('Operation done successfully')

    conn.close()

    return "True"


@app.route('/write_to_attempt_log_sqlite', methods=['GET', 'POST'])
@cross_origin()
def write_to_attempt_log_sqlite():

    app.logger.info("request.get_data(): " + str(request.get_data()))

    d = str(request.get_data())[2:-1].split('&') # bytes to str
    e = {}
    for i in d:
        e[i.split("=")[0]] = i.split("=")[1]

    app.logger.info('e: ' + str(e))

    conn = get_connection_sqlite()

    app.logger.info('Opened database successfully')

    # username = session.get('username', 'na')
    username = e['username']
    pair_id = e['pair_id']
    result = e['result']


    current_datetime = datetime.now()
    current_datetime = current_datetime.strftime("%Y-%m-%d %H:%M:%S") # SQLite Datetime Format

    app.logger.info("username: " + str(username))
    app.logger.info("pair_id: " + str(pair_id))
    app.logger.info("result: " + str(result))

    cursor_insert = conn.cursor()
        # INSERT INTO hindi_to_english_ques_bank (hindi, english) VALUES('हाथ ताली बजाने के लिए', 'Hands To Clap');

    insert_query = """insert into attempt_log (attempt_time, username, pair_id, result)
        values ( '{}', '{}', {}, '{}' )""".format(current_datetime, username, pair_id, result)

    app.logger.info('insert_query: ' + insert_query)

    count = cursor_insert.execute(insert_query)
    conn.commit()

    app.logger.info("Record insertion successful: " + str(cursor_insert.rowcount))

    app.logger.info('Operation done successfully')

    conn.close()

    return "True"


@app.route('/get_chapters_mysql', methods = ['GET', 'POST'])
@cross_origin()
def get_chapters_mysql():
    conn = get_mysql_connection()  # Use MySQL connection

    app.logger.info('Opened database successfully')

    query = """SELECT chapter, title, COUNT(pair_id) FROM ques_info GROUP BY chapter, title ORDER BY chapter"""

    app.logger.info("query: " + query)
    cursor = conn.cursor()
    cursor.execute(query)

    l = []

    for row in cursor:
        d = { 'ch_num': row[0], 'ch_name': row[1], 'qcount': row[2] }
        l.append(d)

    conn.close()  # Close the connection

    return jsonify(l)


@app.route('/get_chapters_sqlite', methods = ['GET', 'POST'])
@cross_origin()
def get_chapters_sqlite():

    conn = get_connection_sqlite()

    app.logger.info('Opened database successfully')

    # query = """select distinct chapter, title from ques_info order by chapter"""
    query = """select chapter, title, count(pair_id) from ques_info group by chapter, title order by chapter"""

    app.logger.info("query: " + query)
    cursor = conn.execute(query)

    l = []

    for row in cursor:
        d = { 'ch_num': row[0], 'ch_name': row[1], 'qcount': row[2] }
        l.append(d)

    return jsonify(l)

@app.route('/get_user_progress_mysql', methods = ['GET', 'POST'])
@cross_origin()
def get_user_progress_mysql():
    username = request.json['username']
    
    # Connect to MySQL database
    conn = get_mysql_connection()  # Use MySQL connection

    cursor = conn.cursor()

    # Execute a query to fetch data from the table
    query = f"""
SELECT a.username, a.att_time AS attempt_time, a.cnt AS total, b.cnt AS true_cnt, a.cnt - b.cnt AS false_cnt
FROM
(
    SELECT COUNT(*) AS cnt, username, DATE(attempt_time) AS att_time FROM attempt_log GROUP BY username, DATE(attempt_time)
) a
JOIN
(
    SELECT COUNT(*) AS cnt, username, DATE(attempt_time) AS att_time
    FROM attempt_log
    WHERE result = 1
    GROUP BY username, DATE(attempt_time)
) b
ON a.username = b.username AND a.att_time = b.att_time
WHERE a.username = '{username}'
"""

    cursor.execute(query)

    app.logger.info("query: " + query)

    data = cursor.fetchall()

    # Get the column names from the cursor.description
    columns = [desc[0] for desc in cursor.description]

    # Convert data to a list of dictionaries
    data_list = [dict(zip(columns, row)) for row in data]

    # Convert the list of dictionaries to JSON
    # Convert date fields to string (ISO format)
    for record in data_list:
        for key, value in record.items():
            if isinstance(value, date):
                record[key] = value.isoformat()  # Converts to "YYYY-MM-DD"

    # Serialize to JSON
    json_data = json.dumps(data_list, indent=2)

    # Close the database connection
    conn.close()

    # Print or use the JSON data as needed
    return jsonify(json_data)

"""SELECT a.username, a.att_time AS attempt_time, a.cnt AS total, b.cnt AS true_cnt, a.cnt - b.cnt AS false_cnt
FROM
(
    SELECT COUNT(*) AS cnt, username, DATE(attempt_time) AS att_time FROM attempt_log GROUP BY username, DATE(attempt_time)
) a
JOIN
(
    SELECT COUNT(*) AS cnt, username, DATE(attempt_time) AS att_time
    FROM attempt_log
    WHERE result = 'TRUE'
    GROUP BY username, DATE(attempt_time)
) b
ON a.username = b.username AND a.att_time = b.att_time
WHERE a.username != ''
"""

@app.route('/get_user_progress_sqlite', methods = ['GET', 'POST'])
@cross_origin()
def get_user_progress_sqlite():

    # Connect to SQLite database
    conn = get_connection_sqlite()

    cursor = conn.cursor()

    # Execute a query to fetch data from the table

    query = """
select a.username, a.att_time as attempt_time, a.cnt as total, b.cnt as true_cnt, a.cnt - b.cnt as false_cnt
from
(
    SELECT COUNT(*) as cnt, username, strftime('%Y-%m-%d', attempt_time) as att_time from attempt_log group by username, date(attempt_time)
) a
JOIN

(
    SELECT COUNT(*) as cnt, username, strftime('%Y-%m-%d', attempt_time) as att_time
    from attempt_log
    where result = 'TRUE'
    group by username, date(attempt_time)
) b

on a.username = b.username and a.att_time = b.att_time

where a.username != ''"""

    cursor.execute(query)

    app.logger.info("query: " + query)

    data = cursor.fetchall()

    # Get the column names from the cursor.description
    columns = [desc[0] for desc in cursor.description]

    # Convert data to a list of dictionaries
    data_list = [dict(zip(columns, row)) for row in data]

    # Convert the list of dictionaries to JSON
    json_data = json.dumps(data_list, indent=2)

    # Close the database connection
    conn.close()

    # Print or use the JSON data as needed
    return jsonify(json_data)















def load_next_ques_chapter_and_difficulty_wise(username, chapter, difficulty):
    conn = get_mysql_connection()  # Use MySQL connection

    if difficulty == 'Easy':
        english_length = "< 5"
    elif difficulty == 'Medium':
        english_length = "= 5"
    elif difficulty == 'Hard':
        english_length = "> 5"

    query = """
SELECT hq.pair_id, hq.hindi, hq.english
FROM hindi_to_english_ques_bank hq
JOIN (
    SELECT atq.pair_id
    FROM attempted_hindi_to_eng_ques atq
    JOIN ques_info qi ON atq.pair_id = qi.pair_id
    JOIN hindi_to_english_ques_bank ON hindi_to_english_ques_bank.pair_id = qi.pair_id

    WHERE atq.username = '%s' AND atq.flag = 0 AND ROUND(qi.chapter, 1) = %s
    AND LENGTH(TRIM(hindi_to_english_ques_bank.english)) - LENGTH(REPLACE(TRIM(hindi_to_english_ques_bank.english), ' ', '')) + 1 %s
    ORDER BY RAND()
    LIMIT 1
) subquery ON hq.pair_id = subquery.pair_id;
""" % (username, chapter, english_length)

    app.logger.info("load_next_ques_chapter_and_difficulty_wise: query: " + query)
    app.logger.info("username: " + username)
    app.logger.info("chapter: " + str(chapter))
    app.logger.info("difficulty : " + difficulty)
    app.logger.info("english_length : " + english_length)


    # Execute the query using parameterized inputs
    cursor = conn.cursor()
    cursor.execute(query)

    row = cursor.fetchone()
    print(row)
    cursor.close()
    conn.close()

    if row:
        pair_id, hindi, english = row
    else:
        pair_id, hindi, english = -1, -1, -1

    return pair_id, hindi, english


def reset_attempted_questions_for_this_user_chapter_difficulty(conn, username, chapter, difficulty):

    if difficulty == 'Easy':
        english_length = "< 5"
    elif difficulty == 'Medium':
        english_length = "= 5"
    elif difficulty == 'Hard':
        english_length = "> 5"

    cursor = conn.cursor()

    update_query = """update attempted_hindi_to_eng_ques
        set flag = 0 where username = '%s'
        AND pair_id in (select hindi_to_english_ques_bank.pair_id 
        FROM hindi_to_english_ques_bank 
        JOIN ques_info on hindi_to_english_ques_bank.pair_id = ques_info.pair_id 
        WHERE chapter = '%s' 
        AND LENGTH(TRIM(english)) - LENGTH(REPLACE(TRIM(english), ' ', '')) + 1 %s)""" % (username, chapter, english_length)

    app.logger.info('reset_attempted_questions_for_this_user_chapter_difficulty: update_query: ' + update_query)

    count = cursor.execute(update_query)

    app.logger.info('Update count: ' + str(count))
    conn.commit()

    cursor.close()


@app.route('/next_ques_chapter_and_difficulty_wise', methods=['POST'])
@cross_origin()
def next_ques_chapter_and_difficulty_wise():
    print("Request data: " + str(request.data))
    app.logger.info("request.get_data(): " + str(request.get_data()))

    d = str(request.get_data())[2:-1].split('&') # bytes to str
    e = {}
    for i in d:
        e[i.split("=")[0]] = i.split("=")[1]

    app.logger.info('e: ' + str(e))

    username = e['username']
    chapter = e['chapter']
    difficulty = e['difficulty']

    conn = get_mysql_connection()  # Use MySQL connection

    print('Database opened by next_ques_chapter_and_difficulty_wise()')

    pair_id, hindi, english = load_next_ques_chapter_and_difficulty_wise(username, chapter, difficulty)

    if pair_id == -1:
        reset_attempted_questions_for_this_user_chapter_difficulty(conn, username, chapter, difficulty)
        pair_id, hindi, english = load_next_ques_chapter_and_difficulty_wise(username, chapter, difficulty)

    app.logger.info("pair_id: " + str(pair_id))
    app.logger.info("hindi: " + str(hindi))
    app.logger.info("english: " + str(english))

    if pair_id == -1 or pair_id == '-1':
        init_questions_chapter_wise_mysql(username, chapter)
        pair_id, hindi, english = load_next_ques_chapter_and_difficulty_wise(username, chapter, difficulty)

    app.logger.info("username: " + str(username))
    app.logger.info("pair_id: " + str(pair_id))
    app.logger.info("hindi: " + str(hindi))
    app.logger.info("english: " + str(english))

    cursor = conn.cursor()


    update_query = """UPDATE attempted_hindi_to_eng_ques
        SET flag = 1
        WHERE username = '%s' AND pair_id = %s""" % (username, pair_id)

    app.logger.info('next_ques_chapter_wise_mysql: update_query: ' + update_query)

    count = cursor.execute(update_query)
    conn.commit()

    app.logger.info('Update count: ' + str(count))

    print('Operation (next_ques_chapter_and_difficulty_wise) done successfully')

    conn.close()

    return jsonify({
        'pair_id': pair_id,
        'hindi': hindi,
        'english': english
    })


@app.route('/get_qcount_for_chapters_and_difficulty_wise', methods = ['GET', 'POST'])
@cross_origin()
def get_qcount_for_chapters_and_difficulty_wise():
    conn = get_mysql_connection()  # Use MySQL connection

    app.logger.info('Opened database successfully')

    query = """SELECT chapter, title, COUNT(a.pair_id),
SUM(CASE WHEN LENGTH(TRIM(b.english)) - LENGTH(REPLACE(TRIM(b.english), ' ', '')) + 1  < 5 THEN 1 ELSE 0 END) AS easy,
SUM(CASE WHEN LENGTH(TRIM(b.english)) - LENGTH(REPLACE(TRIM(b.english), ' ', '')) + 1  = 5 THEN 1 ELSE 0 END) AS medium,
SUM(CASE WHEN LENGTH(TRIM(b.english)) - LENGTH(REPLACE(TRIM(b.english), ' ', '')) + 1  > 5 THEN 1 ELSE 0 END) AS hard
FROM ques_info a
    JOIN hindi_to_english_ques_bank b ON a.pair_id = b.pair_id 
    GROUP BY chapter, title ORDER BY chapter;"""

    app.logger.info("query: " + query)
    cursor = conn.cursor()
    cursor.execute(query)

    l = []

    for row in cursor:
        d = { 
            'ch_num': row[0], 
            'ch_name': row[1], 
            'qcount': row[2],
            'easy': row[3],
            'medium': row[4],
            'hard': row[5]
        }
        l.append(d)

    conn.close()  # Close the connection

    return jsonify(l)



if __name__=='__main__':
    app.run(debug=True, port=6050)
