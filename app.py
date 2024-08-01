from dash import Dash, html, dcc, Output, Input, callback, ctx, State
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from funcs import create_graph_card, create_main_graph, create_map_graph, graph_highlight
from dash_bootstrap_templates import load_figure_template
import pandas as pd


code = {'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR',
        'California': 'CA', 'Colorado': 'CO', 'Connecticut': 'CT', 'Delaware': 'DE',
        'District of Columbia': 'DC', 'Florida': 'FL', 'Georgia': 'GA', 'Hawaii': 'HI',
        'Idaho': 'ID', 'Illinois': 'IL', 'Indiana': 'IN', 'Iowa': 'IA',
        'Kansas': 'KS', 'Kentucky': 'KY', 'Louisiana': 'LA', 'Maine': 'ME',
        'Maryland': 'MD', 'Massachusetts': 'MA', 'Michigan': 'MI', 'Minnesota': 'MN',
        'Mississippi': 'MS', 'Missouri': 'MO', 'Montana': 'MT', 'Nebraska': 'NE',
        'Nevada': 'NV', 'New Hampshire': 'NH', 'New Jersey': 'NJ', 'New Mexico': 'NM',
        'New York': 'NY', 'North Carolina': 'NC', 'North Dakota': 'ND', 'Ohio': 'OH',
        'Oklahoma': 'OK', 'Oregon': 'OR', 'Pennsylvania': 'PA', 'Rhode Island': 'RI',
        'South Carolina': 'SC', 'South Dakota': 'SD', 'Tennessee': 'TN', 'Texas': 'TX',
        'Utah': 'UT', 'Vermont': 'VT', 'Virginia': 'VA', 'Washington': 'WA',
        'West Virginia': 'WV', 'Wisconsin': 'WI', 'Wyoming': 'WY'}

main_df = pd.read_csv('data.csv')
main_df['state_code'] = main_df['state'].map(code)
main_df['Investment Dollars'] = main_df['Investment Dollars'].str.replace(',', '').astype(int)


app = Dash(__name__, external_stylesheets=[dbc.themes.YETI, dbc.icons.BOOTSTRAP])
load_figure_template("yeti") # using a template for consistant graphs formatting

# Creating the cards that contain the different graphs
by_program = create_graph_card('by_program')
by_state = create_graph_card('by_state')

# a dash mantine button menue to switch the column value of the graphs
choices = html.Div(
    [
        dmc.SegmentedControl(
            id="segmented",
            value="Investment Dollars",
            data=[{"value": "Investment Dollars", "label": "Investment Dollars"},
                  {"value": "Number of Investments", "label": "Number of Investments"},
                  ],
            color='blue.9',
            fullWidth=True,
            className='fw-bold shadow-sm mt-2',
        ),
    ]
)


column_heigh_style = {"height": "100%"}
data = {'last_program': None, 'last_state': None, 'program_filtered': None, 'state_filtered': False, 'inputs': []}


app.layout = dbc.Container(
        # the dcc.Store holds 'gloabal variables' that will be used for the corss-filtering logic inside the callback
    [
        dcc.Store(id='store', data=data),
        dbc.Row(dbc.Col(choices, width={'offset': 1, "size": 3}), className='mt-3'),
        dbc.Row([dbc.Col(by_state, width=5, style=column_heigh_style), dbc.Col(by_program, width=5, style=column_heigh_style)],
                className='my-4',
                justify='around'),
        ],
    fluid=True,
    style={'background-color': '#F8F9F9', "height": '100vh'}
)


@callback([
Output('by_program', 'figure'), Output('by_state', 'figure'), Output('by_program', 'clickData'),
Output('by_state', 'clickData'), Output('store', 'data')
],
           [Input('segmented', 'value'), Input('by_program', 'clickData'), Input('by_state', 'clickData')],
State('store', 'data'))
def update_graphs(value, clicked_program, clicked_state, app_state):
   # make a copy of the dataframe for each graph
    program_df = main_df.copy()
    state_df = main_df.copy()

   # get the values of the 'global variables' from the dcc.Store input
    last_program = app_state['last_program']
    last_state = app_state['last_state']
    program_filtered = app_state['program_filtered']
    state_filtered = app_state['state_filtered']
    inputs = app_state['inputs']
    graph_trigger = ctx.triggered_id # get which figure triggered the callback

    dict = {}
    if graph_trigger == 'by_program':
        dict = {'input': ctx.triggered[0]['prop_id'].split('.')[0], 'value':ctx.triggered[0]['value']['points'][0]['x']}
        inputs.append(dict)

    if graph_trigger == 'by_state':
        dict = {'input': ctx.triggered[0]['prop_id'].split('.')[0], 'value': ctx.triggered[0]['value']['points'][0]['location']}
        inputs.append(dict)

    # Keeping a list of slected values for each graph to be used for filtering
    program_list = [d.get('value') for d in inputs if d.get('input') == 'by_program']
    state_list = [d.get('value') for d in inputs if d.get('input') == 'by_state']

    # get the current selected value for each figure
    selected_program = program_list[-1] if len(program_list) >= 1 else None
    selected_state = state_list[-1] if len(state_list) >= 1 else None


    if selected_program is not None:
        if program_filtered and selected_program == last_program and graph_trigger == 'by_program':
            program_filtered = False
        elif program_filtered == False and graph_trigger != 'by_program':
            program_filtered = False
        else:
            state_df = state_df[state_df['program'] == selected_program]
            last_program = selected_program
            program_filtered = True
    else:
        program_filtered = False


    if selected_state is not None:
        if state_filtered and selected_state == last_state and graph_trigger == 'by_state':
            state_filtered = False
        elif state_filtered == False and graph_trigger != 'by_state':
            state_filtered = False
        else:
            program_df = program_df[program_df['state_code'] == selected_state]
            last_state = selected_state
            state_filtered = True
    else:
        state_filtered = False

    program_bar_graph = create_main_graph(program_df, x='program', y=value, title='Program Area', value=value)
    if selected_program is not None and program_filtered:
        graph_highlight(program_bar_graph, selected_program)

    state_map = create_map_graph(state_df, value)
    if selected_state is not None and state_filtered:
        graph_highlight(state_map, selected_state)

    app_state['last_program'] = last_program
    app_state['last_state'] = last_state
    app_state['program_filtered'] = program_filtered
    app_state['state_filtered'] = state_filtered
    app_state['inputs'] = inputs

    # All clickData attributes of the graph reset to None so we can 'unclick' a clicked value
    return program_bar_graph, state_map, None, None, app_state


if __name__ == '__main__':
    app.run()