from abc import ABC, abstractmethod
from db_functions import DotaDB
from datetime import datetime, timedelta
from query_builder import QueryBuilder
import dash_mantine_components as dmc
from dash import html, no_update

class Filter(ABC):
    filter_name: str
    component_id: str
    db = DotaDB()

    @staticmethod
    def handle_filters(qb: QueryBuilder, exclude=None, **kwargs):
        for filter_name, value in kwargs.items():
            if filter_name in FILTER_MAP:
                FILTER_MAP[filter_name].apply_to_query(
                    qb, value, exclude=(filter_name == exclude)
                )
        return qb

    @abstractmethod
    def parse_from_url(self, params: dict):
        return params.get(self.filter_name, [None])[0] 
    
    @abstractmethod
    def apply_to_query(self, qb, value, exclude: bool):
        """Apply filter condition to QueryBuilder"""
        pass

    @abstractmethod
    def to_url_params(self, value) -> dict:
        return {self.filter_name: value} if value else {}

    @abstractmethod
    def get_data(self, **filters):
        """Fetch available options for this filter"""
        pass

    @abstractmethod
    def render(self, value, data, **kwargs):
        """Return the Mantine component for this filter"""
        pass

    def get_updated_data(self, triggered_component_id, **filters):
        """Return no_update if this filter triggered, otherwise fetch fresh data"""
        if triggered_component_id == self.component_id:
            return no_update
        return self.get_data(exclude=self.filter_name, **filters)

    def get_outputs(self, triggered_component_id, **filters) -> list:
        """Return list of output values for this filter — override for multi-output filters"""
        return [self.get_updated_data(triggered_component_id, **filters)]

class PatchFilter(Filter):
    filter_name = 'patch'
    component_id = 'patch-filter'

    def parse_from_url(self, params):
        return super().parse_from_url(params)
    
    def apply_to_query(self, qb, value, exclude):
        if value and not exclude:
            qb.join('p', 'LEFT JOIN patches p ON md."gameVersionId" = p.id')
            qb.where('p.name = %s', value)
        return qb

    def to_url_params(self, value):
        return super().to_url_params(value)
    
    def get_data(self, **filters):
        qb = QueryBuilder()
        qb.join('p', 'INNER JOIN patches p ON md."gameVersionId" = p.id')
        self.handle_filters(qb, **filters)
        query, params = qb.build(
            select='DISTINCT p.name',
            order_by='ORDER BY p.name DESC'
        )
        return [result[0] for result in self.db.query_select(query, params=params)]
    
    def render(self, value, data):
        return dmc.Select(
            id=self.component_id,
            label='Game Version',
            placeholder='Select Game Version',
            data=data,
            value=value,
            searchable=True
        )

class LeagueFilter(Filter):
    filter_name = 'league'
    component_id = 'league-filter'

    def parse_from_url(self, params):
        return super().parse_from_url(params)
    
    def apply_to_query(self, qb, value, exclude):
        if value and not exclude:
            qb.join('ld', 'LEFT JOIN league_details ld ON md."leagueId" = ld.id')
            qb.where('ld."displayName" = %s', value)
        return qb
    
    def to_url_params(self, value):
        return super().to_url_params(value)
    
    def get_data(self, **filters):
        qb = QueryBuilder()
        qb.join('ld', 'INNER JOIN league_details ld ON md."leagueId" = ld.id')
        self.handle_filters(qb, **filters)  # will skip 'ld' since already joined
        query, params = qb.build(
            select='DISTINCT ld."displayName"',
            extra_conditions='ld."displayName" NOT LIKE \'?%%\'',
            order_by='ORDER BY ld."displayName" ASC'
        )
        leagues = [result[0] for result in self.db.query_select(query, params=params)]
        return leagues
    
    def render(self, value, data):
        return dmc.Select(
            id='league-filter',
            label='League',
            placeholder='Select League',
            data=data,
            value=value,
            searchable=True
        )

class TeamsFilter(Filter):
    filter_name = 'teams'
    component_id = 'teams-filter'

    def parse_from_url(self, params):
        return params.get(self.filter_name, None)
    
    def apply_to_query(self, qb, value, exclude):
        if value:
            if value[0] and not exclude:
                qb.join('radiant', 'LEFT JOIN team_details radiant ON radiant.id = md."radiantTeamId"')
                qb.join('dire', 'LEFT JOIN team_details dire ON dire.id = md."direTeamId"')
                if len(value) == 2:
                    qb.where(
                        '(radiant.name = %s AND dire.name = %s) OR (radiant.name = %s AND dire.name = %s)',
                        value[0], value[1], value[1], value[0]
                    )
                else:
                    qb.where('(radiant.name = ANY(%s)) OR (dire.name = ANY(%s))', value, value)
        return qb

    def to_url_params(self, value):
        return super().to_url_params(value)
    
    def get_data(self, **filters):
        qb = QueryBuilder()
        qb.join('tdr', 'INNER JOIN team_details tdr ON tdr.id = md."radiantTeamId"')
        qb.join('tdd', 'INNER JOIN team_details tdd ON tdd.id = md."direTeamId"')
        qb.where('tdr."isPro" = \'t\' AND tdd."isPro" = \'t\'')
        self.handle_filters(qb, **filters)
        q1, params1 = qb.build(select='DISTINCT tdr.name')
        q2, params2 = qb.copy().build(select='DISTINCT tdd.name')

        query = f'''
            {q1}
            UNION
            {q2}
            ORDER BY name ASC
        '''
        return [r[0] for r in self.db.query_select(query, params=params1 + params2)]
    
    def render(self, value, data):
        teams_placeholder = 'Select 2 To See Head-to-Head' if len(data) > 0 else 'No Pro Teams Found'
        return dmc.MultiSelect(
            id='teams-filter',
            label='Pro Teams',
            placeholder=teams_placeholder,
            data=data,
            value=value,
            searchable=True
        )
    
    def get_outputs(self, triggered_component_id, **filters) -> list:
        data = self.get_updated_data(triggered_component_id, **filters)
        if data is no_update:
            placeholder = no_update
        else:
            placeholder = 'Select 2 To See Head-to-Head' if data else 'No Pro Teams Found'
        return [placeholder, data]
    
class DurationsFilter(Filter):
    filter_name = 'durations'
    component_id = 'durations-filter'
    def __init__(self):
        self.db_max_duration = self.get_db_max_duration()

    def get_db_max_duration(self):
        query = 'SELECT MAX("durationSeconds") / 60 FROM match_details'
        return self.db.query_select(query)[0][0]

    def parse_from_url(self, params):
        start_duration = params.get('startDuration', [0])[0]
        end_duration = params.get('endDuration', [self.db_max_duration])[0]
        durations = [start_duration, end_duration]
        durations = list(map(int, durations))
        return durations
    
    def apply_to_query(self, qb, value, exclude):
        if value and not exclude:
            start, end = value
            start = int(start)*60 if start else 0
            end = int(end)*60 if end else self.db_max_duration
            if start and start != 0:
                qb.where('md."durationSeconds" > %s', start)
            if end and end != self.db_max_duration*60:
                qb.where('md."durationSeconds" < %s', end)
        return qb
    
    def to_url_params(self, value):
        params = {}
        if value[0] != 0:
            params['startDuration'] = value[0]
        if value[1] and value[1] != self.db_max_duration:
            params['endDuration'] = value[1]
        return params
    
    def get_data(self, **filters):
        qb = QueryBuilder()
        self.handle_filters(qb, **filters, exclude='durations')
        query, params = qb.build(select='MAX("durationSeconds") / 60')
        return self.db.query_select(query, params=params)[0][0]

    def render(self, value, data):
        return html.Div([
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
        ])

class DatesFilter(Filter):
    filter_name = 'dates'
    component_id = 'date-filter'

    def parse_from_url(self, params):
        start_date = params.get('startDate', [None])[0]
        end_date = params.get('endDate', [None])[0]
        dates = [start_date, end_date]
        return dates
    
    def apply_to_query(self, qb, value, exclude):
        if not exclude:
            if value:
                if value[0]:
                    start_date = datetime.fromisoformat(value[0])
                    if value[0] and value[1]:
                        end_date = datetime.fromisoformat(value[1]) + timedelta(days=1)
                    else:
                        end_date = datetime.fromisoformat(value[0]) + timedelta(days=1)
                else:
                    start_date, end_date = (None, None)
            if start_date:
                qb.where('md."startDateTimeHuman" > %s', start_date)
            if end_date:
                qb.where('md."startDateTimeHuman" < %s', end_date)
        return qb

    def to_url_params(self, value):
        params = {}
        if value[0] != None:
            params['startDate'] = value[0]
            if value[1]:
                params['endDate'] = value[1]
        return params
    
    def get_data(self, **filters):
        return (self.get_date_boundary('MIN', **filters).strftime('%Y-%m-%d'), self.get_date_boundary('MAX', **filters).strftime('%Y-%m-%d'))

    def get_date_boundary(self, boundary, **kwargs) -> datetime: 
        qb = QueryBuilder()
        self.handle_filters(qb, **kwargs, exclude='dates')
        query, params = qb.build(
            select=f'{boundary}(md."startDateTimeHuman")'
        )
        return self.db.query_select(query, params=params)[0][0]
    
    def render(self, value, data):
        default_date = value[0] if value[0] else data[0]
        return dmc.DatePicker(
            id='date-filter',
            type='range',
            minDate=data[0],
            maxDate=data[1],
            value=value,
            defaultDate=default_date,
            mt='md'
        )
    
    def get_outputs(self, triggered_component_id, **filters) -> list:
        # dates has 3 outputs: defaultDate, minDate, maxDate
        min_date, max_date = self.get_date_boundary('MIN', **filters).strftime('%Y-%m-%d'), self.get_date_boundary('MAX', **filters).strftime('%Y-%m-%d')
        return [min_date, max_date, min_date]  # defaultDate, minDate, maxDate

FILTER_IDS = {
    'patch':  'patch-filter',
    'league': 'league-filter',
    'teams':  'teams-filter',
    'durations': 'durations-filter',
    'dates':  'date-filter', #This filter needs to be the last because it has unique fields
}

FILTERS: list[Filter] = [
    PatchFilter(),
    LeagueFilter(),
    TeamsFilter(),
    DurationsFilter(),
    DatesFilter(),
]

FILTER_MAP = {f.filter_name: f for f in FILTERS}