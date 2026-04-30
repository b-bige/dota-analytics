from .base import Filter
import dash_mantine_components as dmc
from dash import html
from src.dashboard.query_builder import QueryBuilder

class DurationsFilter(Filter):
    filter_name = 'durations'
    component_id = 'durations-filter'
    def __init__(self):
        self.db_max_duration = self.get_db_max_duration()

    def get_db_max_duration(self) -> int:
        """Fetches the longest match time in minutes"""
        query = 'SELECT MAX("durationSeconds") / 60 FROM match_details'
        return self.db.select(query)[0][0]

    def parse_from_url(self, params):
        start_duration = params.get('startDuration', [0])[0]
        end_duration = params.get('endDuration', [self.db_max_duration])[0]
        durations = [start_duration, end_duration]
        durations = list(map(int, durations))
        return durations
    
    def apply_to_query(self, qb: QueryBuilder, value, exclude):
        if value and not exclude:
            start, end = value
            start = int(start)*60 if start else 0
            end = int(end)*60 if end else self.db_max_duration
            if start and start != 0:
                qb.where('md."durationSeconds" > :start_time', {'start_time': start})
            if end and end != self.db_max_duration*60:
                qb.where('md."durationSeconds" < :end_time', {'end_time': end})
        return qb
    
    def to_url_params(self, value):
        params = {}
        if value[0] != 0:
            params['startDuration'] = value[0]
        if value[1] and value[1] != self.db_max_duration:
            params['endDuration'] = value[1]
        return params
    
    def get_data(self, **filters):
        return None

    def render(self, value, data):
        return html.Div(
            children=[
                dmc.Text('Duration', size='sm', fw=500, mt=5),
                html.Div(
                    style={
                        'justifyContent': 'center',
                        'display': 'flex',
                        'width': '100%',
                        'paddingLeft': '10px',
                        'paddingRight': '10px'
                    },
                    children=dmc.RangeSlider(
                        id='durations-filter',
                        showLabelOnHover=True,
                        step=1,
                        marks=[
                            {"value": 0,   "label": "0"},
                            {'value': self.db_max_duration, 'label': f'{self.db_max_duration}m'}
                        ],
                        min=0,
                        max=self.db_max_duration,
                        value=value,
                        mt='md',
                        mb='xl',
                        w='100%'
                    ),
                )
            ]
        )