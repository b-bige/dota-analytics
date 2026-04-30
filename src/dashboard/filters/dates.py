from .base import Filter
import dash_mantine_components as dmc
from src.dashboard.query_builder import QueryBuilder
from datetime import datetime, timedelta

class DatesFilter(Filter):
    filter_name = 'dates'
    component_id = 'date-filter'

    def parse_from_url(self, params):
        start_date = params.get('startDate', [None])[0]
        end_date = params.get('endDate', [None])[0]
        dates = [start_date, end_date]
        return dates
    
    def apply_to_query(self, qb: QueryBuilder, value, exclude):
        if not exclude and value and value[0]:
            start_date = datetime.fromisoformat(value[0])
            end_date = datetime.fromisoformat(value[1] if value[1] else value[0]) + timedelta(days=1)
            
            qb.where('md."startDateTimeHuman" > :start_date', {'start_date': start_date})
            qb.where('md."startDateTimeHuman" < :end_date', {'end_date': end_date})
        return qb

    def to_url_params(self, value):
        params = {}
        if value[0] != None:
            params['startDate'] = value[0]
            if value[1]:
                params['endDate'] = value[1]
        return params
    
    def get_data(self, **filters):
        return (self.get_date_boundary('MIN', **filters), self.get_date_boundary('MAX', **filters))

    def get_date_boundary(self, boundary, **kwargs) -> datetime: 
        qb = QueryBuilder()
        self.handle_filters(qb, **kwargs, exclude='dates')
        query, params = qb.build(
            select=f'{boundary}(md."startDateTimeHuman")'
        )
        date_boundary = self.db.select(query, params=params)[0][0]
        try:
            return date_boundary.strftime('%Y-%m-%d') 
        except:
            return None 
    
    def render(self, value, data):
        default_date = value[0] if value[0] else data[0]
        return dmc.DatePicker(
            id='date-filter',
            type='range',
            minDate=data[0],
            maxDate=data[1],
            value=value,
            defaultDate=default_date,
            mt='md',
            w='100%',
            px=10,
            style={'boxSizing': 'border-box'}
        )
    
    def get_outputs(self, triggered_component_id, **filters) -> list:
        # dates has 3 outputs: defaultDate, minDate, maxDate
        min_date, max_date = self.get_date_boundary('MIN', **filters), self.get_date_boundary('MAX', **filters)
        return [min_date, max_date, min_date]  # defaultDate, minDate, maxDate