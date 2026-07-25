import pygeodiff
import pandas as pd
import geopandas as gpd
import re
geodiff = pygeodiff.GeoDiff()

# LOOK FOR DIFFERENCES BETWEEN GEOPACKAGE FILES
def find_differences(original_version, changed_version, out_name):
    # df with all changed rows
    geodiff.create_changeset(original_version, changed_version, out_name + '.diff')
    geodiff.list_changes(out_name + '.diff', out_name + '.json')
    diff_json = pd.read_json(out_name + '.json')
    all_changes = pd.DataFrame(diff_json['geodiff'].tolist())
    return all_changes

# SUMMARIZE DIFFERENCES BY LAYER
def summarize_differences(diff_file):
    # summary df that shows the number+type of changes in each layer
    geodiff.list_changes_summary(diff_file + '.diff', diff_file + '_summary.json')
    summary_df = pd.read_json(diff_file + '_summary.json')
    summary_df = pd.DataFrame(summary_df['geodiff_summary'].tolist())
    summary_df = summary_df[['table', 'update', 'insert', 'delete']]
    return summary_df

# DELETED ROW TABLES (ONE TABLE PER LAYER)
# only cases of row deletion
def deleted_rows(change_df, original_version):
    deleted_rows = change_df[change_df['type'] == 'delete']

    # this will become a dictionary of dataframes, with a dataframe for each gpkg layer
    deleted_rows_by_layer = {}

    for i in deleted_rows['table'].unique(): # for each layer with deleted rows
        # make a dataframe of only the deleted rows
        deleted_from_layer = deleted_rows[deleted_rows['table'] == i]
        deleted_from_layer = pd.DataFrame(deleted_from_layer['changes'].tolist())
        deleted_from_layer = deleted_from_layer.map(lambda d: d.get('old') if isinstance(d, dict) else None)
        deleted_from_layer = deleted_from_layer.iloc[:, 2:]

        # and change the column names to the original names
        colnames = gpd.read_file(original_version, layer = i).columns.tolist()
        colnames = [x for x in colnames if x != 'geometry']
        deleted_from_layer.columns = colnames

        # the add the dataframe to the dictionary
        deleted_rows_by_layer[i] = deleted_from_layer
    
    return deleted_rows_by_layer

# INSERTED ROW TABLES (ONE TABLE PER LAYER)
def inserted_rows(change_df, changed_version):
    # only cases of row insertion
    inserted_rows = change_df[change_df['type'] == 'insert']

    # this will become a dictionary of dataframes, with a dataframe for each gpkg layer
    inserted_rows_by_layer = {}

    for i in inserted_rows['table'].unique(): # for each layer with inserted rows
        # make a dataframe of only the inserted rows
        inserted_from_layer = inserted_rows[inserted_rows['table'] == i]
        inserted_from_layer = pd.DataFrame(inserted_from_layer['changes'].tolist())
        inserted_from_layer = inserted_from_layer.map(lambda d: d.get('new') if isinstance(d, dict) else None)
        inserted_from_layer = inserted_from_layer.iloc[:, 2:]

        # and change the column names to the original names
        colnames = gpd.read_file(changed_version, layer = i).columns.tolist()
        colnames = [x for x in colnames if x != 'geometry']
        inserted_from_layer.columns = colnames

        # the add the dataframe to the dictionary
        inserted_rows_by_layer[i] = inserted_from_layer

    return inserted_rows_by_layer

# CHANGED ROW TABLES (ONE TABLE PER LAYER)
def changed_rows(change_df, original_version):
    # only updated rows
    updated_rows = change_df[change_df['type'] == 'update']

    # this will become a dictionary of dataframes, with a dataframe for each gpkg layer
    updated_rows_by_layer = {}
    for i in updated_rows['table'].unique():
        # subsetted dataframe with just updated rows in current layer
        updated_in_layer = updated_rows[updated_rows['table'] == i]
        updated_in_layer = pd.DataFrame(updated_in_layer['changes'].tolist())

        # replacement dictionary for column index to column names
        # check that this is consistent across layers (e.g., add 2 to the
        # colindex because the first two columns in updated_in_layer don't match
        # anything in the original table)
        input_gpkg = gpd.read_file(original_version, layer = i)
        input_gpkg = input_gpkg.drop(columns=['geometry'])
        colnames = input_gpkg.columns.tolist()
        colindex = list(range(2, len(colnames)+2))
        column_replacements = dict(zip(colindex,colnames))

        # replace column indices with actual column names from original dataset
        for row in range(updated_in_layer.shape[0]):
            for col in range(updated_in_layer.shape[1]):
                if isinstance(updated_in_layer.iloc[row, col], dict):
                    current_col_val = updated_in_layer.iloc[row, col]['column']
                    if current_col_val >= 2:
                        updated_in_layer.iloc[row, col]['column'] = column_replacements[current_col_val]
                    else:
                        updated_in_layer.iloc[row, col] = None

        # make a table with updated rows and without missing columns
        display_updates = pd.DataFrame(index=updated_in_layer.index, columns=input_gpkg.columns)
        for j in range(display_updates.shape[0]):
            row = updated_in_layer.iloc[j].dropna(how='all')
            for col in row:
                both_values = 'old value: ' + str(col['old']) + '<br>new value: ' + str(col['new'])
                display_updates.loc[display_updates.index[j], col['column']] = both_values
            for col in range(len(display_updates.loc[j])):
                if pd.isna(display_updates.iloc[j, col]):
                    original_objectid = re.search(r'old value: (.*?)<br>', display_updates.loc[display_updates.index[j], 'OBJECTID'])
                    original_objectid = int(original_objectid.group(1))
                    original_row = input_gpkg[input_gpkg['OBJECTID'] == original_objectid]
                    original_value = original_row[display_updates.columns[col]].iloc[0]
                    if pd.isna(original_value) == False:
                        display_updates.iloc[j, col] = original_value

        updated_rows_by_layer[i] = display_updates
    
    return updated_rows_by_layer
