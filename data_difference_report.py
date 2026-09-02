# IMPORT DEPENDENCIES
import pandas as pd
from itables import to_html_datatable
import base64

# these are custom functions from a script in this directory
import custom_diff_functions as diff

# this is a file that includes specifies what should be included in the report
# it's in .gitignore, but the README includes a template to create one
with open('report_specifications.py') as f:
    exec(f.read())

# optionally, create a Mermaid flowchart of the version tree
if create_diagram == True:
    import mermaidx
    diagram = mermaidx.render(version_tree_mmd)
    diagram.save(version_tree_image)

# turn the image of a version tree into a base64 string
with open(version_tree_image, 'rb') as f:
    version_tree_bytes = base64.b64encode(f.read())
    version_tree_string = version_tree_bytes.decode("utf-8")

# FUNCTION TO MAKE TAB SETS
_tab_counter = 0

def make_tabset(tabs):
    """
    tabs: dict of {label: html_content_string}
    Returns an HTML string with a row of buttons and matching content panes.
    Each tabset gets a unique id so nested/sibling tabsets don't collide.
    """
    global _tab_counter
    _tab_counter += 1
    group_id = f'tabset-{_tab_counter}'

    buttons = []
    panes = []
    for idx, (label, content) in enumerate(tabs.items()):
        pane_id = f'{group_id}-pane-{idx}'
        active = ' active' if idx == 0 else ''
        buttons.append(
            f'<button class="tab-btn{active}" onclick="showTab(\'{group_id}\', \'{pane_id}\', this)">{label}</button>'
        )
        panes.append(
            f'<div class="tab-pane{active}" id="{pane_id}" data-group="{group_id}">{content}</div>'
        )

    return f'''
<div class="tabset" data-group="{group_id}">
  <div class="tab-buttons">{''.join(buttons)}</div>
  <div class="tab-content">{''.join(panes)}</div>
</div>
'''

# CSS FOR HTML OUTPUT
TAB_STYLE_SCRIPT = '''
<style>
  .tabset { margin: 1em 0; border: 1px solid #ddd; border-radius: 6px; }
  .tab-buttons { display: flex; flex-wrap: wrap; border-bottom: 1px solid #ddd; background: #f7f7f7; }
  .tab-btn {
    padding: 8px 16px; border: none; background: none; cursor: pointer;
    font-size: 14px; border-bottom: 3px solid transparent;
  }
  .tab-btn:hover { background: #eee; }
  .tab-btn.active { border-bottom: 3px solid #2c7be5; font-weight: 600; }
  .tab-pane { display: none; padding: 12px; }
  .tab-pane.active { display: block; }
</style>
<script>
  function showTab(groupId, paneId, btn) {
    // toggle buttons in this group
    btn.parentNode.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    // toggle panes in this group (only direct children of this group's content)
    document.querySelectorAll('.tab-pane[data-group="' + groupId + '"]').forEach(p => p.classList.remove('active'));
    document.getElementById(paneId).classList.add('active');
  }
</script>
'''

# WRITE HTML
with open(out_html_name, 'w', encoding='utf-8') as f:
    # header
    f.write('<!DOCTYPE html>\n')
    f.write('<html>\n')
    f.write('<head>\n')
    f.write('<meta charset="utf-8">\n')
    f.write('<title>Geospatial Data Diff Report</title>\n')
    f.write(TAB_STYLE_SCRIPT)
    f.write('</head>\n')

    # start writing text at beginning of report
    f.write('<body>\n')
    f.write('<h1>Geopackage data difference report</h1>\n\n')
    f.write('Version A is considered the base or original version, and version B is considered the modified version. Deleted rows are only present in A, and inserted rows are only present in B. \n\n')

    # show version tree
    f.write('<h2>Version Tree</h2>\n\n')
    if version_tree_image[-3:] == 'svg':
        f.write(f'<img src="data:image/svg+xml;base64,{version_tree_string}">\n\n')
    else:
        f.write(f'<img src="data:image/{version_tree_image[-3:]};base64,{version_tree_string}">\n\n')
    
    # create tabsets for each pair-wise version comparison
    for i in comparisons:
        f.write(f'<h2>{comparisons[i]['name']}</h2>\n\n')

        base = diff.read_multi_gpkg(comparisons[i]['original'])
        modified = diff.read_multi_gpkg(comparisons[i]['changed'])
        layer_diff = diff.check_layer_match(base, modified)
        colnames = diff.check_colname_match(base, modified)
        col_dtypes = diff.check_dtype_match(base, modified)
        row_summary = diff.summarize_row_changes(base, modified)
        deletions = {j: pd.DataFrame(v) for j, v in diff.find_deleted_rows(base, modified).items()}
        insertions = {j: pd.DataFrame(v) for j, v in diff.find_inserted_rows(base, modified).items()}

        updates = {j: pd.DataFrame(v) for j, v in diff.find_updated_rows(base, modified).items()}
        df_to_del = []
        for i in updates:
            if 'index'.casefold() in updates[i]:
                no_idx = updates[i].drop(columns=['index'.casefold()])
                is_updated = no_idx.astype(str).apply(lambda row: row.str.contains('<br>').any(), axis=1)
                keep_df = pd.DataFrame(list(zip(no_idx['OBJECTID'], is_updated)), columns=['OBJECTID', 'keep'])
                keep_objectid = keep_df[keep_df['keep'] == True]['OBJECTID'].to_list()
                updates[i] = updates[i][updates[i]['OBJECTID'].isin(keep_objectid)]
            if len(updates[i]) == 0:
                df_to_del.append(i)
        updates = {k: v for k, v in updates.items() if k not in df_to_del}

        if all([layer_diff.empty, len(colnames) == 0, len(col_dtypes) == 0,
                row_summary.empty, len(deletions) == 0, len(insertions) == 0, len(updates) == 0]):
            f.write('<p>No differences found.</p>\n\n')
            continue

        # --- Build "Summary" tabset (nested inside outer tabset) ---
        summary_tabs = {}
        if not layer_diff.empty:
            summary_tabs['Different Layers'] = to_html_datatable(layer_diff)

        if len(colnames) > 0:
            colname_tabs = {j: to_html_datatable(colnames[j]) for j in colnames}
            summary_tabs['Different Column Names'] = make_tabset(colname_tabs)

        if len(col_dtypes) > 0:
            dtype_tabs = {j: to_html_datatable(col_dtypes[j]) for j in col_dtypes}
            summary_tabs['Different Column Data Types'] = make_tabset(dtype_tabs)

        if not row_summary.empty:
            summary_tabs['Summary of Row Changes'] = to_html_datatable(row_summary)

        # --- Build the outer tabset ---
        outer_tabs = {}
        if summary_tabs:
            outer_tabs['Summary'] = make_tabset(summary_tabs)

        if len(deletions) > 0:
            deletion_tabs = {j: to_html_datatable(deletions[j], maxRows = 1000, maxBytes = 0) for j in deletions}
            outer_tabs['Deleted Rows'] = make_tabset(deletion_tabs)

        if len(insertions) > 0:
            insertion_tabs = {j: to_html_datatable(insertions[j], maxRows = 1000, maxBytes = 0) for j in insertions}
            outer_tabs['Inserted Rows'] = make_tabset(insertion_tabs)

        if len(updates) > 0:
            update_tabs = {j: to_html_datatable(updates[j], maxRows = 1000, maxBytes = 0, allow_html=True) for j in updates}
            outer_tabs['Updated Rows'] = make_tabset(update_tabs)

        f.write(make_tabset(outer_tabs))
        f.write('\n\n')

    f.write('</body>\n</html>\n')

if create_diagram == True:
    import os
    os.remove(version_tree_image)