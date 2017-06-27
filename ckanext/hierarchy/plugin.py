import ckan.plugins as p
from ckanext.hierarchy.logic import action
from ckanext.hierarchy import helpers
from ckan.lib.plugins import DefaultOrganizationForm
import ckan.plugins.toolkit as tk
from lucparser import LucParser
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
        def _tokenize_search(queryfield):
            def repspace(st):
                # deal with escaped brackets
                # issue if st tarts with ( ? 
                pat = re.compile(r'(\([^)]*\))+')
                brackets = re.finditer(pat, st)
                splitted = re.split(pat, st)
                repstrings = []
                for b in brackets:
                    repstrings.append(re.sub(r' +', '__SPACE__',b.group()))
                for k, i in enumerate(range(1,len(splitted),2)):
                    splitted[i] = repstrings[k] 
                return ''.join(splitted)

            def splitspaces(st):
                st = re.sub(": +", ":", st)
                ## split querystring at spaces if space doesn't occur in quotes
                ## http://stackoverflow.com/a/2787064
                # deal with escaped quotqtion marks
                # implement this: https://stackoverflow.com/a/2787979/6930916
                pat = re.compile(r'''((?:[^ "']|"[^"]*"|'[^']*')+)''')
                splitspaces = pat.split(st)[1::2]
                splitspaces = [el.replace('__SPACE__',' ') for el in splitspaces]
                return splitspaces

            splitquery = splitspaces(repspace(search_params.get(queryfield, '')))
            querylist = [e.split(':', 1) for e in splitquery]
            return querylist
        
        def _assemble_query(q_list):
            print q_list
            q_string = ' '.join([':'.join(el) for el in q_list])
            return q_string
            
        # q_list = _tokenize_search('q')
        # search_params['q'] = _assemble_query(q_list)
        # fq_list = _tokenize_search('fq')
        # search_params['fq'] = _assemble_query(fq_list)
        # orgas = tk.get_action('group_tree_section')({}, {'id': id_,
        #                                                  'type': type_,
        #                                                    'include_parents': include_parents})
        print('\n\n-------------------------- DEBUG THE FUCK ------------------- ')
        lp = LucParser()
        for qtyp in ['fq', 'q']:
            query = search_params.get(qtyp, None)
            if query:
                queryterms = lp.deparse(query)
                for i, q in enumerate(queryterms):
                    if q.get('field') == 'owner_org':
                        queryterms[i]['term'] = '('+ q.get('term') + ' OR ({}))'.format('3595c65e-25ec-4bde-87e7-340085a8feae')
                search_params[qtyp] = lp.assemble(queryterms)

        print('-------------------------- DEPARSED ------------------------')
        print(queryterms)
        print('--------------------------------------------------')
        print('------------------------------ CONTEXT ---------------------------')
        print(tk.c)
        print('----------------------------SEARCH_PARAMS: -----------------------')
        print(search_params)
        gd = tk.c.group_dict or None
        if gd:
            gd.update({'include_parents': False})
            res = tk.get_action('group_tree_section')({}, data_dict=gd)
            print('--------------------------TYPE------------------------------------')
            print(res)
            print(' -------------------------- END ------------------- ')
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
