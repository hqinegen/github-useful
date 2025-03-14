import os
import sys
import re
import csv
import logging
import datetime
import subprocess
from datetime import timedelta
from functools import wraps
from subprocess import PIPE, CalledProcessError, check_call, Popen, check_output
import shlex
import pdb

# Third-Party Library Imports
from flask import (
    Flask, redirect, url_for, render_template, jsonify,
    request, make_response, session, flash
)
from flask_mysqldb import MySQL
import yaml
from ldap3 import Server, Connection, SIMPLE, SYNC, ALL
import pysvn
from filelock import FileLock


app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

log = logging.getLogger('app.authenticator')
# Configure
db = yaml.load(open('db.yaml'))
app.config['MYSQL_HOST'] = db['mysql_host']
app.config['MYSQL_USER'] = db['mysql_user']
app.config['MYSQL_PASSWORD'] =db['mysql_password']
app.config['MYSQL_DB'] = db['mysql_db']

mysql = MySQL(app)

svncodedir = "C:/Users/hqin/UniqueIDserver/code/"
IDfilesdir = "C:/Users/hqin/UniqueIDserver/branch_ID_files/"
exepath = "C:/Users/hqin/UniqueIDserver/server/"

@app.route('/')
def index():
    
    if 'username' in session:
        template = 'indexupdate.html'
        template_var = 'update_item'
    else:
        template = 'index.html'
        template_var = 'message_item'

    # Open a cursor and execute the query
    cur = mysql.connection.cursor()
    result_value = cur.execute("SELECT * FROM message_table")
    message_item = cur.fetchall() if result_value > 0 else []
    cur.close()  # Close the cursor after fetching data

    
    if template_var == 'update_item':
        return render_template(template, update_item=message_item)
    else:
        return render_template(template, message_item=message_item)
   


@app.route('/gname/')
def visits():
    if 'username' in session:
        return render_template('username.html', uname=session.get('username'), checkoutdir=session.get('svn_dir'), bname=session.get('branchname'))
    else:
        return render_template('username.html', uname='None')


def authenticate(domain, user, password):
    authenticated = False
    try:
        server = Server(domain, get_info=ALL)
        connection = Connection(server, authentication=SIMPLE, user=user, password=password,auto_bind=True)
        connection.open()
        connection.bind()
        log.debug("LDAP Result => %s", connection.result)
        authenticated = connection.result['result'] == 0
    except Exception:
        log.exception("Failed to authenticate user", exc_info=True)
    return authenticated
   
def fetch_and_render_messages(template):
    #Helper function to fetch messages from DB and render a template.
    with mysql.connection.cursor() as cur:
        result_value = cur.execute("SELECT * FROM message_table")
        message_item_update = cur.fetchall() if result_value > 0 else []

    return render_template(template, update_item=message_item_update)   
    
   
@app.route('/login', methods=['GET','POST'])
def login():
    # Check if user is already logged in
    if session.get('username'):
        return fetch_and_render_messages('indexupdate.html')

    if request.method == 'POST':
        form = request.form
        name = form.get('name')
        password = form.get('password')

        if authenticate('hdspoole.local', name, password):
            session['username'] = name
            session['passwd'] = password
            return fetch_and_render_messages('indexupdate.html')
        else:
            return render_template('loginfailed.html', uname=name)

    return render_template('login.html')    


@app.route('/logout', methods=['GET','POST'])
def logout():
    #Logs out the user by clearing the session and rendering the logout page.
    session.pop('username', None)
    return render_template('logout.html')
    


@app.route('/details', methods=['GET', 'POST'])
def details():
    #Handles fetching and updating message details based on log ID.
    
    id = request.args.get('logId')
    if not id:
        return jsonify(result="Error: logId parameter is missing")
       

    with mysql.connection.cursor() as cur:
        if request.method == 'GET':
            if cur.execute("SELECT * FROM message_table WHERE log_id = %s", (id,)):
                detail_item = cur.fetchall()
                return render_template('details.html', details=detail_item)
            return jsonify(result="No records found.") #Handle case where no matching log_id exists

        elif request.method == 'POST':
            form = request.form
            new_comment = form.get('comment')  # Use `.get()` to avoid KeyError

            if new_comment:
                cur.execute("UPDATE message_table SET comment = %s WHERE log_id = %s", (new_comment, id))
                mysql.connection.commit()
                return render_template('updatedetails.html', newid=id, newcomment=new_comment)
            return jsonify(result="Error: Comment cannot be empty.")  # Handle case where comment is missing
            
            
@app.route('/update', methods=['GET', 'POST'])
def update():
    #Handles fetching and updating message details based on log ID
    log_id = request.args.get('logId')
    if not log_id:
        return jsonify(result="Error: logId parameter is required.")  # Handle missing logId

    if request.method == 'GET':
        return fetch_details(log_id)

    return process_update(log_id)


def fetch_details(log_id):
    #Fetches message details for a given log ID and renders update form
    with mysql.connection.cursor() as cur:
        if cur.execute("SELECT * FROM message_table WHERE log_id = %s", (log_id,)):
            detail_item = cur.fetchall()
            return render_template('update.html', update_item=detail_item)

    return jsonify(result="No records found for this log ID.") # Handle missing log ID in DB


def process_update(log_id):
    #Processes form submission for updating message details.
    form = request.form
    command = form.get('command')  # Use .get() to avoid KeyError

    if command == 'cancel':
        return render_template('step.html')  # Redirect to step page

    new_details = form.get('id_details')
    new_comment = form.get('comment')

    if not new_details or not new_comment:
        return jsonify(result="Error: Both log_details and comment are required.")  # Handle empty input

    with mysql.connection.cursor() as cur:
        cur.execute(
            "UPDATE message_table SET log_details = %s, comment = %s WHERE log_id = %s",
            (new_details, new_comment, log_id),
        )
        mysql.connection.commit()

    return render_template('updatedetails.html', newid=log_id, newcomment=new_comment)



@app.route('/step')
def step():
    return render_template('step.html')


@app.route('/background_process')
def background_process():

    #svn check check in the code
    brname = request.args.get('branch_name', 0, type=str)

    if not brname:
        return jsonify(result="Please input SVN branch name for checking out")
    
    try:
        subprocess.check_call(["python", "svncheck.py",  session['username'], session['passwd'],brname, svncodedir+brname])
        return jsonify(result=brname)
    except  subprocess.CalledProcessError as e:
        print("session error output")
        print(e)
        return jsonify(result=str(e))
        


patterns =  [
    'STORAGE_HANDLER_LOG',
    'APPLICATION_HANDLER_LOG',
    'FailureResponseAdapter',
    'LOG',
    'LOG_STATE',
    'failure',
    'initialiseMessage',
    'LOG_SESSION',
    'HBB_LOG',
    'HBB_LOG_WITH_TAGS',
    'HBB_LOG_WITH_ATTACHMENT'
] 

def assign_id(pattern, brname):
    #Assigns an ID based on log file processing and stores extracted data in a CSV file.
    
    logdir = os.path.join(IDfilesdir, brname, "")
    maxid_path = os.path.join(exepath, "maxid.txt")
    revision_path = os.path.join(logdir, "revision.txt")
    logfilename = os.path.join(logdir, pattern)

    # Read maxid from file
    numberUn = read_integer_from_file(maxid_path)
    print(f"Max ID: {numberUn}")

    # Read revision ID from file
    rvID = read_string_from_file(revision_path)
    print(f"Revision ID: {rvID}")

    print(f"Checking.. {logfilename}")

    # Process log file if it exists and is not empty
    if os.path.exists(logfilename) and os.path.getsize(logfilename) > 0:
        process_log_file(logfilename, pattern, brname, logdir, numberUn)

    # Update maxid.txt with new numberUn
    write_integer_to_file(maxid_path, numberUn)

    # Process logfileparse
    logfileparse = logfilename + "File"
    if os.path.exists(logfileparse) and os.path.getsize(logfileparse) > 0:
        process_logfileparse(logfileparse, pattern, brname, logdir, rvID, numberUn)


def read_integer_from_file(filepath):
    #Reads an integer value from a file.
    with open(filepath, "r") as file:
        return int(file.readline().strip())


def read_string_from_file(filepath):
    #Reads a string value from a file.
    with open(filepath, "r") as file:
        return file.readline().strip()


def write_integer_to_file(filepath, value):
    #Writes an integer value to a file.
    with open(filepath, "w") as file:
        file.write(str(value))


def process_log_file(logfilename, pattern, brname, logdir, numberUn):
    #Processes a log file and assigns IDs.
    with open(logfilename, "r") as file:
        for line in file:
            line = line.strip()
            message = line.split(":")
            messageline = message[3].strip()  # Remove surrounding spaces

            if not re.search(r"\A/\*", messageline) and not re.search(r"\A//", messageline):
                filename = f"{message[0]}:{message[1]}"
                first_line_num = int(message[2])
                last_line_num = first_line_num + 8
                numberUn += 1
                print(f"New Assigned ID: {numberUn}")

                subprocess.call([
                    os.path.join(exepath, "replace.bat"),
                    str(first_line_num), str(last_line_num), filename, str(numberUn),
                    pattern, brname, "7.0", logdir
                ])


def process_logfileparse(logfileparse, pattern, brname, logdir, rvID, numberUn):
    #Processes logfileparse and writes parsed data to CSV.
    with open(logfileparse, "r") as file:
        for bline in file:
            items = bline.split('$')
            spterm = pattern + '('
            nstr = items[0].split(spterm)[1]

            # Clean extracted message
            nnstr = clean_message(nstr, pattern)

            # Split into database fields
            dbitems = nnstr.split(',')
            nitem = create_database_entry(dbitems, pattern, items, brname, rvID, numberUn)

            # Write to CSV
            with open(os.path.join(logdir, 'branchnew.csv'), 'a') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(nitem)


def clean_message(nstr, pattern):
    #Cleans extracted message based on pattern type.
    if re.search("initialiseMessage", pattern):
        tmpitems = nstr.split('<<')
        return re.sub(r'\)', '', tmpitems[0])
    else:
        cleaned_str = re.sub(r'\);', '', nstr)

        if re.search("FailureResponseAdapter", pattern) and re.search(r'\d{1,5}\)', nstr):
            cleaned_str = re.sub(r'\).*<<', ',', nstr)

        if re.search("HBB_LOG", pattern):
            cleaned_str = cleaned_str.split(',', 1)[-1]

        return cleaned_str


def create_database_entry(dbitems, pattern, items, brname, rvID, numberUn):
    #Creates a formatted database entry list.
    nitem = [None] * 14
    nitem[0] = int(dbitems[0])

    if re.search("HANDLER", pattern):
        nitem[1], nitem[2], nitem[3] = dbitems[1], pattern, dbitems[2]
    elif re.search("FailureResponseAdapter", pattern):
        nitem[1], nitem[2], nitem[3] = "Error", "Orchestration Framework", dbitems[1]
    elif pattern == 'LOG':
        nitem[1], nitem[2], nitem[3] = dbitems[2], dbitems[1], dbitems[3]
    elif re.search("failure", pattern):
        nitem[1], nitem[2], nitem[3] = "Error", "Orchestration Framework", dbitems[1]
    elif pattern == 'LOG_STATE':
        nitem[1], nitem[2], nitem[3] = "Information", dbitems[1] + "test", dbitems[2]
    elif re.search("initialiseMessage", pattern):
        nitem[1], nitem[2], nitem[3] = dbitems[2], dbitems[1], dbitems[1]  # Assumes tmpitems[1] should be used
    elif pattern == 'LOG_SESSION':
        nitem[1], nitem[2], nitem[3] = dbitems[2], dbitems[1], dbitems[5]
    elif re.search("HBB_LOG", pattern):
        serv = re.sub(r'^.*:', '', dbitems[1])
        nitem[1], nitem[2], nitem[3] = serv, pattern, dbitems[2]

    # Remove commas from log messages to prevent CSV issues
    nitem[3] = re.sub(',', '', nitem[3])
    nitem[4] = ''

    # Extract subfolder path
    subf = items[1].split(f"{brname}/", 1)
    nitem[5] = subf[1] if len(subf) > 1 else ""

    nitem[6] = int(items[2])
    nitem[7] = ''
    nitem[8] = session['username']
    nitem[9] = items[3]
    nitem[10] = items[4].strip()
    nitem[11] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    nitem[12] = rvID
    nitem[13] = "none"

    return nitem


@app.route('/background_process_assign')
def background_process_assign():


    brname = request.args.get('branch_name2', 0, type=str)

    if not brname:
        return jsonify(result="Please input SVN branch name for assign")
    try:

        cur = mysql.connection.cursor()
        result_value = cur.execute("SELECT MAX(log_id) FROM message_table")
        if result_value > 0:
            maxidlog = cur.fetchone()
            for row in maxidlog:
                print(row)
                sys.stdout.flush()
                file=open(exepath+"maxid.txt","w")
                file.write(str(row))
                file.close()

        #print("check_call assign")
        subprocess.check_call([exepath+"assign.bat", brname ])


        with FileLock(exepath +"maxid.txt.lock"):
            
            print("Lock acquired.")
            for pattern in patterns:
                assign_id(pattern, brname)
                
           
            fileFID = open( exepath+"maxid.txt", "r")
            numberFID = fileFID.readline()
            numberFID = numberFID.rstrip('\n')

            numberFUn = int(numberFID)
            print(numberFUn)
            sys.stdout.flush()
            fileFID.close()

        if (row == int(numberFID)):
            returnstr = "Nothing to update"
        else:
            initnumber = row+1;
            returnstr = "Assigned ID from" + str(initnumber) + " to " + numberFID
        return jsonify(resultid=returnstr)

    except subprocess.CalledProcessError as e:
        print("error code", e)
        return jsonify(resultid = str(e))



@app.route('/background_validate_database')
def background_validate_database():
    #Validates database by checking if the branch CSV exists and loads it into MySQL.
    
    validatebr = request.args.get('valname', type=str)

    # Validate input
    if not validatebr:
        return jsonify(result="Please input SVN branch name")

    newIDfile = os.path.join(IDfilesdir, validatebr, "branchnew.csv")

    # Check if the file exists
    if not os.path.exists(newIDfile):
        return jsonify(resultv="Nothing to update")

    try:
        with mysql.connection.cursor() as cur:
            query = (
                "LOAD DATA LOCAL INFILE %s INTO TABLE message_table "
                "FIELDS TERMINATED BY ',' LINES TERMINATED BY '\n' "
                "(log_id, log_severity, log_category, log_text, arglist, file_name, "
                "file_line, log_details, user, branch, target, lastmodified, version, comment)"
            )
            result_value = cur.execute(query, (newIDfile,))

        # Return appropriate response
        if result_value > 0:
            return jsonify(resultv="Validate Database OK, you can continue to check in the changes into branch and update the UniqueID database")
        else:
            return jsonify(resultv="Nothing to update in database")

    except Exception as e:
        return jsonify(resultv=f"Error: {str(e)}")
        





@app.route('/background_update_database')
def background_update_database():
    #Updates the database by checking in SVN and loading data from a CSV file.
    
    updatebr = request.args.get('upname', type=str)

    # Validate input
    if not updatebr:
        return jsonify(result="Please input SVN branch name")

    newIDfile = os.path.join(IDfilesdir, updatebr, "branchnew.csv")

    # Run SVN check-in command
    try:
        subprocess.check_call([
            "python", "svncheckin.py",
            session.get('username', ''), session.get('passwd', ''), 
            os.path.join(svncodedir, updatebr)
        ])
    except subprocess.CalledProcessError as e:
        print("Session error output:", e)
        return jsonify(resultc=str(e))

    # Ensure file exists before updating database
    if not os.path.exists(newIDfile):
        return jsonify(resultc="Error: branchnew.csv file not found, database update aborted.")

    # Load data into MySQL database
    try:
        with mysql.connection.cursor() as cur:
            query = (
                "LOAD DATA LOCAL INFILE %s INTO TABLE message_table "
                "FIELDS TERMINATED BY ',' LINES TERMINATED BY '\n' "
                "(log_id, log_severity, log_category, log_text, arglist, file_name, "
                "file_line, log_details, user, branch, target, lastmodified, version, comment)"
            )
            result_value = cur.execute(query, (newIDfile,))

            if result_value > 0:
                mysql.connection.commit()
                return jsonify(resultc="Update runs fine")
            else:
                return jsonify(resultc="No new data to update in the database.")

    except Exception as e:
        return jsonify(resultc=f"Database update failed: {str(e)}")


if __name__ == '__main__':
    app.run(debug=True, host='', port=8083)

