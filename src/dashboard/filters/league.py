from .base import Filter
import dash_mantine_components as dmc
from src.dashboard.query_builder import QueryBuilder

class LeagueFilter(Filter):
    filter_name = 'league'
    component_id = 'league-filter'

    def parse_from_url(self, params):
        return super().parse_from_url(params)
    
    def apply_to_query(self, qb: QueryBuilder, value, exclude):
        if value:
            if value[0] and not exclude:
                qb.join('ld', 'LEFT JOIN league_details ld ON md."leagueId" = ld.id')
                qb.where('ld."displayName" = ANY(:value)', {'value': value})
        return qb
    
    def to_url_params(self, value):
        return super().to_url_params(value)
    
    def get_data(self, **filters):
        qb = QueryBuilder()
        qb.join('ld', 'INNER JOIN league_details ld ON md."leagueId" = ld.id')
        if 'exclude' in filters.keys():
            self.handle_filters(qb, **filters)
        else:
            self.handle_filters(qb, **filters, exclude='league')  # will skip 'ld' since already joined
        query, params = qb.build(
            select='DISTINCT ld."displayName"',
            extra_conditions='ld."displayName" NOT LIKE \'?%%\'',
            order_by='ORDER BY ld."displayName" ASC'
        )
        leagues = [result[0] for result in self.db.select(query, params=params)]
        return leagues
    
    def render(self, value, data):
        return dmc.MultiSelect(
            id='league-filter',
            label='League',
            placeholder='Select League',
            data=data,
            value=value,
            searchable=True
        )