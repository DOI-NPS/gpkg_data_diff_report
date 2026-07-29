# IMPORT DEPENDENCIES
import pandas as pd
from itables import to_html_datatable

# these are custom functions from a script in this directory
import custom_diff_functions as diff

# this is a dictionary with the comparisons to be included in the report
# it's in .gitignore
with open('report_specifications.py') as f:
    exec(f.read())

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
    f.write('<!DOCTYPE html>\n<html>\n<head>\n<meta charset="utf-8">\n')
    f.write('<title>SDE Data Diff Report</title>\n')
    f.write(TAB_STYLE_SCRIPT)
    f.write('</head>\n<body>\n')

    for i in comparisons:
        f.write(f"<h1>{comparisons[i]['name']}</h1>\n\n")

        base = diff.read_multi_gpkg(comparisons[i]['original'])
        modified = diff.read_multi_gpkg(comparisons[i]['changed'])
        layer_diff = diff.check_layer_match(base, modified)
        colnames = diff.check_colname_match(base, modified)
        col_dtypes = diff.check_dtype_match(base, modified)
        row_summary = diff.summarize_row_changes(base, modified)
        deletions = {j: pd.DataFrame(v) for j, v in diff.find_deleted_rows(base, modified).items()}
        insertions = {j: pd.DataFrame(v) for j, v in diff.find_inserted_rows(base, modified).items()}
        updates = {j: pd.DataFrame(v) for j, v in diff.find_updated_rows(base, modified).items()}

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
            deletion_tabs = {j: to_html_datatable(deletions[j]) for j in deletions}
            outer_tabs['Deleted Rows'] = make_tabset(deletion_tabs)

        if len(insertions) > 0:
            insertion_tabs = {j: to_html_datatable(insertions[j]) for j in insertions}
            outer_tabs['Inserted Rows'] = make_tabset(insertion_tabs)

        if len(updates) > 0:
            update_tabs = {j: to_html_datatable(updates[j], allow_html=True) for j in updates}
            outer_tabs['Updated Rows'] = make_tabset(update_tabs)

        f.write(make_tabset(outer_tabs))
        f.write('\n\n')

    f.write('</body>\n</html>\n')