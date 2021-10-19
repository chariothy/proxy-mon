import dash
from dash import html
from dash import dcc
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from dash.dependencies import Input, Output
import pandas as pd
from os import name, path
from utils import ut
from pybeans import utils as pu
from rank import rank, df_from_json

import glob
result_list = glob.glob('./data/*.json')
#print(result_list)

df = None
app = dash.Dash(__name__)
app.title = 'Proxy benchmark'

options = []
for result in result_list:
    options.append(dict(
        label=path.basename(result),
        value=result
    ))
options.sort(key=lambda x: x['value'], reverse=True)
app.layout = html.Div(id = 'parent', children = [
    html.H1(id = 'H1', children = 'Proxy curl Google', style = {'textAlign':'center',\
                                            'marginTop':40,'marginBottom':40}),

        dcc.Dropdown( id = 'dropdown',
        options = options,
        value = options[0]['value']),
        dcc.Graph(id = 'curl_mix'),
        dcc.Graph(id = 'curl_curve'),
    ])

    
@app.callback(Output(component_id='curl_mix', component_property= 'figure'),
              [Input(component_id='dropdown', component_property= 'value')])
def update_violin(data_path):
    global df
    #print(data_path)
    df = df_from_json(data_path)
    df_agg = rank(df)

    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0
    )
    fig.add_trace(
        go.Violin(x=df['alias'], y=df['curl'], name='Violin'),
        row=1, col=1
    )
    fig.add_trace(
        go.Bar(x=df_agg['alias'], y=df_agg['avg'], name='AVG', marker_color='green',
               text=df_agg['avg'], textposition='auto', textangle=0, texttemplate='%{y:.0f}'),
        row=2, col=1
    )
    fig.add_trace(
        go.Bar(x=df_agg['alias'], y=df_agg['lost']*-1, name='Lost', marker_color='red',
               text=df_agg['lost'], textposition='auto', textangle=0),
        row=3, col=1
    )
    fig.update_layout(barmode='relative')
    return fig

    
def _update_curl(data):
    #print(data)
    if not data:
        return px.scatter()
    alias = data['points'][0]['x']
    df_alias = df[df.alias==alias].reset_index(drop=True)
    #print(df_alias)
    fig = px.scatter(df_alias, y='curl', text=df_alias['curl'])
    fig.update_traces(mode='lines+markers+text', textposition="bottom right")
    return fig
    

@app.callback(
    dash.dependencies.Output('curl_curve', 'figure'),
    dash.dependencies.Input('curl_mix', 'hoverData'),
    dash.dependencies.Input('curl_mix', 'clickData'))
def update_curl(hoverData, clickData):
    #ctx = dash.callback_context
    #import json
    # ctx_json = json.dumps({
    #     'states': ctx.states,
    #     'triggered': ctx.triggered,
    #     'inputs': ctx.inputs
    # }, indent=2, ensure_ascii=False)
    #print(ctx_json)
    return _update_curl(hoverData if hoverData else clickData)


if __name__ == '__main__':
    is_prod = ut.env() == 'prod'
    app.run_server(
        host='0.0.0.0' if is_prod else '127.0.0.1', 
        debug=True, extra_files=['./data/*.json']
    )