import ckan.plugins as p
import ckan.model as model

def group_tree(type_='organization'):
    return p.toolkit.get_action('group_tree')({}, {'type': type_})

def group_tree_section(id_, type_='organization'):
    return p.toolkit.get_action('group_tree_section')(
        {}, {'id': id_, 'type': type_})

def group_tree_parents(id_, type_='organization'):
     tree_node =  p.toolkit.get_action('organization_show')({},{'id':id_})
     if (tree_node['groups']):
         parent_id = tree_node['groups'][0]['name']
         parent_node =  p.toolkit.get_action('organization_show')({},{'id':parent_id})
         parent_nodename =  {'displayname': parent_node.get('shortname', parent_node.get('title')),
                             'id': parent_id}
         return group_tree_parents(parent_id) + [parent_nodename]
     else:
         return []

def get_allowable_parent_groups(group_id):
    if group_id:
        group = model.Group.get(group_id)
        allowable_parent_groups = \
            group.groups_allowed_to_be_its_parent(type='organization')
    else:
        allowable_parent_groups = model.Group.all(
            group_type='organization')
    return allowable_parent_groups
