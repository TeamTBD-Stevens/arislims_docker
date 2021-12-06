CREATE DATABASE IF NOT EXISTS arisDB;

USE arisDB;

CREATE TABLE IF NOT EXISTS messages(author VARCHAR(20), subject VARCHAR(100), message text, flag VARCHAR(20), date DATETIME, id INT AUTO_INCREMENT PRIMARY KEY) ENGINE=INNODB;

CREATE TABLE IF NOT EXISTS users(username VARCHAR(20), password VARCHAR(20), usertype VARCHAR(10), firstname VARCHAR(30), lastname VARCHAR(30), samplesout INT, historic_samplesout INT, historic_samplesret INT, id INT AUTO_INCREMENT PRIMARY KEY) ENGINE=INNODB;

CREATE TABLE IF NOT EXISTS samples(Progeny_ID VARCHAR(30), Family_ID VARCHAR(30), Sample_Type VARCHAR(50), Aliquot_Label VARCHAR(30), Fridge_Name VARCHAR(30), Shelf_No VARCHAR(3), Rack_Label VARCHAR(4), Researcher_Name VARCHAR(30), Project_Name VARCHAR(50), Date_Taken_Out VARCHAR(10), Original_Fridge VARCHAR(30), Original_Rack VARCHAR(4), Original_Drawer VARCHAR(20), Original_Box VARCHAR(100), Original_Well VARCHAR(20), Original_Shelf VARCHAR(20), Collection_Date VARCHAR(10), comments VARCHAR(100), Low_DNA VARCHAR(4),  Depleted_DNA VARCHAR(4), flag VARCHAR(20), id INT AUTO_INCREMENT PRIMARY KEY) ENGINE=INNODB;

INSERT INTO users (username,password,usertype,firstname,lastname) VALUES ('admin','admin','ADMIN','LIMS','DEVELOPER');

LOAD DATA LOCAL INFILE '/docker-entrypoint-initdb.d/samples_report_2021-12-02_allsamples_n48092.csv' INTO TABLE arisDB.samples FIELDS TERMINATED BY ',' LINES TERMINATED BY '\n' IGNORE 1 ROWS (@dummy, `Progeny_ID`,`Family_ID`,`Aliquot_Label`,`Sample_Type`,`Fridge_Name`,`Shelf_No`,`Rack_Label`,`Project_Name`,`Researcher_Name`,`Date_Taken_Out`,`Collection_Date`,`Original_Fridge`,`Original_Shelf`,`Original_Rack`,`Original_Drawer`,`Original_Box`,`Original_Well`,@dummy,`Low_DNA`, `Depleted_DNA`,`comments`);

UPDATE arisDB.samples SET Collection_Date = CASE WHEN Collection_Date = '' THEN '' ELSE STR_TO_DATE(Collection_Date, '%m/%d/%Y') END;

#ALTER TABLE arisDB.samples CHANGE COLUMN Collection_Date Collection_Date DATE;

UPDATE arisDB.samples SET Date_Taken_Out = CASE WHEN Date_Taken_Out = '' THEN '' ELSE STR_TO_DATE(Date_Taken_Out, '%m/%d/%Y') END;

#ALTER TABLE arisDB.samples CHANGE COLUMN Date_Taken_Out Date_Taken_Out DATE;



#UPDATE samples
#SET Aliquot_Label = REPLACE(Aliquot_Label, '1', 'YES')
#where id = 1