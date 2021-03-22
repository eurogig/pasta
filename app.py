# Get all the dash parts
import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import dash_table 
import uuid

# Pandas for dataframe processing
import pandas as pd
import json

from localdb import DB as DBcache
from coverityConnection import Coverity as CConnect

# External modules for fetching data
#import table_cov_streamlist as tcs
#import table_cov_defectlist as tcd
#import table_cov_projecttrends as tct

# External modules for generating Plotly widgets
import graphElements as gE

# Date and time
import datetime as dtime
import time
from datetime import timedelta

# Need to trash these external stylesheets and make my own.  Working for now.

#external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
#app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app = dash.Dash(__name__)
#app.css.append_css({'external_url': 'https://cdn.rawgit.com/plotly/dash-app-stylesheets/2d266c578d2a6e8850ebce48fdb52759b2aef506/stylesheet-oil-and-gas.css'})
#app.css.append_css({'external_url': 'https://cdn.rawgit.com/amadoukane96/8a8cfdac5d2cecad866952c52a70a50e/raw/cd5a9bf0b30856f4fc7e3812162c74bfc0ebe011/dash_crm.css'})
# app.scripts.config.serve_locally = True
# app.css.config.serve_locally = True

# Default Settings for debug
app.config['currentStream'] = 'JenkinsFull'
currentSnapshot = '10000'

app.config['suppress_callback_exceptions']=True
app.config['coverityurl']=''
app.config['user']=''
app.config['passkey']=''
app.config['connected']=False
app.config['currentProject'] = 'Jenkins2018'
app.config['connection'] = None


tabs_styles = {
    'height': '44px'
}
tab_style = {
    'borderBottom': '1px solid #444',
    'border-color': '#444',
    'padding': '6px',
    #'fontWeight': 'bold',
    'color': 'white',
    'border-top-left-radius': '1em',
    'border-top-right-radius': '1em',
    'backgroundColor': '#222'
}

tab_selected_style = {
    'borderTop': '1px solid #444',
    'border-color': '#444',
    'borderBottom': '0px solid #d6d6d6',
    'backgroundColor': '#000',
    'color': 'white',
    'fontWeight': 'bold',    
    'padding': '6px',
    'border-top-left-radius': '1em',
    'border-top-right-radius': '1em'    
}


# A function to generate a non dynamic table.  Might switch to this once I change the current plotly table to dropdown filters.  Not used currently.
def generate_table(dataframe, max_rows=10):

    return html.Table(
        # Header
        [html.Tr([html.Th(col) for col in dataframe.columns])] +

        # Body
        [html.Tr([
            html.Td(dataframe.iloc[i][col]) for col in dataframe.columns
        ], style={'background-color':'black'}) for i in range(min(len(dataframe), max_rows))]
    )


# THE MAIN LAYOUT FOR THE HOME AND TABS

app.layout = html.Div([

    html.Div(id='auth-content-example'),
    html.Div([html.H4('')], style={'background-image': 'url("static/logo.png")','background-repeat': 'no-repeat','width':'300px', 'height':'100px','padding':5}),
    #html.Div([html.H4('Platform Application Security Testing Analytics')], style={'background-color':'black','color':'white','width':'100%','padding':5}),
        html.Div([
        dcc.Input(
            id='cov-url',
            placeholder='Coverity URL',
            type='text',
            value=app.config['coverityurl']
        )], style={'float':'right','padding':5}),
        html.Div([
        dcc.Input(
            id='cov-passkey',
            placeholder='Passkey',
            type='password',
            value=''
        )], style={'float':'right','padding':5}),
        html.Div([
        dcc.Input(
            id='cov-user',
            placeholder='UserID',
            type='text',
            value=app.config['user']
        )], style={'float':'right','padding':5}),        
        html.Div([
            html.Button('Connect', id='login'),
        ], style={'float':'right','padding':5}),
        html.Div([
            html.Div([
                dcc.Dropdown(
                options=[
                    {'label': 'Not Connected', 'value': 'Project100'}
                ],
                multi=False,
                id='projectDropdown',
                value="Project100",
                clearable=False
                ),
            ], style={'float':'left','width':'20%','padding':5,'color':'black'} ),
            html.Div([
                dcc.Dropdown(
                options=[
                    {'label': 'Not Connected', 'value': 'Stream100'}
                ],
                multi=False,
                id='streamDropdown',
                value="Stream100"
                ),
            ], style={'float':'left','width':'20%','padding':5,'color':'black'} ),  
            html.Div([
                html.H5(['Enter Credentials to Connect'],id='statusbar')
            ], style={'float':'right','width':'60%','padding':5,'color':'white','text-align':'right'} ),                
        ], style={'display':'flex','width':'100%','padding':5} ),
    dcc.Tabs(id="tabs-example", value='tab-3-example', children=[
        dcc.Tab(label='Trend', value='tab-3-example', style=tab_style, selected_style=tab_selected_style),
        dcc.Tab(label='Defects', value='tab-1-example', style=tab_style, selected_style=tab_selected_style),
        dcc.Tab(label='Snapshots', value='tab-2-example', style=tab_style, selected_style=tab_selected_style),
        dcc.Tab(label='Data', value='tab-0-example', style=tab_style, selected_style=tab_selected_style),
    ]),
    html.Div(id='tabs-content-example', children=[

        #html.Div(id='datatablemain', children=[
            html.H4('Enter Details to Connect to Coverity'),
                dash_table.DataTable(
                    id='datatable-interactivity',
                    columns=[
                       
                    ],
                    data=[{}],
                    filtering=True,
                    sorting=True,
                    selected_rows=[],
                ),
            ], style={'width':'100%','padding':5, 'color':'black'} ),
	    #]),
    #]),
    #html.Div(id='table-content-example'),
], style={'width':'99%','padding':0})

# ****** CALL BACKS *******************
# Call backs in Dash/Plotly create React based responses on the front-end.  Way better than learning React.


# THIS CALL BACK POPULATES THE TAB WITH DYNAMIC CONTENT UPON TAB SWITCH

@app.callback(Output('tabs-content-example', 'children'),
              [Input('tabs-example', 'value'),
              Input('streamDropdown', 'value')])
def render_content(tab, stream):
    if (app.config['connected']):
        app.config['currentStream'] = stream
        return render_current_tab(tab)
    else:
        return None


def render_current_tab(tab):
    if tab == 'tab-1-example':
        #global DF_TCDS
        #DF_TCDS = tcd.get_defect_stats('http://192.168.99.1:8080','admin','15b6bd065594e5bb3e486469a1014235',app.config['currentProject'],app.config['app.config['currentStream']'])
        #DF_TCDS.sort_values(['Date'], ascending=True, inplace=True)
        print("Project:{0:s} Stream:{1:s}".format(app.config['currentProject'],app.config['currentStream']))
        DF_TCDS = app.config['connection'].getDefectStats(app.config['currentProject'],app.config['currentStream'])
        DF_TCDS.sort_values('Date', ascending=True, inplace=True)
        #DF_TCDS = df.loc[(df['Project'] == app.config['currentProject']) & (df['Stream'] == currentStream)]
        print (DF_TCDS)
        if DF_TCDS.empty:
            return html.Div([html.H2('Please wait... Building defect stats')],style={'padding':10,'color':'white'})
        else:
            return html.Div([

                html.H3('Detail By Snapshot'),

                html.Div(
                    [
                    html.Div(
                            [
                
                                html.P(
                                    'Total Current Defects',
                                    className="twelve columns indicator_text"
                                ),
                                html.P(
                                    DF_TCDS['Total'][0],
                                    id = 'total_defects',
                                    className="indicator_value"
                                ),
                            ],
                            className="three columns indicator",
            
                        ),
                    html.Div(
                            [
                
                                html.P(
                                    'Total Current Security Defects',
                                    className="twelve columns indicator_text"
                                ),
                                html.P(
                                    DF_TCDS['Security'][0],
                                    id = 'total_sec_defects',
                                    className="indicator_value"
                                ),
                            ],
                            className="three columns indicator",
            
                        ),                    
                    html.Div(
                            [
                
                                html.P(
                                    'Last Commit',
                                    className="twelve columns indicator_text"
                                ),
                                html.P(
                                    # The index len gives the number of snapshots.  The latest is the final one so the len-1 to index into the array
                                    DF_TCDS['Date'][0],
                                    id = 'last_commit',
                                    className="indicator_value"
                                ),
                            ],
                            className="three columns indicator",
            
                        ),
                    html.Div(
                            [
                
                                html.P(
                                    'Total Commits',
                                    className="twelve columns indicator_text"
                                ),
                                html.P(
                                    len(DF_TCDS.index),
                                    id = 'total_commits',
                                    className="indicator_value"
                                ),
                            ],
                            className="three columns indicator",
            
                        ),                    

                    ],
                    className="row", style={'display': 'flex', 'align-items': 'center', 'justify-content': 'center'}
                ),
                html.Div([html.H4('Choose Comparison Group'),
                    html.Div([
                            dcc.Dropdown(
                            options=[
                                {'label': 'Defect Impact', 'value': 'displayImpact'},
                                {'label': 'Defect Impact Security', 'value': 'displayImpact-Security'},
                                {'label': 'OWASP Top 10 2017', 'value': 'OWASP'},
                                {'label': 'Build vs Analysis Time', 'value': 'displayBuild-Analysis'}
                            ],
                            multi=False,
                            id='stackBarDropdown',
                            value="displayImpact"
                            ),
                        ], style={'width':'33%','padding-top':5,'color':'black'} ),
                    ], style={'padding':10,'color':'white'} ),
                    html.Div([
                    dcc.RadioItems(
                        options=[
                            {'label': 'Line Graph', 'value': 'line'},
                            {'label': 'Stack Bar Graph', 'value': 'stacked'},
                        ],
                        value='line',
                        id='defectGraphType',
                        labelStyle={'display': 'inline-block'}
                    )
                    ], style={'padding':10,'color':'white'} ),
                    html.Div([ dcc.Graph(
                        id='graph-2-tabs',
                        figure=gE.line_chart(DF_TCDS,['High','Medium','Low']) 
                        )
                    ], style={'padding':10}),
                    html.Div([
                        dcc.DatePickerRange(
                            id='date-picker-range',
                            #start_date=dt(1997, 5, 3),
                            end_date=dtime.datetime.now(),
                            start_date=dtime.datetime.now() - timedelta(days=60),
                            #start_date_placeholder_text='Select a date!'
                        ),
                    ], style={'width':'33%','padding-top':5} ),
            ])
    elif tab == 'tab-2-example':
        if (app.config['connected']):
            DF_TCS = app.config['connection'].getLatestSnapshots()
            DF_TCS.sort_values(['Date'], ascending=False, inplace=True)
            return html.Div([
                html.H3('Snapshots by...'),
                html.Div([
					html.Div([
					    html.Div([html.H4('Choose Snapshot Scope'),
                            html.Div([
                                dcc.Dropdown(
                                    options=[
                                        {'label': 'Latest Snapshot', 'value': 'latestSnapshot'},
                                        {'label': 'All Snapshots', 'value': 'allSnapshots'},
                                    ],
                                    multi=False,
                                    id='snapShotScopeDropDown',
                                    clearable=False,
                                    value="latestSnapshot"
                                ),
                            ], style={'width':'33%','padding-top':5,'color':'black'} )
                        ], style={'padding':10,'color':'white'} ),
						html.P("Coverity Snapshot Trends"),
						dcc.Graph(
							id="coverity_snaphot_trends",
							style={"height": "100%", "width": "99%"},
							config=dict(displayModeBar=False),
							figure = gE.scatter_chart(DF_TCS, ['Stream'], 'Date', 'Stream Snapshot Timings')
						),
                    ], style={'padding':10, 'width':'100%'}),
                ]),
                html.Div([
                html.Div([
                dcc.Graph(
                    id="snapshots_version",
                    config=dict(displayModeBar=False),
                    figure = gE.pie_chart(DF_TCS,'Analysis Version', 'Snapshots by Analysis Version ')
                )
                ], style={'float':'left','width':'49%'}),
                html.Div([
                dcc.Graph(
                    id="snapshots_host",
                    config=dict(displayModeBar=False),
                    figure = gE.pie_chart(DF_TCS,'Analysis Host', 'Snapshots by Analysis Host')
                )
                ], style={'float':'left','width':'49%'})
                ], style={'display':'flex','padding':10}),                
            ])
    elif tab == 'tab-0-example':
        if (app.config['connected']):
            DF_TCS = app.config['connection'].getLatestSnapshots()
            DF_TCS.sort_values(['Date'], ascending=False, inplace=True)
            print("I should be drawing a table right now")
            return html.Div(id='datatablemain', children=[
                #db = DBcache(app.config['user'] + app.config['passkey'] + '.db')
                html.H4('Latest Snapshots'),
                #dt.DataTable(
                        # Initialise the rows
                #rows=DF_TCS.to_dict('records'),
                #columns=(DF_TCS.columns),
                ##row_selectable=True,
                #filterable=True,
                #sortable=True,
                ##selected_row_indices=[0],
                #id='awesometable'), 

                #generate_table(DF_TCS, 13)
                dash_table.DataTable(
                    id='datatable-interactivity',
                    columns=[
                        {"name": i, "id": i} for i in DF_TCS.columns
                    ],
                    style_cell_conditional=[
                        {
                            'if': {'row_index': 'odd'},
                            'backgroundColor': 'rgb(0, 0, 0)'
                        }
                    ]+ [
                        {
                            'if': {'row_index': 'even'},
                            'backgroundColor': 'rgb(30, 30, 30)'
                        }
                    ],
                    style_header={
                        'backgroundColor': 'grey',
                        'fontWeight': 'bold'
                    },
                    style_table={'width':'99%'},
                    style_cell={
                        'minWidth': '0px', 'maxWidth': '180px',
                        'whiteSpace': 'normal',
                        'border':'black'
                    },
                    css=[{
                        'selector': '.dash-cell div.dash-cell-value',
                        'rule': 'display: inline; white-space: inherit; overflow: inherit; text-overflow: inherit;',
                        'border': '1px solid black'
                    }],
                    data=DF_TCS.to_dict("rows"),
                    filtering=False,
                    content_style='grow',
                    sorting=True,
                    sorting_type="single",
                    selected_rows=[],
                ),
            ], style={'background-color':'#111','color':'azure','padding':'10px','width':'100%'})
        else:
                return html.Div(id='datatablemain', children=[
                #db = DBcache(app.config['user'] + app.config['passkey'] + '.db')
                html.H4('Latest Snapshots'),
                dt.DataTable(
                        # Initialise the rows
                rows=[{}],
                #columns=(DF_TCS.columns),
                #row_selectable=True,
                filterable=True,
                sortable=True,
                #selected_row_indices=[0],
                id='awesometable'), 
            ], style={'background-color':'#111','color':'azure','padding':'10px'})              
    elif tab == 'tab-3-example':
        if (app.config['connected']):
            #DF_TCT = tct.get_trends('http://192.168.99.1:8080','admin','15b6bd065594e5bb3e486469a1014235',app.config['currentProject'],app.config['currentStream'])
            DF_TCT = app.config['connection'].getProjectTrends(app.config['currentProject'])
            return html.Div([
                #html.H3('Something Over Time...'),

                html.Div(
                [
                    html.P("Coverity Stream Trends"),
                    dcc.Graph(
                        id="coverity_trends",
                        style={"height": "110%", "width": "98%"},
                        config=dict(displayModeBar=False),
                        figure = gE.line_chart(DF_TCT, DF_TCT.columns, 'Date', 'Project Defect Trends: ' + DF_TCT['Project'][0])
                    ),
                ],style={'padding':10,'width':'100%'}),

            ], style={'background-color':'#000','color':'#fff'})


@app.callback(Output('projectDropdown', 'options'),
#@app.callback(Output('datatablemain', 'children'),
              [Input('login', 'n_clicks')],
              [State('cov-url', 'value'), State('cov-passkey', 'value'),
               State('cov-user', 'value')])
def update_projectlist(n_clicks, value_url, value_passkey, value_user):
#    return 'The user was "{}" with passkey "{}" and the url is "{}" '.format(

    app.config['coverityurl']=value_url
    app.config['user']=value_user
    app.config['passkey']=value_passkey
    poptions=[]   
    if (app.config['coverityurl']):
        #db = DBcache(app.config['user'] + app.config['passkey'] + '.db')
        if (app.config['connection'] == None):
            app.config['connection'] = CConnect(app.config['user'],app.config['passkey'], app.config['coverityurl'])   
        app.config['connected']=True 
        #if (app.config['connected']==True):
    #    time.sleep(.300)

        projectList = app.config['connection'].getProjectList()
        print("projects!")
        print(projectList)
 
        for project in projectList['Project']:
            poptions.append({'label': project, 'value': project})
    else:
        poptions = [
                    {'label': 'Not Connected', 'value': 'Project100'}
                ] 

    return poptions



@app.callback(Output('streamDropdown', 'options'),
#@app.callback(Output('datatablemain', 'children'),
              [Input('projectDropdown', 'value')])
def update_streamlist(projectValue):
#    return 'The user was "{}" with passkey "{}" and the url is "{}" '.format(

    if ((app.config['connected']==True) & (bool(projectValue))):
        app.config['currentProject'] = projectValue
        streamList = app.config['connection'].getStreamList(projectValue)
        poptions=[]
        for stream in streamList['Stream']:
            poptions.append({'label': stream, 'value': stream})       
        print("Poptions") 
        print(poptions)   
        return poptions
        #[
        #{'label': 'blabh', 'value': 'Projbrbrrbbect10'},
        #{'label': 'Projasdfasect16', 'value': 'brbasdf'},
        #{'label': 'asdasdf', 'value': 'dddddd'} 
        #]


# The CALLBACK for the dropdown selector to choose how to few defects and change the stacked bar graph dynamically.
@app.callback(Output('graph-2-tabs', 'figure'),
              [Input('stackBarDropdown', 'value'), Input('defectGraphType', 'value')])
def update_stack(grouper, graphType):
    if (grouper == 'displayBuild-Analysis'):
        DF_THIS = app.config['connection'].getSnapshotsForStream(app.config['currentProject'],app.config['currentStream'])
    else:
        DF_THIS = app.config['connection'].getDefectStats(app.config['currentProject'],app.config['currentStream'])
        DF_THIS.sort_values('Date', ascending=True, inplace=True)
    if (grouper == 'displayImpact'):
        breakDown = ['High','Medium','Low']
    elif (grouper == 'OWASP'):
        breakDown = ['A1','A2','A3','A4','A5','A6','A7','A8','A9','A10']
    elif (grouper == 'displayImpact-Security'):
        breakDown = ['High Security','Medium Security','Low Security']
    elif (grouper == 'displayBuild-Analysis'):
        breakDown = ['Build Time','Analysis Time'] 
    if (graphType == 'stacked'):
        return gE.stackedbar(DF_THIS,breakDown)   
    elif (graphType == 'line'):         
        return gE.line_chart(DF_THIS, breakDown)    

# The CALLBACK for the dropdown selector to choose how to show all or latest snapshot
@app.callback(Output('coverity_snaphot_trends', 'figure'),
              [Input('snapShotScopeDropDown', 'value')])
def update_scatter(scope):
    if (scope == 'allSnapshots'):
        DF_TCS = app.config['connection'].getSnapshots()
    elif (scope == 'latestSnapshot'):         
        DF_TCS = app.config['connection'].getLatestSnapshots()
    DF_TCS.sort_values(['Date'], ascending=False, inplace=True)
    return gE.scatter_chart(DF_TCS, ['Stream'], 'Date', 'Stream Snapshot Timings')
       

## The CALLBACK for the dropdown selector to choose how to show all or latest snapshot
#@app.callback(Output('snapshots_version', 'figure'),
#              [Input('snapShotScopeDropDown', 'value')])
#def update_pie1(scope):
#    if (scope == 'allSnapshots'):
#        DF_TCS = app.config['connection'].getSnapshots()
#    elif (scope == 'latestSnapshot'):         
#        DF_TCS = app.config['connection'].getLatestSnapshots()
#    DF_TCS.sort_values(['Date'], ascending=False, inplace=True)
#    return gE.pie_chart(DF_TCS,'Analysis Version', 'Snapshots by Analysis Version ')
       

# The CALLBACK for the dropdown selector to choose how to show all or latest snapshot
#@app.callback(Output('snapshots_host', 'figure'),
#              [Input('snapShotScopeDropDown', 'value')])
#def update_stack(scope):
#    if (scope == 'allSnapshots'):
#        DF_TCS = app.config['connection'].getSnapshots()
#    elif (scope == 'latestSnapshot'):         
#        DF_TCS = app.config['connection'].getLatestSnapshots()
#    DF_TCS.sort_values(['Date'], ascending=False, inplace=True)
#    return gE.pie_chart(DF_TCS,'Analysis Host', 'Snapshots by Analysis Host')
       



# START THE DASH APP

if __name__ == '__main__':
    app.run_server(host='0.0.0.0', debug=True)
