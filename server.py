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


history_df = pd.read_csv(ut['history_path'], parse_dates=['date'])
history_df.pos += 1
history_fig = px.line(history_df, x='date', y='pos', color='alias', markers=True)

options = []
for result in result_list:
    options.append(dict(
        label=path.basename(result),
        value=result
    ))
options.sort(key=lambda x: x['value'], reverse=True)
app.layout = html.Div(id = 'parent', children = [
    html.H1(id = 'H1', children = 'Proxy curl Google', style = {'textAlign':'center', 'marginTop':10,'marginBottom':10}),
    dcc.Dropdown( id = 'dropdown',
        options = options,
        value = options[0]['value'],
        style = {'marginTop':0,'marginBottom':0}
    ),
    dcc.Graph(id = 'curl_mix', style = {'marginTop':0,'marginBottom':0}),
    dcc.Graph(id = 'curl_curve', style = {'marginTop':0,'marginBottom':0}, config={'displayModeBar': False}),
    dcc.Graph(id = 'server_history', style = {'marginTop':0,'marginBottom':0}, config={'displayModeBar': False}),
    dcc.Graph(id = 'all_history', style = {'marginTop':0,'marginBottom':0}, figure=history_fig)
    ])

    

@app.callback(Output(component_id='curl_mix', component_property= 'figure'),
              [Input(component_id='dropdown', component_property= 'value')])
def update_violin(data_path):
    global df
    #print(data_path)
    df = df_from_json(data_path)

    df_agg = rank(df)
    df_agg['pos'] = df_agg.index + 1

    fig = make_subplots(
        rows=5, cols=1,
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
    fig.add_trace(
        go.Bar(x=df_agg['alias'], y=df_agg['pos'], name='Rank', marker_color='purple',
               text=df_agg['pos'], textposition='auto', textangle=0),
        row=4, col=1
    )
    fig.add_trace(
        go.Violin(x=history_df['alias'], y=history_df['pos'], name='History', marker_color='gray'),
        row=5, col=1
    )
    fig.update_layout(barmode='relative')
    return fig

    
def _update_curl(data):
    #print(data)
    if not data:
        return px.scatter(template='plotly_white')
    alias = data['points'][0]['x']
    df_alias = df[df.alias==alias].reset_index(drop=True)
    #print(df_alias)
    
    fig_curl = px.scatter(df_alias, y='curl', text=df_alias['curl'], title=f"{alias} (Curl延迟)", template='plotly_white')
    fig_curl.update_traces(mode='lines+markers+text', textposition="bottom right")
    
    return fig_curl
    

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


def _update_history(data):
    #print(data)
    if not data:
        return px.scatter()
    alias = data['points'][0]['x']
    df_alias = history_df[history_df.alias==alias]
    #print(df_alias)
    fig_hist = px.scatter(df_alias, x='date', y='pos', text=df_alias['pos'], title=f"{alias} (历史排名)")
    fig_hist.update_traces(mode='lines+markers+text', textposition="bottom right")
    return fig_hist


@app.callback(
    dash.dependencies.Output('server_history', 'figure'),
    dash.dependencies.Input('curl_mix', 'hoverData'),
    dash.dependencies.Input('curl_mix', 'clickData'))
def update_history(hoverData, clickData):
    return _update_history(hoverData if hoverData else clickData)



if __name__ == '__main__':
    is_prod = ut.env() == 'prod'
    app.run_server(
        host='0.0.0.0' if is_prod else '127.0.0.1', 
        debug=not is_prod,
        reload=True
    )