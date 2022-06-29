import base64
import json
import pathlib
import datetime
from typing import Dict, List
import random
import io

import dash
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from dash import ALL, dcc, html
from dash.dependencies import Input, Output, State
from pcgsepy.config import BIN_POP_SIZE, CS_MAX_AGE, N_GENS_ALLOWED
from pcgsepy.evo.fitness import (Fitness, box_filling_fitness,
                                 func_blocks_fitness, mame_fitness,
                                 mami_fitness)
from pcgsepy.evo.genops import expander
from pcgsepy.hullbuilder import HullBuilder
from pcgsepy.lsystem.solution import CandidateSolution
from pcgsepy.mapelites.behaviors import (BehaviorCharacterization, avg_ma,
                                         mame, mami, symmetry)
from pcgsepy.mapelites.emitters import *
from pcgsepy.mapelites.emitters import (ContextualBanditEmitter,
                                        HumanPrefMatrixEmitter, RandomEmitter)
from pcgsepy.mapelites.map import get_structure
from pcgsepy.setup_utils import get_default_lsystem

used_ll_blocks = [
    'MyObjectBuilder_CubeBlock_LargeBlockArmorCornerInv',
    'MyObjectBuilder_CubeBlock_LargeBlockArmorCorner',
    'MyObjectBuilder_CubeBlock_LargeBlockArmorSlope',
    'MyObjectBuilder_CubeBlock_LargeBlockArmorBlock',
    'MyObjectBuilder_Gyro_LargeBlockGyro',
    'MyObjectBuilder_Reactor_LargeBlockSmallGenerator',
    'MyObjectBuilder_CargoContainer_LargeBlockSmallContainer',
    'MyObjectBuilder_Cockpit_OpenCockpitLarge',
    'MyObjectBuilder_Thrust_LargeBlockSmallThrust',
    'MyObjectBuilder_InteriorLight_SmallLight',
    'MyObjectBuilder_CubeBlock_Window1x1Slope',
    'MyObjectBuilder_CubeBlock_Window1x1Flat',
    'MyObjectBuilder_InteriorLight_LargeBlockLight_1corner'
]

lsystem = get_default_lsystem(used_ll_blocks=used_ll_blocks)

expander.initialize(rules=lsystem.hl_solver.parser.rules)

hull_builder = HullBuilder(erosion_type='bin',
                           apply_erosion=True,
                           apply_smoothing=False)

feasible_fitnesses = [
    #     Fitness(name='BoundingBox',
    #             f=bounding_box_fitness,
    #             bounds=(0, 1)),
    Fitness(name='BoxFilling',
            f=box_filling_fitness,
            bounds=(0, 1)),
    Fitness(name='FuncionalBlocks',
            f=func_blocks_fitness,
            bounds=(0, 1)),
    Fitness(name='MajorMediumProportions',
            f=mame_fitness,
            bounds=(0, 1)),
    Fitness(name='MajorMinimumProportions',
            f=mami_fitness,
            bounds=(0, 1))
]

behavior_descriptors = [
    BehaviorCharacterization(name='Major axis / Medium axis',
                             func=mame,
                             bounds=(0, 10)),
    BehaviorCharacterization(name='Major axis / Smallest axis',
                             func=mami,
                             bounds=(0, 20)),
    BehaviorCharacterization(name='Symmetry',
                             func=symmetry,
                             bounds=(0, 1))
]

behavior_descriptors_names = [x.name for x in behavior_descriptors]

emitters = ['Random', 'Preference Matrix', 'Contextual Bandit']

block_to_colour = {
    # colours from https://developer.mozilla.org/en-US/docs/Web/CSS/color_value
    'LargeBlockArmorCorner': '#778899',
    'LargeBlockArmorSlope': '#778899',
    'LargeBlockArmorCornerInv': '#778899',
    'LargeBlockArmorBlock': '#778899',
    'LargeBlockGyro': '#2f4f4f',
    'LargeBlockSmallGenerator': '#ffa07a',
    'LargeBlockSmallContainer': '#008b8b',
    'OpenCockpitLarge': '#32cd32',
    'LargeBlockSmallThrust': '#ff8c00',
    'SmallLight': '#fffaf0',
    'Window1x1Slope': '#fffff0',
    'Window1x1Flat': '#fffff0',
    'LargeBlockLight_1corner': '#fffaf0'
}

def _get_colour_mapping(block_types: List[str]) -> Dict[str, str]:
    colour_map = {}
    for block_type in block_types:
        c = block_to_colour.get(block_type, '#ff0000')
        if block_type not in colour_map.keys():
            colour_map[block_type] = c
    return colour_map


app = dash.Dash(__name__,
                title='Spasceships comparator',
                external_stylesheets=[
                    'https://codepen.io/chriddyp/pen/bWLwgP.css'],
                update_title=None)

def set_app_layout():
    description_str, help_str = '', ''
    
    curr_dir = pathlib.Path(__file__).parent.resolve()
    
    with open(curr_dir.joinpath('assets/description.md'), 'r') as f:
        description_str = f.read()
    with open(curr_dir.joinpath('assets/help.md'), 'r') as f:
        help_str = f.read()
    
    app.layout = html.Div(children=[
        # HEADER
        html.Div(children=[
            html.H1(children='🚀Space Engineers🚀 Spaceships comparator',
                    className='title'),
            dcc.Markdown(children=description_str,
                         className='page-description'),
        ],
            className='header'),
        html.Br(),
        
        dcc.Upload(
            id='upload-data',
            children=html.Div([
                'Drag and Drop or ',
                html.A('Select Files')
            ]),
            style={
                'width': '60%',
                'height': '60px',
                'lineHeight': '60px',
                'borderWidth': '1px',
                'borderStyle': 'dashed',
                'borderRadius': '5px',
                'textAlign': 'center',
                'margin': '10px'
            },
            # Allow multiple files to be uploaded
            multiple=True
        ),
        
        # BODY
        html.Div(children=[
            
            # content plots
            html.Div(children=[
                
                # spaceship 1
                html.Div(children=[
                    # title
                    html.Div(children=[
                        html.H1(children='Spaceship from Experiment 1',
                                style={'text-align': 'center'})
                        ]),
                    html.Br(),
                    # spaceship content display + properties
                    # CONTENT PLOT
                        html.Div(children=[
                            dcc.Graph(id="spaceship-1-content",
                                    figure=go.Figure(data=[])),
                        ],
                            className='content-div',
                            style={'width': '100%'}),
                        html.Div(children=[
                            html.H6('Content properties',
                                    className='section-title'),
                            html.Div(children=[],
                                    id='spaceship-1-properties'),
                            ],
                                className='properties-div',
                                style={'width': '60%', 'textAlign': 'center'}),
                        html.Div(children=[
                            dcc.Slider(1, 3, 1,
                                    value=1,
                                    id='spaceship-1-slider',
                                    marks=None,
                                    tooltip={"placement": "bottom",
                                            "always_visible": True}),
                            ],
                                style={'width': '60%', 'margin': '0 auto'})
                    ],
                        style={'width': '30%'}),
                
                # spaceship 2
                html.Div(children=[
                    # title
                    html.Div(children=[
                        html.H1(children='Spaceship from Experiment 2',
                                style={'text-align': 'center'})
                        ]),
                    html.Br(),
                    # spaceship content display + properties
                    # CONTENT PLOT
                        html.Div(children=[
                            dcc.Graph(id="spaceship-2-content",
                                    figure=go.Figure(data=[])),
                        ],
                            className='content-div',
                            style={'width': '100%'}),
                        html.Div(children=[
                            html.H6('Content properties',
                                    className='section-title'),
                            html.Div(children=[],
                                    id='spaceship-2-properties'),
                            ],
                                className='properties-div',
                                style={'width': '60%', 'textAlign': 'center'}),
                        html.Div(children=[
                            dcc.Slider(1, 3, 1,
                                    value=1,
                                    id='spaceship-2-slider',
                                    marks=None,
                                    tooltip={"placement": "bottom",
                                            "always_visible": True}),
                            ],
                                style={'width': '60%', 'margin': '0 auto'}),
                    ],
                        style={'width': '30%'}),
                
                # spaceship 3
                html.Div(children=[
                    # title
                    html.Div(children=[
                        html.H1(children='Spaceship from Experiment 3',
                                style={'text-align': 'center'})
                        ]),
                    html.Br(),
                    # spaceship content display + properties
                    # CONTENT PLOT
                        html.Div(children=[
                            dcc.Graph(id="spaceship-3-content",
                                    figure=go.Figure(data=[])),
                        ],
                            className='content-div',
                            style={'width': '100%'}),
                        html.Div(children=[
                            html.H6('Content properties',
                                    className='section-title'),
                            html.Div(children=[],
                                    id='spaceship-3-properties'),
                            ],
                                className='properties-div',
                                style={'width': '60%', 'textAlign': 'center'}),
                        html.Div(children=[
                            dcc.Slider(1, 3, 1,
                                    value=1,
                                    id='spaceship-3-slider',
                                    marks=None,
                                    tooltip={"placement": "bottom",
                                            "always_visible": True}),
                            ],
                                style={'width': '60%', 'margin': '0 auto'}),
                    ],
                        style={'width': '30%'}),
        ],
                     style={'width': '100%', 'display': 'flex', 'flex-direction': 'row', 'justify-content': 'center'}),
        ]), 
        html.Br(),
        html.Div(id='eoe',
                 children=[]),
        html.Br(),
        html.Div(children=[
                    html.Button(children='Save',
                                id='save-btn',
                                n_clicks=0,
                                className='button',
                                disabled=False),
                    dcc.Download(id='save-data')
                ],
                    className='button-div'),     
        html.Br(),
        # FOOTER
        html.Div(children=[
            html.H6(children='Help',
                    className='section-title'),
            dcc.Markdown(help_str,
                         className='page-description')
        ],
            className='footer'),
        dcc.Store(id='rngseed', data=json.dumps(0))
        ])


def parse_contents(filename,
                   contents):
    _, rngseed, exp_n = filename.split('_')
    rngseed = int(rngseed)
    exp_n = int(exp_n.replace('exp', '').replace('.txt', ''))

    _, content_string = contents.split(',')
    cs_string = base64.b64decode(content_string).decode(encoding='utf-8')

    return rngseed, exp_n, cs_string    


def get_content_plot(spaceship: CandidateSolution) -> go.Figure:
    ll_spaceship = lsystem.hl_to_ll(spaceship)
    spaceship.ll_string = ll_spaceship.string
    spaceship.set_content(get_structure(string=spaceship.ll_string,
                                                extra_args={
                                                    'alphabet': lsystem.ll_solver.atoms_alphabet
                                                    }))
    # create content plot...
    hull_builder.add_external_hull(structure=spaceship.content)
    content = spaceship.content.as_grid_array()
    arr = np.nonzero(content)
    x, y, z = arr
    cs = [content[i, j, k] for i, j, k in zip(x, y, z)]
    ss = [spaceship.content._clean_label(spaceship.content.ks[v - 1]) for v in cs]
    fig = px.scatter_3d(x=x,
                        y=y,
                        z=z,
                        color=ss,
                        color_discrete_map=_get_colour_mapping(ss),
                        labels={
                            'x': 'x',
                            'y': 'y',
                            'z': 'z',
                            'color': 'Block type'
                        },
                        title=f'{spaceship.string}')
    fig.update_layout(scene=dict(aspectmode='data'),
                      paper_bgcolor='rgba(0,0,0,0)',
                      plot_bgcolor='rgba(0,0,0,0)')
    return fig


def get_spaceship_properties(spaceship: CandidateSolution) -> Dict[str, Any]:
    spaceship_properties = [
        dcc.Markdown(children=f'**Size**: {spaceship.content.as_grid_array().shape}',
                     className='properties-text'),
        dcc.Markdown(children=f'**Number of blocks**: {spaceship.n_blocks}',
                     className='properties-text')        
    ]
    for bc in behavior_descriptors:
        spaceship_properties.append(dcc.Markdown(children=f'**{bc.name}**: {np.round(bc(spaceship), 4)}',
                                                 className='properties-text'))
    return spaceship_properties


@app.callback(
    Output("save-data", "data"),
    Output('eoe', "children"),
    Input("save-btn", "n_clicks"),
    State('spaceship-1-slider', 'value'),
    State('spaceship-2-slider', 'value'),
    State('spaceship-3-slider', 'value'),
    State('rngseed', 'data'),
    prevent_initial_call=True,
)
def download_mapelites(n_clicks,
                       slider1_value, slider2_value, slider3_value, rng_seed):
    rng_seed = json.loads(rng_seed)
    
    random.seed(rng_seed)
    my_emitterslist = emitters.copy()
    random.shuffle(my_emitterslist)
    
    res = {emitter:v for emitter, v in zip(my_emitterslist, [slider1_value, slider2_value, slider3_value])}
    
    eoe = dcc.Markdown('''
                       ##### This concludes the experiment
                       
                       Please visit the [Google Form](/) page to compile the questionnaire.
                       ''')
    
    return dict(content=str(res), filename=f'{str(rng_seed).zfill(3)}_res.json'), eoe


@app.callback(
              Output('spaceship-1-content', 'figure'),
              Output('spaceship-1-properties', 'children'),
              
              Output('spaceship-2-content', 'figure'),
              Output('spaceship-2-properties', 'children'),
              
              Output('spaceship-3-content', 'figure'),
              Output('spaceship-3-properties', 'children'),
              
              Output('rngseed', 'data'),
              
              Input('upload-data', 'contents'),
              
              State('upload-data', 'filename'),
              
              State('spaceship-1-content', 'figure'),
              State('spaceship-1-properties', 'children'),
              
              State('spaceship-2-content', 'figure'),
              State('spaceship-2-properties', 'children'),
              
              State('spaceship-3-content', 'figure'),
              State('spaceship-3-properties', 'children'),
              
              State('rngseed', 'data')
)
def general_callback(list_of_contents,
                     list_of_names, spaceship_1_plot, spaceship_1_properties, spaceship_2_plot, spaceship_2_properties, spaceship_3_plot, spaceship_3_properties, rng_seed):
    rng_seed = json.loads(rng_seed)
    
    ctx = dash.callback_context

    if not ctx.triggered:
        event_trig = None
    else:
        event_trig = ctx.triggered[0]['prop_id'].split('.')[0]

    if event_trig == 'upload-data':
        children = [parse_contents(n, c) for c, n in zip(list_of_contents, list_of_names)]
        for child in children:
            rng_seed, exp_n, cs_string = child
            cs = CandidateSolution(string=cs_string)
            if exp_n == 1:
                spaceship_1_plot = get_content_plot(spaceship=cs)
                spaceship_1_properties = get_spaceship_properties(spaceship=cs)
            elif exp_n == 2:
                spaceship_2_plot = get_content_plot(spaceship=cs)
                spaceship_2_properties = get_spaceship_properties(spaceship=cs)
            elif exp_n == 3:
                spaceship_3_plot = get_content_plot(spaceship=cs)
                spaceship_3_properties = get_spaceship_properties(spaceship=cs)
    
    return spaceship_1_plot, spaceship_1_properties, spaceship_2_plot, spaceship_2_properties, spaceship_3_plot, spaceship_3_properties, json.dumps(rng_seed)
