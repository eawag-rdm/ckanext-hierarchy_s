from ckan.plugins import toolkit as tk
import ckan.model as model

def group_tree(type_='organization'):
    return tk.get_action('group_tree')({}, {'type': type_})

def group_tree_section(id_, type_='organization', include_parents=True):
    return tk.get_action('group_tree_section')(
        {}, {'id': id_, 'type': type_, 'include_parents': include_parents})

def group_tree_crumbs(id_):
    ''' Returns list of dicts with
      + either shortname (if available) or title (alternatively) and
      + id and
      + url
    for <id_> and all parents.

    '''
    tree_node =  tk.get_action('organization_show')({},{'id':id_})
    crumbs = [{'crumbname': tree_node.get('shortname') or tree_node.get('title'),
               'id': id_,
               'url': tk.url_for(controller='organization',
                                 action='read', id=id_)}]
    if (tree_node['groups']):
        id_parent = tree_node['groups'][0]['name']
        return group_tree_crumbs(id_parent) + crumbs
    else:
        return(crumbs)

def get_allowable_parent_groups(group_id):
    if group_id:
        group = model.Group.get(group_id)
        allowable_parent_groups = \
            group.groups_allowed_to_be_its_parent(type='organization')
    else:
        allowable_parent_groups = model.Group.all(
            group_type='organization')
    return allowable_parent_groups

# Helper function from
# https://github.com/datagovuk/ckanext-dgu/blob/5fb78b354517c2198245bdc9c98fb5d6c82c6bcc/ckanext/dgu/lib/helpers.py
# for speedier rendering of organization-tree

def render_tree():
    '''Returns HTML for a hierarchy of all publishers'''
    context = {'model': model, 'session': model.Session}
    top_nodes = tk.get_action('group_tree')(context=context,
            data_dict={'type': 'organization'})
    return _render_tree(top_nodes)

def _render_tree(top_nodes):
    '''Renders a tree of nodes. 10x faster than Jinja/organization_tree.html
    Note: avoids the slow url_for routine.
    '''
    html = '<ul>'
    for node in top_nodes:
        html += _render_tree_node(node)
    return html + '</ul>'

def _render_tree_node(node):
    html = '<a href="/organization/{}">{}</a>'.format(node['name'], node['title'])
    if node['highlighted']:
        html = '<strong>{}</strong>'.format(html)
    if node['children']:
        html += '<ul>'
        for child in node['children']:
            html += _render_tree_node(child)
        html += '</ul>'
    html = '<li id="node_{}">{}</li>'.format(node['name'], html)
    return html
