from ckan.plugins import toolkit as tk
import ckan.model as model

def group_tree(type_='organization'):
    return tk.get_action('group_tree')({}, {'type': type_})

def group_tree_section(id_, type_='organization'):
    return tk.get_action('group_tree_section')(
        {}, {'id': id_, 'type': type_})

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

