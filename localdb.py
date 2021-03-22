import sqlite3

# Pandas for dataframe processing
import pandas as pd
import time
import datetime
import threading

# External modules for fetching data

class DB(object):    
    """DB initializes and manipulates SQLite3 cache with Coverity data"""

    def __init__(self, database='dashtables.db'):
        """Initialize a new or connect to an existing database.

        Accept setup statements to be executed.
        """
        self.connectedwrite = False
        self.connected = False
        self.readmutex = threading.Lock()
        #the database filename
        self.database = database
        #holds incomplete statements
#        self.statement = ''
        #indicates if selected data is to be returned or printed
        self.display = False

        self.connect()

        #execute setup satements (removed as 3rd parameter)
#        self.execute(statements)
        # Get the initial Coverity data tables depending on how much is already there.
        #self.getCoverityData()

        self.close()            

    def connect(self):
        """Connect to the SQLite3 database."""
        print ("opening:" + self.database)
        self.connection = sqlite3.connect(self.database)
        #this cursor will be used for DB reads
        self.cursor = self.connection.cursor()
        self.connected = True
        self.statement = ''

    def connectwrite(self):
        """Connect to the SQLite3 database."""
        print ("opening for write:" + self.database)
        self.connectionwrite = sqlite3.connect(self.database)
        #this cursor will be used for DB writes
        self.cursorwrite = self.connectionwrite.cursor()
        self.connectedwrite = True
        self.statement = ''

    def getCoverityData(self):
        return None

    def close(self):
        """Close the SQLite3 database."""
        self.connection.commit()
        self.connection.close()
        self.connected = False

    def closewrite(self):
        """Close the SQLite3 database."""
        self.connectionwrite.commit()
        self.connectionwrite.close()
        self.connectedwrite = False        

    def incomplete(self, statement):
        """Concatenate clauses until a complete statement is made."""

        self.statement += statement
        if self.statement.count(';') > 1:
            print ('An error has occurerd: ' +
                'You may only execute one statement at a time.')
            print ('For the statement: %s' % self.statement)
            self.statement = ''
        if sqlite3.complete_statement(self.statement):
            #the statement is not incomplete, it's complete
            return False
        else:
            #the statement is incomplete
            return True

    def dftotable(self, df, tablename):
        
        close = False    
        if not self.connectedwrite:
            #open a previously closed connection
            self.connectwrite()
            #mark the connection to be closed once complete
            close = True    

        df.to_sql(tablename, self.connectionwrite, index=False, if_exists="append")

        if close:
            self.closewrite()  

    def tabletodf(self, query):
        
        close = False  
        self.readmutex.acquire()  
        if not self.connected:
            #open a previously closed connection
            print("Connecting for Read")
            self.connect()
            #mark the connection to be closed once complete
            close = True    

        df = pd.read_sql_query(query, self.connection)

        if close:
            self.close()      
            print("Closing from Read")    
        self.readmutex.release()      
        return df
        #df.to_sql(tablename, self.connection, index=False, if_exists="append")

           

    def execute(self, statements):
        """Execute complete SQL statements.

        Incomplete statements are concatenated to self.statement until they 
        are complete.

        Selected data is returned as a list of query results. Example: 

        for result in db.execute(queries):
            for row in result:
                print row
        """

        queries = []
        close = False
        if not self.connected:
            #open a previously closed connection
            self.connect()
            #mark the connection to be closed once complete
            close = True
        if type(statements) == str:
            #all statements must be in a list
            statements = [statements]
        for statement in statements:
            if self.incomplete(statement):
                #the statement is incomplete
                continue
            #the statement is complete
            try:
                statement = self.statement.strip()
                #reset the test statement
                self.statement = ''
                self.cursor.execute(statement)
                #retrieve selected data
                data = self.cursor.fetchall()
                if statement.upper().startswith('SELECT'):
                    #append query results
                    queries.append(data)

            except sqlite3.Error as error:
                print ('An error occurred:', error.args[0])
                print ('For the statement:', statement)

        #only close the connection if opened in this function
        if close:
            self.close()   
        #print results for all queries
        if self.display:      
            for result in queries:
                if result:
                    for row in result:
                        print (row)
                else:
                    print (result)
        #return results for all queries
        else:
            return queries

"""
# if __name__ == '__main__':     
#    statement = ('CREATE TABLE %s (id INTEGER, filename TEXT);')                    
    tables = ['source', 'query']

    database = 'io.db'
    statements = [statement % table for table in tables]

    #setup
    db = DB(database, statements)

    #a single statement
    db.execute(
        ["INSERT INTO source (id, filename) values (8, 'reference.txt');"])

    #a list of complete statements
    db.execute(["INSERT INTO query (id, filename) values (8, 'one.txt');",
                "INSERT INTO query (id, filename) values (9, 'two.txt');"])

    #a list of incomplete statements
    db.execute(["INSERT INTO query (id, filename) ", 
                "values (10, 'three.txt');"])

    #retrieving multiple query results
    queries = ['SELECT * FROM source;', 'SELECT * FROM query;']
    for result in db.execute(queries):
        print (result)

[(8, u'reference.txt')]
[(8, u'one.txt'), (9, u'two.txt'), (10, u'three.txt')]
"""
