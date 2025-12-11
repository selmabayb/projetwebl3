from django import template

register = template.Library()

@register.filter
def filter_by_status(cases, statuses):
    """Filtre une liste de cas (Case objects) par une liste de statuts."""
    if not isinstance(statuses, list):
        statuses = [statuses]
    
    return [case for case in cases if case.status in statuses]

@register.filter
def length(value):
    """Retourne la longueur d'une liste ou d'un queryset."""
    return len(value)