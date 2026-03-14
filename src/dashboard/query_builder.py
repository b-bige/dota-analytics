from abc import ABC, abstractmethod

class QueryBuilder:
    def __init__(self, base_table='match_details md'):
        self.base_table = base_table
        self._joins = {}
        self._conditions = []
        self._having = []
        self._params = []
        self._having_params = []

    def copy(self):
        """Return a fresh copy with only the filter conditions/joins, not query-specific ones"""
        new_qb = QueryBuilder(self.base_table)
        new_qb._joins = self._joins.copy()
        new_qb._conditions = self._conditions.copy()
        new_qb._params = self._params.copy()
        new_qb._having = self._having.copy()
        new_qb._having_params = self._having_params.copy()
        # intentionally NOT copying _joins — those are query-specific
        return new_qb

    def join(self, alias, join_sql):
        """Add a join only if not already present"""
        if alias not in self._joins:
            self._joins[alias] = join_sql
        return self  # fluent chaining

    def where(self, condition, *params):
        self._conditions.append(condition)
        self._params.extend(params)
        return self
    
    def having(self, condition, *params):
        self._having.append(condition)
        self._having_params.extend(params)
        return self

    def build(self, select, group_by='', order_by='', extra_conditions='', extra_params=None):
        extra_params = extra_params or []
        joins = ' '.join(self._joins.values())

        where = 'WHERE 1=1'
        if self._conditions:
            where += ' AND ' + ' AND '.join(f'({c})' for c in self._conditions)
        if extra_conditions:
            where += f' AND ({extra_conditions})'  # wrap extra_conditions too

        having = ''
        if self._having:
            having = 'HAVING ' + ' AND '.join(f'({h})' for h in self._having)  # wrap having too

        query = f'''
            SELECT {select}
            FROM {self.base_table}
            {joins}
            {where}
            {group_by}
            {having}
            {order_by}
        '''
        return query, self._params + self._having_params + extra_params
    
    def is_filtered(self):
        """True if any filters have been applied"""
        return len(self._conditions) > 0