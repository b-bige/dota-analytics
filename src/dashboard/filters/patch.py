from .base import Filter
import dash_mantine_components as dmc
from src.dashboard.query_builder import QueryBuilder

class PatchFilter(Filter):
    filter_name = 'patch'
    component_id = 'patch-filter'

    def parse_from_url(self, params):
        return super().parse_from_url(params)
    
    def apply_to_query(self, qb: QueryBuilder, value, exclude):
        if value: 
            if value[0] and not exclude:
                qb.join('p', 'LEFT JOIN patches p ON md."gameVersionId" = p.id')
                qb.where('p.name = ANY(:value)', {'value': value})
        return qb

    def to_url_params(self, value):
        return super().to_url_params(value)
    
    def get_data(self, **filters):
        qb = QueryBuilder()
        qb.join('p', 'INNER JOIN patches p ON md."gameVersionId" = p.id')
        if 'exclude' in filters.keys():
            self.handle_filters(qb, **filters)
        else:
            self.handle_filters(qb, **filters, exclude='patch')
        query, params = qb.build(
            select='DISTINCT p.name',
            order_by='ORDER BY p.name DESC'
        )
        return [result[0] for result in self.db.select(query, params=params)]
    
    def render(self, value, data):
        return dmc.MultiSelect(
            id=self.component_id,
            label='Game Version',
            placeholder='Select Game Version',
            data=data,
            value=value,
            searchable=True
        )