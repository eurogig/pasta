from plotly import graph_objs as go

def pie_chart(df, column, g_title = 'Pie Chart'):
#    df = df.dropna(subset=["Type", "Reason", "Origin"])
    nb_cases = len(df.index)
    types = []
    values = []

    types = df[column].unique().tolist()
    for case_type in types:
        nb_type = df.loc[df[column] == case_type].shape[0]
        values.append(nb_type / nb_cases * 100)

    trace = go.Pie(
        labels=types,
        values=values,
        hole = 0.6,
        marker={"colors": ["#264e86", "#0074e4", "#74dbef", "#eff0f4"]},
    )

    layout = go.Layout(
        title=g_title,
        font = dict(color='#333'),
        titlefont=dict(color='#CCCCCC', size=14),
        plot_bgcolor="#191A1A",
        paper_bgcolor="#020202",
        legend = dict(
            font=dict(color='#CCCCCC', size=10),
            orientation='h',
            bgcolor='rgba(0,0,0,0)')
    )
    return {"data": [trace], "layout": layout}


def stackedbar (df, y_columns, x_column = 'Date', g_title = 'Stacked Bar'):

    # priority filtering

    data = []
    #tmp = df.sort_values([x_column], ascending=True)
    dates = df['Date'].tolist()
    print ("Dates:")
    print(dates)
    #print (tmp['High'].tolist())
    for col in y_columns:
        data_trace = go.Bar(
            x=dates, y=df[col].tolist(), name=col
        )
        data.append(data_trace)

    layout = go.Layout(
        barmode="stack",
        title=g_title,
        font = dict(color='#d8d9da'),
        titlefont=dict(color='#CCCCCC', size=14),
        plot_bgcolor="#191A1A",
        paper_bgcolor="#020202",
        legend = dict(
            font=dict(color='#CCCCCC', size=10),
            orientation='h',
            bgcolor='rgba(0,0,0,0)'),      
#        title=g_title
    )

    return {"data": data, "layout": layout}

def scatter_chart(df, y_columns, x_column = 'Date', g_title = 'Scatter Chart'):

    data = []

    for col in y_columns:

        trace1 = go.Scatter(
        x=df[x_column],
        y=df[col],
        text=df["Project"],
        mode = 'markers'
        )

        data.append(trace1)

    layout = go.Layout(
#       xaxis=dict(showgrid=False),
        yaxis=dict(
        title= 'Stream',
        ticklen= 5,
        gridwidth= 2,
        ),
        margin=dict(l=200, r=5, b=37, t=50, pad=10),
        title=g_title,
        height=800,
        font = dict(color='#d8d9da'),
        titlefont=dict(color='#CCCCCC', size=14),
        plot_bgcolor="#191A1A",
        paper_bgcolor="#020202",
        legend = dict(
            font=dict(color='#CCCCCC', size=10),
            orientation='h',
            bgcolor='rgba(0,0,0,0)')        
    )

    return {"data": data, "layout": layout}

def line_chart(df, y_columns, x_column = 'Date', g_title = 'Line Chart'):

    data = []

    for col in y_columns:

        if ((col != 'Date') & (col != 'Project') & (col != 'LOC')):
                trace1 = go.Scatter(
                x=df[x_column],
                y=df[col],
                name=col,
                )

                data.append(trace1)

    layout = go.Layout(
#        xaxis=dict(showgrid=False),
        margin=dict(l=40, r=25, b=37, t=37, pad=10),
        title=g_title,
        font = dict(color='#d8d9da'),
        titlefont=dict(color='#CCCCCC', size=14),
        plot_bgcolor="#191A1A",
        paper_bgcolor="#020202",
        legend = dict(
            font=dict(color='#CCCCCC', size=10),
            orientation='h',
            bgcolor='rgba(0,0,0,0)')          
    )

    return {"data": data, "layout": layout}


