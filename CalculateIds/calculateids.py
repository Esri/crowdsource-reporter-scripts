import arcpy

# workspace containing fc and table
workspace = r''

# Feature class needing id values in field Report_ID
fc = r''

# table that manages ID values. 3 fields:
#   - RPTTYPE - text field - an index for the type of report getting an id assigned so multiple ids can be managed in one table
#   - NEXTVAL - long int - the next value to use in the id sequence
#   - INTERVAL - long int - the number of values to jump between id values
tbl = r''

# value to search for in the RPTTYPE field in the table to find the right sequence
inc_type = 'Parks'

# get next id value and interval from table
with arcpy.da.SearchCursor(tbl, ['NEXTVAL', 'INTERVAL'], where_clause = """RPTTYPE = '{}'""".format(inc_type)) as tblrows:
    for row in tblrows:
        sequence_value = row[0]
        interval_value = row[1]

# Start edit session
edit = arcpy.da.Editor(workspace)
edit.startEditing(False, True)
edit.startOperation()

# find and update all features that need ids
with arcpy.da.UpdateCursor(fc, 'Report_ID', where_clause="""Report_ID is null""") as fcrows:

    for row in fcrows:

        # Calculate a new id value from a string and the current id value
        row[0] = "ConcernID-{}".format(sequence_value)
        #row[0] = "ConcernID-{:04d}".format(sequence_value) #alt: pad sequence value with 4 zeros

        fcrows.updateRow(row)

        # increment the sequence value by the specified interval
        sequence_value += interval_value

# update the table values for next time
with arcpy.da.UpdateCursor(tbl, 'NEXTVAL', where_clause="""RPTTYPE = '{}'""".format(inc_type)) as tblrows:
    for row in tblrows:
        row[0] = sequence_value
        tblrows.updateRow(row)

# Close edit session
edit.stopOperation()
edit.stopEditing(True)