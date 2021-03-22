# Get zeep for communicating to Coverity
from zeep import Client, Settings
from zeep.wsse.username import UsernameToken
from localdb import DB as ConnectDB

from json import dumps

import pandas as pd

import time
import datetime
import threading

# for creating the hash DB name
import hashlib

a1 = [77,78,88,89,90,91,943,917]
a2 = [287,384,613]
a3 = [311,312,319,320,326,327,328,359,295]
a4 = [611,776]
a5 = [22,284,285,639,425]
a6 = [209,16]
a7 = [79]
a8 = [502]
a9 = []
a10 = [223,778]
Top10Owasp = [a1, a2, a3, a4, a5, a6, a7, a8, a9, a10]

class Coverity(object):    
    """ initializes and manipulates Coverity ."""

    def __init__(self, user, passkey, url='http://localhost:8080'):
    
        #the database filename
        self.coverityurl = url
        self.username = user
        self.passkey = passkey
        self.configurl = self.coverityurl + '/ws/v9/configurationservice?wsdl'         
        self.defecturl = self.coverityurl + '/ws/v9/defectservice?wsdl' 

        self.connect()
        self.connectDBCache()


    def connect(self):
        """Connect to the Coverity database."""

        self.connectionConfig =  Client(self.configurl, wsse=UsernameToken(self.username, self.passkey))
        self.connectionDefect =  Client(self.defecturl, wsse=UsernameToken(self.username, self.passkey))
        self.connected = True

    def connectDBCache(self):

        # So we don't create a file with the passkey of the user blatantly displayed
        # MD5 is weak but we aren't claiming to be super secure here and it's unlikely that
        # the md5ed combination of user and passkey are going to be anywhere near a lookup database.
        self.dbname = "Coverity" + self.username + self.coverityurl
        salt = "Coverity"
        self.dbhash = hashlib.md5(self.dbname.encode('utf-8')).hexdigest()
        self.dbfile = self.dbhash + '.db'
        print ("Creating database " + self.dbfile + " if it doesn't exist")
        self.db = ConnectDB(self.dbfile)

        # Setup the Project Snapshot Data Table
        # ('Project', 'Stream','SnapshotIds',"Date","Analysis Host","Analysis Version","Build Command","Analysis Command","Commit User")
        #snapshotQuery = 'CREATE TABLE IF NOT EXISTS snapShots (Project TEXT NOT NULL, Stream TEXT NOT NULL, SnapshotIds TEXT PRIMARY KEY, Date DATETIME NOT NULL, #Analysis Host TEXT NOT NULL, Analysis Version TEXT NOT NULL, Build Command TEXT NOT NULL, Analysis Command TEXT NOT NULL, Commit User TEXT NOT NULL);'
        #self.db.execute(snapshotQuery)

        # ('Project', 'Stream','SnapshotId',"Checker","CID","CWE","Status","Impact","Type","FirstDetected","LastDetected")
        # Setup the Project Defects Table
        #defectsQuery = 'CREATE TABLE IF NOT EXISTS defects (Project TEXT NOT NULL, Stream TEXT NOT NULL, SnapshotIds TEXT PRIMARY KEY, Checker TEXT NOT NULL, CID TEXT NOT NULL, CWE TEXT NOT NULL, Status TEXT NOT NULL, Impact TEXT NOT NULL, Type TEXT NOT NULL, FirstDetected DATETIME NOT NULL,LastDetected DATETIME NOT NULL);'
        #self.db.execute(defectsQuery)

        mytemptable = pd.DataFrame(columns=('Project', 'Stream','SnapshotId',"Total","High","Medium","Low","Quality","Security","OWASP","A1","A2","A3","A4","A5","A6","A7","A8","A9","A10","High Security","Medium Security","Low Security","Date"))
        self.db.dftotable(mytemptable, 'defectStats')

        mytemptable2 = pd.DataFrame(columns=('Project', 'Stream','SnapshotId',"Checker","CID","CWE","Status","Impact","Type","FirstDetected","LastDetected",))
        self.db.dftotable(mytemptable2, 'defects')

        #Project', 'LOC','Outstanding',"Fixed","Dismissed","Date
        # Setup the ETL Data Table
        #etlQuery = 'CREATE TABLE IF NOT EXISTS trendData (Project TEXT PRIMARY KEY, LOC TEXT NOT NULL, Outstanding TEXT NOT NULL, Fixed TEXT NOT NULL, Dismissed TEXT NOT NULL, Date TEXT NOT NULL );'
        #self.db.execute(etlQuery)

        # Do this first as it's the easiest way to set the date of the latest snapshots and defects in the database to self.latestDate
        self.getProjectsandSnapshots()

        self.dbconnected = True

    def closeDBcache(self): 
        """Close the Coverity database."""
        #self.db.commit()
        self.db.close()
        self.dbconnected = False


    def getProjectsandSnapshots(self):

        row = 0;
        snapshotrow = 0;

        # ADD CODE TO FETCH THE LATEST DATE FROM THE TABLE AND THEN ONLY GO GET THOSE SNAPSHOTS FROM COVERITY

        if (self.connected == False):
            print ("Not Connected to Coverity") 
            return None
       
       # Get the latest snapshot date to append new data rather that refetch old
        getLatestSnapshotQuery = 'SELECT max(Date) FROM snapShotsLatest;'
        replyList = self.db.execute(getLatestSnapshotQuery)

        try:
            latestDateString = str(replyList[0])[3:-4]
        except:
            latestDateString = '1970-01-01 00:00:00'
        self.latestDate = (datetime.datetime.strptime(latestDateString,"%Y-%m-%d %H:%M:%S") + datetime.timedelta(seconds=1))

        print("latest date is :" + str(self.latestDate))

        # Build the getProjects JSON request to get all Projects and Streams
        proj_request_data = {
            'filterSpec': {
        #        'descriptionPattern': '',
        #        'includeChildren': 'false',
            'includeStreams': 'true',
        #        'namePattern': '',
            },
        }

        # Setup the dataframe for the latest Snapshots and another for allsnapshots.  Might not use the latest one and just make an sqlquery for it.
        mytable = pd.DataFrame(columns=('Project', 'Stream','SnapshotIds',"Date","Analysis Host","Analysis Version","Build Command","Analysis Command","Commit User","Build Time","Analysis Time"))
        allsnapshots = pd.DataFrame(columns=('Project', 'Stream','SnapshotIds',"Date","Analysis Host","Analysis Version","Build Command","Analysis Command","Commit User","Build Time","Analysis Time"))

        projectdata = self.connectionConfig.service.getProjects(**proj_request_data)


        for project in projectdata:
            #log_to_screen ("Project:" + project.id.name + " (id:" + str(project.projectKey) + ")" )
            for streams in project.streams:
                #log_to_screen ("Streams:\n\t" + streams.id.name + "(" + streams.componentMapId.name + "," + streams.language + ")")

                # Build the data request for the getSnapshotsForStream request 
                # <startDate>2018-11-02T08:04:37</startDate>  !! Note the T in the time string where the space would be
                streams_request_data = {
                    'streamId': {
                    'name': streams.id.name
                    },
                    'filterSpec': {
                        # Adding one second to the latest time because if we don't it'll retrieve the last item again as a duplicate
                        'startDate':self.latestDate,
                    }
                }

                #log_to_screen ("getting stream details for:" + streams.id.name)

                snapshotsdata = self.connectionConfig.service.getSnapshotsForStream(**streams_request_data) 
                
                if (len(snapshotsdata)):
                    lastSnapshot = len(snapshotsdata) - 1
                    snapshot = snapshotsdata[lastSnapshot]


                    for snapshot in snapshotsdata:
                        snapshot_request_data = {
                            'snapshotIds': {
                            'id': snapshot.id
                            },
                        }
                        # 2018-11-02 08:04:37.366000
                        snapshotinformation = self.connectionConfig.service.getSnapshotInformation(**snapshot_request_data)
                        print (str(snapshotinformation[0].dateCreated)[:-6])

                        #This converts the date to an sqlite happy format!
                        #The try except is here because sometimes Coverity doesnt have the .023423 microsecond on the commit time. Probably a back compatibility thing
                        #try:
                        #    happydate = datetime.datetime.fromtimestamp(time.mktime(time.strptime(str(snapshotinformation[0].dateCreated)[:-6],"%Y-%m-%d %H:%M:%S.%f")))
                        #except:
                        #    happydate = datetime.datetime.fromtimestamp(time.mktime(time.strptime(str(snapshotinformation[0].dateCreated)[:-6],"%Y-%m-%d %H:%M:%S")))

                        allsnapshots.loc[snapshotrow]=[project.id.name,streams.id.name,snapshot.id,self.convertDate(snapshotinformation[0].dateCreated),snapshotinformation[0].analysisHost,snapshotinformation[0].analysisVersion,snapshotinformation[0].buildCommandLine,snapshotinformation[0].analysisCommandLine,snapshotinformation[0].commitUser,snapshotinformation[0].buildTime,snapshotinformation[0].analysisTime]
                        snapshotrow=snapshotrow+1

                    #print("The snapshot range is {0:d} - {1:d} ".format(snapshotrow-len(snapshotsdata),snapshotrow-1))
                    #self.getAllDefects(allsnapshots.loc[snapshotrow-len(snapshotsdata):snapshotrow-1])

                    mytable.loc[row]=[project.id.name,streams.id.name,snapshot.id,self.convertDate(snapshotinformation[0].dateCreated),snapshotinformation[0].analysisHost,snapshotinformation[0].analysisVersion,snapshotinformation[0].buildCommandLine,snapshotinformation[0].analysisCommandLine,snapshotinformation[0].commitUser,snapshotinformation[0].buildTime,snapshotinformation[0].analysisTime]    
                    row=row+1


        self.db.dftotable(allsnapshots, 'snapShots')
        self.db.dftotable(mytable, 'snapShotsLatest')
        allsnapshots.sort_values(['Date'], ascending=False, inplace=True)

        self.getETLData()

        print ("Getting defects in new thread")
        # getAllDefects Should go in order of latest to oldest and populate in the background to keep the interface lively
        thread = threading.Thread(target=self.getAllDefects, args=())
        thread.daemon = True                            # Daemonize thread
        thread.start()                                  # Start the execution
        print ("Returning while etting defects in new thread")
        #self.getAllDefects()

        return allsnapshots

    def getAllDefects(self):

        row = 0
        sdf = self.getNewSnapshots()
        mytable = pd.DataFrame(columns=('Project', 'Stream','SnapshotId',"Total","High","Medium","Low","Quality","Security","OWASP","A1","A2","A3","A4","A5","A6","A7","A8","A9","A10","High Security","Medium Security","Low Security","Date"))

        for index, snapshot in sdf.iterrows():
            #for snapshot in sdf:
            ddf = self.get_defects(snapshot['Project'],snapshot['Stream'],snapshot['SnapshotIds'])
            typelist = ddf['Type'].value_counts()
            if  'Quality' not in typelist:
                typelist['Quality'] = 0
            if 'Security' not in typelist:
                typelist['Security'] = 0
            impactlist = ddf['Impact'].value_counts()
            if 'Low' not in impactlist:
                impactlist['Low'] = 0
            if 'Medium' not in impactlist:
                impactlist['Medium'] = 0
            if 'High' not in impactlist:
                impactlist['High'] = 0
    #		tmp= df.loc[(df['Impact'] == 'High') & df['Type'] == 'Security']
            highsecurity = len(ddf.query('Impact == "High" & Type == "Security"').index) 
            mediumsecurity = len(ddf.query('Impact == "Medium" & Type == "Security"').index) 
            lowsecurity = len(ddf.query('Impact == "Low" & Type == "Security"').index) 
            highsecurity = len(ddf.query('Impact == "High" & Type == "Security"').index) 

            sa1 = len((ddf.loc[(ddf['CWE'].isin(a1))]))
            sa2 = len((ddf.loc[(ddf['CWE'].isin(a2))]))
            sa3 = len((ddf.loc[(ddf['CWE'].isin(a3))]))
            sa4 = len((ddf.loc[(ddf['CWE'].isin(a4))]))
            sa5 = len((ddf.loc[(ddf['CWE'].isin(a5))]))
            sa6 = len((ddf.loc[(ddf['CWE'].isin(a6))]))
            sa7 = len((ddf.loc[(ddf['CWE'].isin(a7))]))
            sa8 = len((ddf.loc[(ddf['CWE'].isin(a8))]))
            sa9 = len((ddf.loc[(ddf['CWE'].isin(a9))]))
            sa10 = len((ddf.loc[(ddf['CWE'].isin(a10))]))
            owasp = sa1 + sa2 + sa3 + sa4 + sa5 + sa6 + sa7 + sa8 + sa9 + sa10
            mytable.loc[row]=[
                snapshot['Project'],
                snapshot['Stream'],
                snapshot['SnapshotIds'],
                len(ddf.index),
                impactlist['High'],
                impactlist['Medium'],
                impactlist['Low'],
                typelist['Quality'],
                typelist['Security'],
                owasp,
                sa1,
                sa2,
                sa3,
                sa4,
                sa5,
                sa6,
                sa7,
                sa8,
                sa9,
                sa10,
                highsecurity,
                mediumsecurity,
                lowsecurity,
                sdf.Date[index]
            ]
            row=row+1

        self.db.dftotable(mytable, 'defectStats')
        return mytable


    def get_defects(self,project,stream,snapshot):

        # Initialize our api, app and connection to Coverity

        row = 0
        mytable = pd.DataFrame(columns=('Project', 'Stream','SnapshotId',"Checker","CID","CWE","Status","Impact","Type","FirstDetected","LastDetected",))

        # NOTICE only getting the last 999 max defects for each snapshot
        defect_request_data = {
            'projectId': {
                    'name': project
            },
            'filterSpec': {
    #			'cweList':[99,94],
                'streamIncludeNameList': {
                    'name': stream
                },
                'streamIncludeQualifier': 'ANY',
            },
            'pageSpec': {
                    'pageSize': 999,
                'sortAscending':True,
                    'startIndex':0
            },
            'snapshotScope': { 
                'showSelector': snapshot
            },
        }

        defectlist = self.connectionDefect.service.getMergedDefectsForSnapshotScope(**defect_request_data)


        for defect in defectlist.mergedDefects:
    #		log_to_screen ("Defect:" + defect.checkerName + " (id:" + str(defect.cid) + ")" )
            #print (self.getNestedAttributeTuple(defect.defectStateAttributeValues, 'DefectStatus'))
            mytable.loc[row]=[project,stream,snapshot,defect.checkerName,defect.cid,defect.cwe,self.getNestedAttributeTuple(defect.defectStateAttributeValues, 'DefectStatus'), defect.displayImpact, defect.displayIssueKind, self.convertDate(defect.firstDetected), self.convertDate(defect.lastDetected)]
            row=row+1

        self.db.dftotable(mytable, 'defects')
        return mytable


    def getETLData(self):


        row = 0
        mytable = pd.DataFrame(columns=('Project', '1000LOC','Outstanding',"Fixed","Dismissed","Date"))

        allProjectsList = self.getProjectList()

        getLatestSnapshotQuery = 'SELECT max(Date) FROM projectTrends;'
        replyList = self.db.execute(getLatestSnapshotQuery)

        try:
            latestTrendDateString = str(replyList[0])[3:-4]
        except:
            latestTrendDateString = '1970-01-01 00:00:00'
        self.latestTrendDateString = (datetime.datetime.strptime(latestTrendDateString,"%Y-%m-%d %H:%M:%S") + datetime.timedelta(days=1))

        print("latestTrendDateString is :" + latestTrendDateString)        

        for project in allProjectsList['Project']:

            print("getting trend for project:{0:s}".format(project))
            trend_request_data = {
                'projectId': {
                    'name': project
                },
                'filterSpec': {
                    # Adding one second to the latest time because if we don't it'll retrieve the last item again as a duplicate
                    'startDate':self.latestTrendDateString,
                }
            }

            trendlist = self.connectionDefect.service.getTrendRecordsForProject(**trend_request_data)


            for day in trendlist:
                mytable.loc[row]=[project,day.codeLineCount/1000,day.outstandingCount,day.fixedCount ,day.dismissedCount,self.convertDate(day.metricsDate)]
                row=row+1

        self.db.dftotable(mytable, 'projectTrends')
        return mytable

    def getProjectTrends(self, project):
        return self.db.tabletodf('select * from projectTrends where "Project" = "{0:s}";'.format(project))        

    def getProjectList(self):
        return self.db.tabletodf('select DISTINCT "Project" from snapShotsLatest;')        

    def getLatestSnapshots(self):
        return self.db.tabletodf('select * from snapShotsLatest;')  

    def getStreamList(self, project):
        return self.db.tabletodf('select "Stream" from snapShotsLatest where "Project" = "{0:s}";'.format(project))      

    def getDefectStats(self,project,stream):
        return self.db.tabletodf('select * from defectStats where "Project" = "{0:s}" and "Stream" = "{1:s}"'.format(project,stream))

    def getSnapshotsForStream(self,project,stream):
        return self.db.tabletodf('select * from snapShots where "Project" = "{0:s}" and "Stream" = "{1:s}"'.format(project,stream))     

    def getSnapshots(self):
        return self.db.tabletodf('select * from snapShots')

    def getNewSnapshots(self):
        print('select * from snapShots where "Date" > "{:%Y-%m-%d %H:%M:%S}";'.format(self.latestDate))
        return self.db.tabletodf('select * from snapShots where "Date" > "{:%Y-%m-%d %H:%M:%S}";'.format(self.latestDate))


    def getNestedAttributeTuple(self,groupTuple,searchString):
        # this for loop is only styled this way because I was trying a different way to do a for loop
        for i in range(len(groupTuple)):
            if groupTuple[i].attributeDefinitionId.name == searchString:
                return groupTuple[i].attributeValueId.name
        return 'XXX' # should never happen

    def convertDate(self, coverityDate):

        #This converts the date to an sqlite happy format!    
        #The try except is here because sometimes Coverity doesnt have the .023423 microsecond on the commit time. Probably a back compatibility thing
        try:
            happydate = datetime.datetime.fromtimestamp(time.mktime(time.strptime(str(coverityDate)[:-6],"%Y-%m-%d %H:%M:%S.%f")))
        except:
            happydate = datetime.datetime.fromtimestamp(time.mktime(time.strptime(str(coverityDate)[:-6],"%Y-%m-%d %H:%M:%S")))

        return happydate
