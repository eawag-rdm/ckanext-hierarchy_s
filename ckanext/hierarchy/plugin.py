import ckan.plugins as p
from ckanext.hierarchy.logic import action
from ckanext.hierarchy import helpers
from ckan.lib.plugins import DefaultOrganizationForm
import ckan.plugins.toolkit as tk
from lucparser import LucParser
import re
import logging
import pdb

log = logging.getLogger(__name__)

# This plugin is designed to work only these versions of CKAN
p.toolkit.check_ckan_version(min_version='2.0')


class HierarchyDisplay(p.SingletonPlugin):

    p.implements(p.IConfigurer, inherit=True)
    p.implements(p.IActions, inherit=True)
    p.implements(p.ITemplateHelpers, inherit=True)
    p.implements(p.IPackageController, inherit=True)

    # IConfigurer
    def update_config(self, config):
        p.toolkit.add_template_directory(config, 'templates')
        p.toolkit.add_template_directory(config, 'public')
        p.toolkit.add_resource('public/scripts/vendor/jstree', 'jstree')

    # IActions
    def get_actions(self):
        return {'group_tree': action.group_tree,
                'group_tree_section': action.group_tree_section,
                'group_tree_children':action.group_tree_children
                }

    # ITemplateHelpers
    def get_helpers(self):
        return {'group_tree': helpers.group_tree,
                'group_tree_section': helpers.group_tree_section,
                'group_tree_crumbs': helpers.group_tree_crumbs,
                'get_allowable_parent_groups': helpers.get_allowable_parent_groups,
                'render_tree': helpers.render_tree
                }

    # IPackageController
    # Modify the search query to include the datasets from
    # the children organizations in the result list
    # HvW: Do this always
    def before_search(self, search_params):
        ''' If include children selected the query string is modified '''

        def _get_organizations_from_subquery(subquery):
            patall = '"?([\w-]+)"?'
            patwrong = 'AND|OR|NOT'
            patnot = 'NOT\s+("?([\w-]+)"?)'
            parentorgs = set(re.findall(patall, subquery))
            parentwrong = set(re.findall(patwrong, subquery))
            parentnot = set(re.findall(patnot, subquery))
            parentorgs = list(parentorgs - parentwrong - parentnot)
            return parentorgs
            
        # q_list = _tokenize_search('q')
        # search_params['q'] = _assemble_query(q_list)
        # fq_list = _tokenize_search('fq')
        # search_params['fq'] = _assemble_query(fq_list)
        # orgas = tk.get_action('group_tree_section')({}, {'id': id_,
        #                                                  'type': type_,
        #                                                    'include_parents': include_parents})
        print('\n\n-------------------------- DEBUG THE FUCK ------------------- ')
        print('------------------------------ CONTEXT ---------------------------')
        print(tk.c)
        print('----------------------------SEARCH_PARAMS: -----------------------')
        print(search_params)
        lp = LucParser()
        #childorgas = tk.get_action('group_tree_children')({}, data_dict=
        for qtyp in ['fq', 'q']:
            query = search_params.get(qtyp, None)
            if query:
                queryterms = lp.deparse(query)
                for i, q in enumerate(queryterms):
                    if not isinstance(q, dict):
                        continue
                    fieldname = q.get('field')
                    if fieldname not in ['owner_org', 'organization']:
                        continue
                    parentgroups = _get_organizations_from_subquery(q.get('term'))
                    print('parents {}: {}'.format(fieldname, parentgroups))
                    children = [tk.get_action('group_tree_children')({}, data_dict={'id': p, 'type': 'organization'}) for p in parentgroups]
                    print('\nchildren: {}'.format(children))
                    childlist = [c[{'owner_org': 'id', 'organization': 'name'}[fieldname]] for child in children for c in child]
                    print('\nchildlist: {}'.format(childlist))
                    if childlist:
                        childsearch = ' OR ' + ' OR '.join(childlist)
                        print('\nchildsearch: {}'.format(childsearch))
                        search_params[qtyp] = lp.add_to_query(search_params[qtyp], childsearch, fieldname=fieldname)

        return search_params


class HierarchyForm(p.SingletonPlugin, DefaultOrganizationForm):

    p.implements(p.IGroupForm, inherit=True)

    # IGroupForm

    def group_types(self):
        return ('organization',)

    def group_controller(self):
        return 'organization'

    def setup_template_variables(self, context, data_dict):
        from pylons import tmpl_context as c
        model = context['model']
        group_id = data_dict.get('id')
        c.allowable_parent_groups = helpers.get_allowable_parent_groups(group_id)
