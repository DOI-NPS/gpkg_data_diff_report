import geopandas as gpd
import pandas as pd

# read in geopackages to dictionaries
def read_multi_gpkg(path):
    gpkgs = {}
    layernames = gpd.list_layers(path)
    layernames = layernames.iloc[:, 0].tolist()
    for layer in layernames:
        gpkgs[layer] = gpd.read_file(path, layer = layer)
        for col in gpkgs[layer].columns:
            try:
                gpkgs[layer][col] = gpkgs[layer][col].astype('int64')
            except Exception:
                gpkgs[layer][col] = gpkgs[layer][col].astype('string')
    return gpkgs

# check whether the geopackages have the same layers
def check_layer_match(gpkgA, gpkgB):
    only_A = list(set(gpkgA) - set(gpkgB))
    only_B = list(set(gpkgB) - set(gpkgA))
    combined_sets = {'Unique to A': pd.Series(only_A), 'Unique to B': pd.Series(only_B)}
    return pd.DataFrame(combined_sets)

# check for differences in column names
def check_colname_match(gpkgA, gpkgB):
    colname_mismatches = {}
    for i in list(set(gpkgA) & set(gpkgB)):
        # check column names
        a_colnames = gpkgA[i].columns.tolist()
        b_colnames = gpkgB[i].columns.tolist()
        a_cols = list(set(a_colnames) - set(b_colnames))
        b_cols = list(set(b_colnames) - set(a_colnames))
        # if any don't match then output df for this layer
        if len(a_cols) > 0 or len(b_cols) > 0:
            combined_sets = {'Unique to A': pd.Series(a_cols), 'Unique to B': pd.Series(b_cols)}
            colname_mismatches[i] = pd.DataFrame(combined_sets)
    return(colname_mismatches)

# check for differences in column data types
def check_dtype_match(gpkgA, gpkgB):
    dtype_mismatches = {}
    for i in list(set(gpkgA) & set(gpkgB)):
        # check column names
        a_colnames = gpkgA[i].columns.tolist()
        b_colnames = gpkgB[i].columns.tolist()
        a_cols = set(a_colnames) - set(b_colnames)
        b_cols = set(b_colnames) - set(a_colnames)
        # compare data types in columns
        if len(a_cols) == 0 and len(b_cols) == 0:
            compare_dtype = gpkgA[i].dtypes.compare(gpkgB[i].dtypes)
        else: # if the columns are different, need to only compare intersecting columns
            base_redux = gpkgA[i]
            mod_redux = gpkgB[i]
            base_redux = base_redux[base_redux.columns.intersection(mod_redux.columns)]
            mod_redux = mod_redux[mod_redux.columns.intersection(base_redux.columns)]
            compare_dtype = base_redux.dtypes.compare(mod_redux.dtypes)
        # add df of differences to dictionary, if present
        compare_dtype = compare_dtype.rename(columns = {'self':'original', 'other':'modified'})
        if not compare_dtype.empty:
            dtype_mismatches[i] = compare_dtype
    return dtype_mismatches

# check for deleted rows
def find_deleted_rows(gpkgA, gpkgB):
    deleted_rows = {}
    for i in list(set(gpkgA) & set(gpkgB)):
        if gpkgA[i].empty:
            continue
        if 'OBJECTID' in gpkgA[i].columns:
            deleted_objectid = list(set(gpkgA[i]['OBJECTID']) - set(gpkgB[i]['OBJECTID']))
            if len(deleted_objectid) > 0:
                deleted_rows[i] = gpkgA[i][gpkgA[i]['OBJECTID'].isin(deleted_objectid)]
        else:
            comparison = pd.merge(gpkgA[i], gpkgB[i], how='outer', indicator=True)
            deletions = comparison[comparison['_merge'] == 'left_only']
            if len(deletions) > 0:
                deleted_rows[i] = comparison[comparison['_merge'] == 'left_only']
    return deleted_rows

# check for inserted rows
def find_inserted_rows(gpkgA, gpkgB):
    inserted_rows = {}
    for i in list(set(gpkgA) & set(gpkgB)):
        if gpkgA[i].empty:
            continue
        if 'OBJECTID' in gpkgA[i].columns:
            inserted_objectid = list(set(gpkgB[i]['OBJECTID']) - set(gpkgA[i]['OBJECTID']))
            if len(inserted_objectid) > 0:
                inserted_rows[i] = gpkgB[i][gpkgB[i]['OBJECTID'].isin(inserted_objectid)]
        else:
            comparison = pd.merge(gpkgA[i], gpkgB[i], how='outer', indicator=True)
            deletions = comparison[comparison['_merge'] == 'left_only']
            if len(deletions) > 0:
                inserted_rows[i] = comparison[comparison['_merge'] == 'right_only']
    return inserted_rows

# check for row updates
def find_updated_rows(gpkgA, gpkgB):
    updated_rows = {}
    for i in list(set(gpkgA) & set(gpkgB)):
        # skip empty layers
        if gpkgA[i].empty or 'OBJECTID' not in gpkgA[i].columns:
            continue
        a_row_matches = gpkgA[i]
        b_row_matches = gpkgB[i]
        # sort by OBJECTID for df comparison
        a_row_matches['OBJECTID'] = a_row_matches['OBJECTID'].astype('int64')
        a_row_matches = a_row_matches.sort_values(by = 'OBJECTID')
        b_row_matches['OBJECTID'] = b_row_matches['OBJECTID'].astype('int64')
        b_row_matches = b_row_matches.sort_values(by = 'OBJECTID')
        # keep only rows with an OBJECTID that exists in A and B
        keep_objectid = list(set(a_row_matches['OBJECTID']) & set(b_row_matches['OBJECTID']))
        a_row_matches = a_row_matches[a_row_matches['OBJECTID'].isin(keep_objectid)]
        a_row_matches = a_row_matches.reset_index(drop = True)
        b_row_matches = b_row_matches[b_row_matches['OBJECTID'].isin(keep_objectid)]
        b_row_matches = b_row_matches.reset_index(drop = True)
        # reduce columns to only columns that exist in A and B
        a_cols = set(gpkgA[i].columns) - set(gpkgB[i].columns)
        b_cols = set(gpkgB[i].columns) - set(gpkgA[i].columns)
        if len(a_cols) > 0:
            a_to_compare = a_row_matches.drop(columns = list(a_cols))
        else:
            a_to_compare = a_row_matches
        if len(b_cols) > 0:
            b_to_compare = b_row_matches.drop(columns = list(b_cols))
        else:
            b_to_compare = b_row_matches
        # if there are differences between A and B, make a df of the updates
        if not a_to_compare.equals(b_to_compare):
            # compare reduced data frames for changed rows
            update_dbl_df = a_to_compare.compare(b_to_compare, keep_shape = True, keep_equal = True)
            # collapse "self" and "other" versions of each column
            update_col_merge = pd.DataFrame()
            for j in range(0, update_dbl_df.shape[1], 2):
                versionA = update_dbl_df.iloc[:,j]
                versionB = update_dbl_df.iloc[:,j+1]
                versionAB = pd.Series(dtype = str)
                for k in range(len(versionA)):
                    if versionA[k] == versionB[k]:
                        versionAB[k] = str(versionA[k])
                    elif pd.isna(versionA[k]) and pd.isna(versionB[k]):
                        versionAB[k] = 'NaN'
                    else:
                        versionAB[k] = 'A: ' + str(versionA[k]) + '<br>B: ' + str(versionB[k])
                update_col_merge[update_dbl_df.columns[j][0]] = versionAB
            # only keep rows with updates
            update_col_merge = update_col_merge[update_col_merge.map(lambda x: '<br>' in str(x)).any(axis=1)]
            # if the columns in both versions are the same, then the merged columns df
            # can be added to the dictionary later
            if len(a_cols) == 0 and len(b_cols) == 0:
                updated_rows[i] = update_col_merge
            # but if any columns were added or dropped, then re-insert them into the
            # output df before adding the df to the dictionary
            else:
                all_colnames = list(dict.fromkeys(list(gpkgA[i].columns) + list(gpkgB[i].columns)))
                update_display = pd.DataFrame(columns=all_colnames)
                for j in update_display.columns:
                    if j in a_cols:
                        update_display[j] = 'A: ' + a_row_matches[j].astype(str)
                    elif j in b_cols:
                        update_display[j] = 'B: ' + b_row_matches[j].astype(str)
                    else:
                        update_display[j] = update_col_merge[j]
                updated_rows[i] = update_display
    return updated_rows

# summarize differences
def summarize_row_changes(gpkgA, gpkgB):
    summary_df = pd.DataFrame(columns = ['Layer', 'Insertions', 'Deletions', 'Updates'])
    insert = find_inserted_rows(gpkgA, gpkgB)
    delete = find_deleted_rows(gpkgA, gpkgB)
    update = find_updated_rows(gpkgA, gpkgB)
    for i in list(set(gpkgA) | set(gpkgB)):
        if i not in list(set(gpkgA) & set(gpkgB)):
            in_n = None
            del_n = None
            upd_n = None
        else:
            if i in insert.keys():
                in_n = insert[i].shape[0]
            else:
                in_n = 0
            if i in delete.keys():
                del_n = delete[i].shape[0]
            else:
                del_n = 0
            if i in update.keys():
                upd_n = update[i].shape[0]
            else:
                upd_n = 0
        summary_df.loc[len(summary_df)] = [i, in_n, del_n, upd_n]
    return summary_df