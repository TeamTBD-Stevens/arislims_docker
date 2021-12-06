import os
from flask_mysqldb import MySQLdb
from pandas.core.dtypes.missing import notnull
from werkzeug.local import F
from application import app, mysql
from flask import request, render_template, json, Response, session, send_file
import datetime as dt
from werkzeug.utils import secure_filename
import pandas as pd
import numpy as np
from initdb import updateSamples

# the samplesData variable is what each page uses to load relevant samples pertaining to each page's functionality
# the modID variable is how sample selections are preserved between pages
# The only case this rule is broken is with reporting samples that weren't found using the search by file functionality
# In this case since there is no id associated with these not found samples, a cookie is used


#variable that loads fridge data. For now fridges explicitly coded
fridgesData = ["Atlas -80C","Barracuda -80C","Cobra -80C","Dragon -80C","Elephant -80C","Falcon -80C","Emu 4C","Duck 4C","Condor 4C","Albatross 4C","Bluebird 4C","Fox -20C","Grizzly -20C","Jaguar -30C","Beetle 4C (mini)","Ant 4C (mini)","Iguana 4C (mini)","Ferret 4C","Eagle 4C","Dingo 4C (mini)","Chinchilla 4C (mini)","Hammerhead -20C (mini)","Coordinator 4C (mini)"]
#sort alphabetically
fridgesData.sort()
shelfData = ["A","B","C","D","E"]
rackData = ['1','2','3','4','5','6','7','8','9','10','11','12','N/A']

# If db is missing tables, create them

# labels for sample columns
sample_labels = ["Progeny_ID","Family_ID","Aliquot_Label","Sample_Type","Fridge_Name","Shelf_No","Rack_Label","Project_Name","Researcher_Name","Date_Taken_Out","Original_Fridge","Original_Shelf","Original_Rack","Original_Drawer","Original_Box","Original_Well","Collection_Date","flag","Low_DNA","comments","id"]

# admin and loggedin variables
loggedin = False

# Homepage / Dashboard
@app.route('/', methods=["GET","POST"])
@app.route('/index', methods=["GET","POST"])
@app.route('/home', methods=["GET","POST"])
def index():
    loggedin = False
    admin = False
    user = ''
    firstname = ''
    if 'username' in session:
        user = session['username']
        admin = True if session['usertype']=='ADMIN' else False
        firstname = session['firstname']
        loggedin = True
    samplesData = []
    messagesData = []
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if request.method == 'POST':
#        if admin:          ***2021_12_02: removing the "if admin" logic so that this page works for non-admin users***
        # Marking messages as resolved
        if request.form.get('markresolved'):
            markID = request.form.get('markresolved')
            cur.execute(f'UPDATE messages SET flag=\'resolved\' WHERE id=\'{markID}\'')
            mysql.connection.commit()
        # Posting messages
        elif request.form.get('message-subject'):
            author = f"\'{session['firstname']} {session['lastname'][0]}\'"
            sub_replaceapos = request.form.get('message-subject').replace('\'','\'\'') # replacing ' with '' so that apostrophes can be includede in messages
            subject = f"\'{sub_replaceapos}\'"
            body_replaceapos = request.form.get('message-body').replace('\'',"\'\'")
            body = f"\'{body_replaceapos}\'"
            flag = f"\'{request.form.get('flag')}\'"
            datetime = dt.datetime.now()
            cur.execute('INSERT INTO messages (author,subject,message,flag,date) VALUES ('+author+','+subject+','+body+','+flag+',\''+str(datetime)+'\')')
            mysql.connection.commit()

    # Counting number of samples taken out by each member
    cur.execute('SELECT Researcher_Name, COUNT(Researcher_Name) FROM samples WHERE Researcher_Name!=\'\' AND Date_Taken_Out!=\'None\' GROUP BY Researcher_Name')
    samplesData=cur.fetchall()
    # Fetching messages ordered by date, and appending resolved messages to the end
    cur.execute('SELECT * FROM messages WHERE flag=\'resolved\' ORDER BY date DESC')
    resolvedData = cur.fetchall() #This will be added to the end of messagesData so that all resolved messages are shown at the bottom of the table
    cur.execute('DELETE FROM messages WHERE date < now() - interval 30 DAY') # Delete all messages that are more than 30 days old
    mysql.connection.commit()
    cur.execute('SELECT * FROM messages WHERE flag!=\'resolved\' ORDER BY date DESC')
    messagesData = cur.fetchall()
    messagesData = messagesData + resolvedData
    cur.close()
        
    return render_template('index.html', index=True, samplesData=samplesData, messagesData=messagesData, loggedin=loggedin, admin=admin, user=user, firstname=firstname, date=dt.date.today())

# Login page
@app.route('/login', methods=["GET","POST"])
def login():
    msg = ''
    loggedin = False
    admin = False
    user = ''
    firstname = ''
    lastname = ''
    if 'username' in session:
        user = session['username']
        firstname = session['firstname']
        lastname = session['lastname']
        admin = True if session['usertype']=='ADMIN' else False
        loggedin = True
        return render_template('login.html', login=True, loggedin=loggedin, admin=admin, user=user, firstname=firstname, lastname=lastname, msg=msg)
    if request.method == 'POST':
        if 'username' in request.form and 'password' in request.form:
            username = request.form['username']
            password = request.form['password']
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cur.execute(f'SELECT * FROM users WHERE username = \'{username}\' AND password = \'{password}\'')
            acc = cur.fetchone()
            if acc:
                session['id'] = acc['id']
                session['username'] = acc['username']
                session['usertype'] = acc['usertype']
                session['firstname'] = acc['firstname']
                session['lastname'] = acc['lastname']
                session['samplesout'] = acc['samplesout']
                session['historic_samplesout'] = acc['historic_samplesout']
                session['historic_samplesret'] = acc['historic_samplesret']
                loggedin = True
                admin = True if session['usertype']=='ADMIN' else False
                user = session['username']
                firstname = session['firstname']
                lastname = session['lastname']
            else:
                msg = 'Invalid username/password, try again!'
    return render_template('login.html', login=True, loggedin=loggedin, admin=admin, user=user, firstname=firstname, lastname=lastname, msg=msg)

@app.route('/logout', methods=["GET","POST"])
def logout():
    if 'username' in session:
        keys = []
        for key in session:
            keys.append(key)
        for key in keys:
            session.pop(key)

    return render_template('logout.html')

@app.route('/register',methods=["GET","POST"])
def register():
    if 'username' in session:
        return 'Invalid access. Log out to register a new user.'
    loggedin=False
    if request.method == "POST":
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        admincheck = 'ADMIN' if request.form.get('admincheck') else 'USER'
        temp = [request.form.get('username'),request.form.get('password'), admincheck,request.form.get('firstname'),request.form.get('lastname')]
        values = ','.join(map("'{0}'".format,temp))
        cur.execute(f'INSERT INTO users (username,password,usertype,firstname,lastname) VALUES ({values})')
        mysql.connection.commit()
        cur.close()
        loggedin=True

    return render_template('register.html', loggedin=loggedin)

# Samples page
@app.route('/samples', methods=["GET","POST"])
def samples():
    if 'username' in session:
        # print('FORM AND ARGS:::::::')
        # print(request.form)
        # print(request.args)
        admin = True if session['usertype'] == 'ADMIN' else False
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        modID = []
        samplesData = []
        conditions = ''
        notfound = []
        fields = []
        userInput = {}
        msg=''
        sortstring = ''
        sorttype = 'Date_Taken_Out'
        if 'sortord' not in session:
            session['sortord'] = 'DESC'
        if 'fridge' not in session:
            session['fridge'] = ''
        if not request.args:
            if 'filemodID' in session:
                session.pop('filemodID')

        # column sorting
        if 'sorttype' in request.args:
            sortord = 'ASC' if session['sortord'] == 'DESC' else 'DESC'
            session['sortord'] = sortord
            sorttype = request.args.get('sorttype')
            sortstring = f"ORDER BY {sorttype} {sortord}"
        else:
            sortord = 'DESC'

        # Searching by file is post 
        if request.method == 'POST':
            # Search by File Upload
            if request.files:
                if 'filemodID' in session:
                    session.pop('filemodID')
                file = request.files['usersamples']
                filename = secure_filename(file.filename)
                filepath = os.path.join("application","input",filename)
                file.save(filepath)
                # SELECT SAMPLES BY FILE
                [samplesData,modID,fields,notfound] = selectByFile(filepath)
                session['notfound'] = notfound
                session['fields'] = fields
                session['filemodID'] = modID

        elif request.method == 'GET':
            # if a search is being made, no longer consider file search data
            if 'search' in request.args:
                if 'filemodID' in session:
                    session.pop('filemodID')
            # for continued sorting of file search data
            if 'filemodID' in session:
                modID = session['filemodID']
                idstring = ','.join(map("{0}".format,modID))
                cur.execute(f'SELECT * FROM samples WHERE id IN ({idstring}) ORDER BY {sorttype} {sortord}')
                samplesData = cur.fetchall()                    
            else:
                # Search functionality
                conditions = ''
                # Building conditions
                for item in request.args:
                # Building conditions from args
                    if request.args.get(item) and item!='search' and item!='tocsv' and item!='Collection_Int' and item!='sorttype' and item!='sortord' and item!='modID':
                        conditions = f"{conditions} {item} like \'%{request.args.get(item)}%\' AND"
                        userInput[item]=request.args.get(item)
                session['fridge'] = userInput["Fridge_Name"] if "Fridge_Name" in userInput else session['fridge'] # Jinja does not support userInput["Fridge_Name"] == {{ fridge }}, so this is work around
                # If conditions, do a query
                interval = request.args.get('Collection_Int') if request.args.get('Collection_Int') else None
                if conditions or interval:
                    colfilt = '' # filter string for less than n years since collection date
                    if interval:
                        userInput["Collection_Int"] = interval
                        colfilt = f" AND Collection_Date > now() - interval {interval} YEAR"
                    cur.execute(f'SELECT * FROM samples WHERE {conditions} NOT flag <=> \'MISSING\'{colfilt} {sortstring}')
                    samplesData = cur.fetchall()
                    modID = [ item['id'] for item in samplesData ]
                # If no conditions then just return samples that are currently out by default
                else:
                    cur.execute(f'SELECT * FROM samples LIMIT 25') #2021_12_01: added this display line for DB, commented out below line.
                    #cur.execute(f'SELECT * FROM samples WHERE Date_Taken_Out IS NOT NULL AND NOT flag <=> \'MISSING\' {sortstring}')
                    samplesData = cur.fetchall()
                    modID = [ item['id'] for item in samplesData ]
                    cur.close()
            # Otherwise (e.g. for empty inputs) samples that are currently out by default        
        else:
            cur.execute(f'SELECT * FROM samples LIMIT 25')  # 2021_12_01: added this display line for DB, commented out below line.
            #cur.execute(f'SELECT * FROM samples WHERE Date_Taken_Out IS NOT NULL AND NOT flag <=> \'MISSING\' {sortstring}')
            samplesData = cur.fetchall()
            modID = [ item['id'] for item in samplesData ]
            cur.close()
    else:
        return 'Unauthorized to access samples. Please log in.'
    
    msg=''
    for item in samplesData:
        if item['Low_DNA'] == "YES":
            msg = "Warning: at least one sample in this selection is flagged LOW DNA"
            break
    numsamp = len(samplesData)

    return render_template('samples.html', samples=True, modID=modID, msg=msg, fridgesData=fridgesData, conditions=conditions, numsamp=numsamp, sorttype=sorttype, sortord=sortord, fields=fields, notfound=notfound, samplesData = samplesData, session=session, admin=admin, userInput=userInput, loggedin=True, date=dt.date.today())

# Actions page
@app.route('/actions',  methods=["GET","POST"])
def actions():
    samplesData = []
    modID = []
    if 'username' in session:
#        if session['usertype'] == 'ADMIN':         ***2021_12_02: removing 'if admin' logic so that page works for non-admin users***
        msg = ''
        admin = True if session['usertype'] == 'ADMIN' else False
        if request.method == 'POST':
            #Using id column to individually identify samples
            if request.form.get('CHECK'):
                cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                for item in request.form.getlist('CHECK'):
                    cur.execute('SELECT * FROM samples WHERE id=\'' + item + '\'')
                    samp = cur.fetchone()
                    if samp['flag'] == 'LOW DNA':
                        msg = "Warning: At least one sample in your selection is flagged LOW DNA"
                    samplesData.append(samp)
                cur.close()
                modID = [ item['id'] for item in samplesData ]
            else:
                return samples()
    else:
        return 'Invalid access to actions page. Please log in.'
    return render_template('actions.html', samples=True, loggedin=True, msg=msg, admin=admin, samplesData = samplesData, fridgesData = fridgesData, shelfData=shelfData, rackData=rackData, modID = modID, date=dt.date.today())

@app.route('/savechanges', methods=["GET","POST"])
def savechanges():
    if 'username' in session:
        if 'filemodID' in session:
            session.pop('filemodID')
        admin = True if session['usertype'] == 'ADMIN' else False
        if request.method == 'POST':
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            # Returning samples (from mysamples page)
            if request.form.get('return'):
                if request.form.get('CHECK'):
                    for item in request.form.getlist('CHECK'):
                        query = 'UPDATE samples SET Shelf_No=NULL,Rack_Label=NULL,Project_Name=NULL,Researcher_Name=NULL,Date_Taken_Out=NULL,Fridge_Name=NULL,comments=NULL WHERE id=\'' + item + '\''
                        cur.execute(query)
                        mysql.connection.commit()
                else:
                    return mysamples()
            # Taking out samples (from actions page)
            elif request.form.get('savechanges'):
                modID = request.args.getlist('modID', None)
                commentscol = ''
                comments = ''
                if request.form.get('comchange'):
                    commentscol = ',comments='
                    comments = f"\'{request.form.get('comchange')}\'"
                for item in modID:
                    query = f"UPDATE samples SET Shelf_No=\'{request.form.get('shelfchange')}\',Rack_Label=\'{request.form.get('rackchange')}\',Project_Name=\'{request.form.get('projchange')}\',Researcher_Name=\'{session['firstname']} {session['lastname'][0]}\',Date_Taken_Out=\'{request.form.get('datechange')}\',Fridge_Name=\'{request.form.get('fridgechange')}\'{commentscol}{comments} WHERE id=\'{item}\'"
                    cur.execute(query)
                mysql.connection.commit()
            elif request.form.get('setmissing'):
                modID = request.args.getlist('modID', None)
                for item in modID:
                    idstring = ','.join(map("{0}".format,modID))
                    cur.execute(f'UPDATE samples SET flag=\'MISSING\' WHERE id IN ({idstring})')
                    mysql.connection.commit()
            elif request.form.get('setlowdna'):
                modID = request.args.getlist('modID', None)
                for item in modID:
                    cur.execute('UPDATE samples SET Low_DNA=\'YES\' WHERE id=\''+item+'\'')
                    mysql.connection.commit()
            elif request.form.get('setdepleteddna'):         #***2021_12_02: adding in logic for DEPLETED_DNA flag***
                modID = request.args.getlist('modID', None)
                for item in modID:
                    cur.execute('UPDATE samples SET Depleted_DNA=\'YES\' WHERE id=\'' + item + '\'')
                    mysql.connection.commit()
            elif request.form.get('setfound') and request.form.get('CHECK'):
                for item in request.form.getlist('CHECK'):
                    cur.execute('UPDATE samples SET flag=NULL WHERE id=\''+item+'\'')
                    mysql.connection.commit()
            else:
                return actions()
            cur.close()
            return render_template('savechanges.html', samples=True, loggedin=True, admin=admin)
    else:
        return 'Invalid access to this webpage'

@app.route('/downloadcsv', methods=["GET","POST"])
def downloadcsv():
    if 'username' in session:
        if request.args.get('modID'):
            samplesData = []
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            modID = request.args.getlist('modID')
            for item in modID:
                cur.execute("SELECT * FROM samples WHERE id=\'"+item+'\'')
                samplesData.append(cur.fetchone())
            return toCsv(samplesData, sample_labels, 'samples_report_')
        elif 'notfound' in session:
            notfound = session['notfound']
            session.pop('fields')
            session.pop('notfound')
            return toCsv(notfound,sample_labels,'samples_notfound_')
        else:
            return "Sample list empty. Table needs to be populated to download a csv."
    else:
        return 'Invalid access'

@app.route('/mysamples', methods=["GET","POST"])
def mysamples():
    if 'username' in session:
        admin = True if session['usertype'] == 'ADMIN' else False
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        modID = []
        samplesData = []
        conditions = ''
        notfound = []
        fields = []
        userInput = {}
        msg=''
        sortstring = ''
        sorttype = 'Date_Taken_Out'
        if 'sortord' not in session:
            session['sortord'] = 'DESC'

        # column sorting
        if 'sorttype' in request.args:
            sortord = 'ASC' if session['sortord'] == 'DESC' else 'DESC'
            session['sortord'] = sortord
            sorttype = request.args.get('sorttype')
            sortstring = f"ORDER BY {sorttype} {sortord}"
        else:
            sortord = 'DESC'

        # Searching by search inputs is get
        if request.method == 'GET':
            conditions = ''
            # Search functionality
            # Building conditions
            for item in request.args:
            # Building conditions from args
                if request.args.get(item) and item!='search' and item!='tocsv' and item!='Collection_Int' and item!='sorttype' and item!='sortord' and item!='modID':
                    conditions = f"{conditions} {item} like \'%{request.args.get(item)}%\' AND"
                    userInput[item]=request.args.get(item)
            # If conditions, do a query
            interval = request.args.get('Collection_Int') if request.args.get('Collection_Int') else None
            if conditions or interval:
                colfilt = '' # filter string for less than n years since collection date
                if interval:
                    userInput["Collection_Int"] = interval
                    colfilt = f" AND Collection_Date > now() - interval {interval} YEAR"
                cur.execute(f"SELECT * FROM samples WHERE {conditions} NOT flag <=> \'MISSING\' AND Researcher_Name=\'{session['firstname']} {session['lastname'][0]}\' {colfilt} {sortstring}")
                samplesData = cur.fetchall()
                modID = [ item['id'] for item in samplesData ]
            # If no conditions then just return samples that user has out
            else:
                cur.execute(f"SELECT * FROM samples WHERE NOT flag <=> \'MISSING\' AND Researcher_Name=\'{session['firstname']} {session['lastname'][0]}\' {sortstring}")
                samplesData = cur.fetchall()
                modID = [ item['id'] for item in samplesData ]
                cur.close()
        # Otherwise (e.g. for empty inputs) samples user has out      
        else:
            cur.execute(f"SELECT * FROM samples WHERE NOT flag <=> \'MISSING\' AND Researcher_Name=\'{session['firstname']} {session['lastname'][0]}\' {sortstring}")
            samplesData = cur.fetchall()
            modID = [ item['id'] for item in samplesData ]
            cur.close()
    else:
        return 'Unauthorized to access samples. Please log in.'
    
    msg=''
    for item in samplesData:
        if item['flag'] == "LOW DNA":
            msg = "Warning: at least one sample in this selection is flagged LOW DNA"
            break
    numsamp = len(samplesData)

    return render_template('mysamples.html', date=dt.date.today(),numsamp=numsamp, sorttype=sorttype, sortord=sortord, admin = admin, userInput=userInput, modID=modID, samplesData=samplesData, mysamples=True, loggedin=True)

@app.route('/missing', methods=["GET","POST"])
def missing():
    if 'username' in session:
        admin = True if session['usertype'] == 'ADMIN' else False
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        modID = []
        samplesData = []
        conditions = ''
        notfound = []
        fields = []
        userInput = {}
        msg=''
        sortstring = ''
        sorttype = 'Date_Taken_Out'
        if 'sortord' not in session:
            session['sortord'] = 'DESC'

        # column sorting
        if 'sorttype' in request.args:
            sortord = 'ASC' if session['sortord'] == 'DESC' else 'DESC'
            session['sortord'] = sortord
            sorttype = request.args.get('sorttype')
            sortstring = f"ORDER BY {sorttype} {sortord}"
        else:
            sortord = 'DESC'

        # Searching by file is post 
        if request.method == 'POST':
            # Search by File Upload
            if request.files:
                file = request.files['usersamples']
                filename = secure_filename(file.filename)
                filepath = os.path.join("application","input",filename)
                file.save(filepath)
                # SELECT SAMPLES BY FILE
                [samplesData,modID,fields,notfound] = selectByFile(filepath)
                session['notfound'] = notfound
                session['fields'] = fields

        # Searching by search inputs is get
        elif request.method == 'GET':
            conditions = ''
            # Search functionality
            # Building conditions
            for item in request.args:
            # Building conditions from args
                if request.args.get(item) and item!='search' and item!='tocsv' and item!='Collection_Int' and item!='sorttype' and item!='sortord' and item!='modID':
                    conditions = f"{conditions} {item} like \'%{request.args.get(item)}%\' AND"
                    userInput[item]=request.args.get(item)
            # If conditions, do a query
            interval = request.args.get('Collection_Int') if request.args.get('Collection_Int') else None
            if conditions or interval:
                colfilt = '' # filter string for less than n years since collection date
                if interval:
                    userInput["Collection_Int"] = interval
                    colfilt = f" AND Collection_Date > now() - interval {interval} YEAR"
                cur.execute(f'SELECT * FROM samples WHERE {conditions} flag = \'MISSING\'{colfilt} {sortstring}')
                samplesData = cur.fetchall()
                modID = [ item['id'] for item in samplesData ]
            # If no conditions then just return samples that are currently out by default
            else:
                cur.execute(f'SELECT * FROM samples WHERE flag = \'MISSING\' {sortstring}')
                samplesData = cur.fetchall()
                modID = [ item['id'] for item in samplesData ]
                cur.close()
        # Otherwise (e.g. for empty inputs) samples that are currently out by default        
        else:
            cur.execute(f'SELECT * FROM samples WHERE flag = \'MISSING\' {sortstring}')
            samplesData = cur.fetchall()
            modID = [ item['id'] for item in samplesData ]
            cur.close()
    else:
        return 'Unauthorized to access samples. Please log in.'
    
    msg=''
    for item in samplesData:
        if item['flag'] == "LOW DNA":
            msg = "Warning: at least one sample in this selection is flagged LOW DNA"
            break
    numsamp = len(samplesData)

    return render_template('missing.html', admin = admin, missing=True, sortord=sortord, sorttype=sorttype, numsamp=numsamp, date=dt.date.today(), userInput=userInput, modID=modID, samplesData=samplesData, loggedin=True)

@app.route('/updatelims',methods=["GET","POST"])
def updatelims():
    if 'username' in session:
        if session['usertype'] == 'ADMIN':
            if request.files and request.form.get('updatelims'):
                file = request.files['progenyfile']
                filename = secure_filename(file.filename)
                filepath = os.path.join("application","input",filename)
                file.save(filepath)
                updateSamples(filepath)
        else:
            return 'Invalid access'
    else:
        return 'Invalid access'
    return render_template('updatelims.html', admin=True, loggedin=True, updatelims=True)

#basic api
@app.route("/api")
@app.route("/api/<idx>")
def api(idx=None):
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute('SELECT * FROM samples')
    jdata = apicall(idx)
    cur.close()

    return Response(json.dumps(jdata), mimetype="application/json")
#
#
#
####################NON-VIEW FUNCTIONS
# Need to update this apicall function, currently pretty useless
def apicall(idx): 
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute('SELECT * FROM samples ORDER BY Date_Taken_Out DESC')
    samplesData = cur.fetchall()
    if(idx == None): #no index given -> send all sample data
        return samplesData
    else:
        try: #get by id
            cur.execute('SELECT * FROM samples WHERE id='+str(idx))
            return cur.fetchone()
        except: #if it fails, maybe a range is given
            try: #try to parse the range (to provide a range, give two integers delimited by '-' eg 1-2)
                jdata = []
                j_range = idx.split('-')
                for i in range(int(j_range[0]),int(j_range[1])+1):
                    cur.execute('SELECT * FROM samples WHERE id='+i)
                    jdata.append(cur.fetchone)
                return jdata
            except:
                try:
                    j_sample = idx.split('_')
                    cur.execute('SELECT * FROM samples WHERE Progeny_ID = \'' + j_sample[0] + '\' AND Aliquot_Label = \'' + j_sample[1] + '\' ORDER BY Date_Taken_Out DESC')
                    jdata = cur.fetchone()
                    cur.close()
                    return jdata
                except:
                    try:
                        j_name = str(idx)
                        cur.execute('SELECT * FROM samples WHERE Researcher_Name = \'' + j_name + '\' ORDER BY Date_Taken_Out DESC')
                        jdata = cur.fetchall()
                        return jdata
                    except:    
                        print("Invalid idx, dumping all samples")
                        return "Invalid range or no sample with given ID found"

def selectByFile(filepath):
    samplesData = []
    modID = []
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    df = pd.read_csv(filepath, dtype=np.string_)
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')] # get rid of empty columns
    df.replace('\'','\'\'', regex=True, inplace=True) # replace apostrophe's with readable ones (may be unnecessary in actual use cases but prevents parsing errors)
    df.fillna('EXCLUDE', inplace=True) # identify data to not use for querying
    cols = df.columns.values.tolist()
    rows = df.values.tolist()
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    missing = []
    notfound = []
    for item in rows:
        indices = [i for i in range(len(item)) if item[i]!='EXCLUDE']
        item = list((item[i] for i in indices))
        tempcol = list((cols[i] for i in indices))
        values = ','.join(map("'{0}'".format,item))
        tempfields = ','.join(map("{0}".format,tempcol))
        if tempfields and values:
            cur.execute('SELECT * FROM samples WHERE (' + tempfields + ') = (' + values + ')')
            res = cur.fetchall()              
            if res:
                for samp in res:
                    if samp['flag'] == 'MISSING':
                        missing.append(samp)
                    else:
                        samplesData.append(samp)
                        modID.append(samp["id"])
            else:
                notfound.append(dict(zip(tempcol,item)))
    cur.close()
    # here down is to deal with duplicates
    samplesDF = pd.DataFrame(samplesData, dtype=str)
    missingDF = pd.DataFrame(missing, dtype=str)
    modIDDF = pd.DataFrame(modID, dtype=str)
    notfoundDF = pd.DataFrame(notfound, dtype=str)
    samplesDF.drop_duplicates(inplace=True)
    missingDF.drop_duplicates(inplace=True)
    modIDDF.drop_duplicates(inplace=True)
    notfoundDF.drop_duplicates(inplace=True)
    notfoundDF = pd.concat([missingDF,notfoundDF])
    notfoundDF.index.rename('id',inplace=True)
    samplesData = samplesDF.to_dict('records')
    notfound = notfoundDF.to_dict('records') if not notfoundDF.empty else []
    
    modIDdict = modIDDF.to_dict('records')
    modID = []

    for item in modIDdict:
        modID.append(item[0])
    return samplesData,modID,cols,notfound

def toCsv(samplesData, columns, filename):
    if len(samplesData)<1:
        return 'No samples in query.'
    file_string = filename + str(dt.date.today()) + '.csv'
    filepath = os.path.join("output",file_string)
    df = pd.DataFrame(samplesData, columns=columns)
    index = False
    if 'id' in df.columns.values.tolist():
        df = df.set_index('id')
        index=True
    df.to_csv(os.path.join("application","output",file_string), index=index)
    return send_file(filepath,mimetype='text/csv', as_attachment=True)
