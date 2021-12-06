# Use this code to update the database from Progeny
import mysql.connector
from flask_mysqldb import MySQLdb
from mysql.connector import Error
from mysql.connector import connection
import pandas as pd
from sqlalchemy import create_engine
from config import devConfig, deployConfig, godzillaConfig

header_dict = {
    "IndID":"Progeny_ID",
    "family_ID":"Family_ID",
    "Sample_Info.LIMS_ID":"id",
    "Sample_Info.SInf_SampleType":"Sample_Type",
    "Sample_Info.SInf_SampleLabel":"Aliquot_Label",
    "Sample_Info.SInf_Freezer/Refrigerator":"Original_Fridge",
    "Sample_Info.SInf_Shelf":"Original_Shelf",
    "Sample_Info.Sinf_Rack":"Original_Rack",
    "Sample_Info.SInf_Drawer":"Original_Drawer",
    "Sample_Info.SInf_Box":"Original_Box",
    "Sample_Info.SInf_Well":"Original_Well",
    "Sample_Info.SInf_CollectionDate":"Collection_Date",
    "Sample_lowDNA":"Low_DNA"
}

sample_labels = ["Progeny_ID","Family_ID","Aliquot_Label","Sample_Type","Fridge_Name","Shelf_No","Rack_Label","Project_Name","Researcher_Name","Date_Taken_Out","Original_Fridge","Original_Shelf","Original_Rack","Original_Drawer","Original_Box","Original_Well","Collection_Date","flag","comments","id"]


curConfig = godzillaConfig
HOST = curConfig.MYSQL_HOST
DB = curConfig.MYSQL_DB
USER = curConfig.MYSQL_USER
PASS = curConfig.MYSQL_PASSWORD

def updateSamples(file):
    try:
        db = mysql.connector.connect(host=HOST,
                                        database=DB,
                                        user=USER,
                                        password=PASS)
        if db.is_connected():
            print('Connected to '+DB)

            cur = db.cursor(MySQLdb.cursors.DictCursor)
            print('TABLE CHECK ALGO')
            cur.execute('CREATE TABLE IF NOT EXISTS messages(author VARCHAR(20), subject VARCHAR(100), message text, flag VARCHAR(20), date DATETIME, id INT AUTO_INCREMENT PRIMARY KEY) ENGINE=INNODB;')
            cur.execute('CREATE TABLE IF NOT EXISTS users(username VARCHAR(20), password VARCHAR(20), usertype VARCHAR(10), firstname VARCHAR(30), lastname VARCHAR(30), samplesout INT, historic_samplesout INT, historic_samplesret INT, id INT AUTO_INCREMENT PRIMARY KEY) ENGINE=INNODB;')
            cur.execute('CREATE TABLE IF NOT EXISTS samples(Progeny_ID VARCHAR(30), Family_ID VARCHAR(30), Sample_Type VARCHAR(50), Aliquot_Label VARCHAR(30), Fridge_Name VARCHAR(30), Shelf_No VARCHAR(3), Rack_Label VARCHAR(4), Researcher_Name VARCHAR(30), Project_Name VARCHAR(50), Date_Taken_Out DATE, Original_Fridge VARCHAR(30), Original_Rack VARCHAR(4), Original_Drawer VARCHAR(20), Original_Box VARCHAR(100), Original_Well VARCHAR(20), Collection_Date DATE, flag VARCHAR(20), comments VARCHAR(100), Low_DNA VARCHAR(4), id INT AUTO_INCREMENT PRIMARY KEY) ENGINE=INNODB;')

            # Create an developer acc automatically
            cur.execute('SELECT * FROM users WHERE username=\'admin\'')
            if not cur.fetchone():
                cur.execute('INSERT INTO users (username,password,usertype,firstname,lastname) VALUES (\'admin\',\'admin\',\'ADMIN\',\'LIMS\',\'DEVELOPER\')')
                db.commit()

            # save taken out data, and flags/comments
            cols = 'id,' + ','.join(map("{0}".format,sample_labels[4:10])) + ',flag,comments'
            cur.execute('SELECT '+cols+' FROM samples WHERE Researcher_Name IS NOT NULL OR flag IS NOT NULL OR comments IS NOT NULL')
            samples_out = cur.fetchall()
            df2 = pd.DataFrame(data = samples_out, columns=['id'] + sample_labels[4:10] + ['flag','comments'])
            df2.set_index('id', inplace=True)
            cur.close()
            db.close()


            url = 'mysql://'+USER+':'+PASS+'@'+HOST+'/'+DB
            engine = create_engine(url, echo = True)
            df = pd.read_csv(file, index_col='Sample_Info.LIMS_ID', usecols=header_dict.keys())
            df.rename(columns = header_dict, inplace = "True")
            df = df[df.columns.intersection(header_dict.values())]

            df.insert(5,"Date_Taken_Out",'')
            df.insert(5,"Project_Name",'')
            df.insert(5,"Researcher_Name",'')
            df.insert(5,"Rack_Label",'')
            df.insert(5, "Shelf_No", '')
            df.insert(5, "Fridge_Name", '')
            df.insert(16, "flag", '')
            df["Date_Taken_Out"] = None
            df["Project_Name"] = None
            df["Researcher_Name"] = None
            df["Rack_Label"] = None
            df["Shelf_No"] = None
            df["Fridge_Name"] = None
            df["flag"] = None
            df["comments"] = None

            # convert 1s from Progeny to YES, and empty to NO
            df['Low_DNA'].where(~(df.Low_DNA==1),other="YES", inplace=True)
            df['Low_DNA'].fillna(value="NO",inplace=True)

            # merge LIMS data with Progeny data
            df.update(df2, overwrite=False)

            df = df.where(pd.notnull(df),None)
            
            df['Collection_Date'] = pd.to_datetime(df.Collection_Date).dt.strftime('%Y-%m-%d')

            # Update all samples
            with engine.connect() as conn, conn.begin():
                print('SQLAlchemy connection made to db')
                df.to_sql(name='samples', con=conn, if_exists = 'replace', index=True, index_label="id")
                conn.execute('ALTER TABLE samples ADD PRIMARY KEY(id)')

    except Error as e:
        print(e)