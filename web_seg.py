import dash
from dash import html
from dash import dcc
import plotly.graph_objects as go
import plotly.express as px
from dash.dependencies import Input, Output
import pandas as pd
from os import name, path
from utils import ut
from pybeans import utils as pu

import glob
result_list = glob.glob('./data/*.json')
print(result_list)


app = dash.Dash(__name__)

options = []
for result in result_list:
    options.append(dict(
        label=path.basename(result),
        value=result
    ))
options.sort(key=lambda x: x['value'], reverse=True)
app.layout = html.Div(id = 'parent', children = [
    html.H1(id = 'H1', children = 'Proxy curl Google time', style = {'textAlign':'center',\
                                            'marginTop':40,'marginBottom':40}),

        dcc.Dropdown( id = 'dropdown',
        options = options,
        value = options[0]['value']),
        dcc.Graph(id = 'curl_violin'),
        dcc.Graph(id = 'avg_bar', hoverData={'points': [{'customdata': [100]}]}),
        dcc.Graph(id = 'lost_bar'),
        dcc.Graph(id = 'curl_curve'),
    ])

    
@app.callback(Output(component_id='curl_violin', component_property= 'figure'),
              [Input(component_id='dropdown', component_property= 'value')])
def update_violin(dropdown_value):
    #print(dropdown_value)
    result = pu.load_json(dropdown_value)
    df = pd.json_normalize(
        result,
        record_path=['raw'],
        meta=[
            'alias'
        ]
    )
    df.rename(columns={0: 'curl'}, inplace=True)
    #print(df)
    fig = px.violin(df, x='alias', y='curl')
    fig.update_layout(
                      yaxis_title = 'Curl time (ms)',
                      legend = dict(x=0.01, y=0.99))
    return fig

    
@app.callback(Output(component_id='avg_bar', component_property= 'figure'),
              [Input(component_id='dropdown', component_property= 'value')])
def update_curl_bar(dropdown_value):
    #print(dropdown_value)
    result = pu.load_json(dropdown_value)
    remarks = [x['alias'] for x in result]
    curls = [x['curl'] for x in result]
    losts = [x['timeout'] for x in result]
    raws = [x['raw'] for x in result]
    hover_curls = [f"Curl={x['curl']}, Lost={x['timeout']}" for x in result]
    hover_losts = [f"Lost={x['timeout']}" for x in result]

    fig = go.Figure()
    fig.add_trace(go.Bar(x=remarks, y=curls, name='Google curl', hovertext=hover_curls))
    fig.add_trace(go.Bar(x=remarks, y=losts, name='Timeout (10s)', hovertext=hover_losts))
    fig.update_traces(opacity=0.8, customdata=raws)
    
    fig.update_layout(
                      yaxis_title = 'Curl time (ms)',
                      barmode='overlay', legend=dict(x=0.01, y=0.99)
                      )
    return fig


@app.callback(Output(component_id='lost_bar', component_property= 'figure'),
              [Input(component_id='dropdown', component_property= 'value')])
def update_lost_bar(dropdown_value):
    #print(dropdown_value)
    result = pu.load_json(dropdown_value)
    remarks = [x['alias'] for x in result]
    curls = [x['curl'] for x in result]
    losts = [x['timeout'] for x in result]
    raws = [x['raw'] for x in result]
    hover_curls = [f"Curl={x['curl']}, Lost={x['timeout']}" for x in result]
    hover_losts = [f"Lost={x['timeout']}" for x in result]

    fig = px.bar(x=remarks, y=losts)
    fig.update_traces(marker_color='red')
    fig.update_layout(
                      yaxis_title = 'Timeout (10s)',
                      legend=dict(x=0.01, y=0.99)
                      )
    return fig


@app.callback(
    dash.dependencies.Output('curl_curve', 'figure'),
    [dash.dependencies.Input('avg_bar', 'hoverData')])
def update_curl(hoverData):
    #print(hoverData)
    curl_raws = hoverData['points'][0]['customdata']
    fig = px.scatter(curl_raws)
    fig.update_traces(mode='lines+markers')
    fig.update_layout(height=225, margin={'l': 20, 'b': 30, 'r': 10, 't': 10}, legend=dict(x=0.01, y=0.99))
    return fig


if __name__ == '__main__': 
    app.run_server(host='0.0.0.0', debug=(ut.env()!='prod'))