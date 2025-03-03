import streamlit as st
import pandas as pd
from st_table_select_cell import st_table_select_cell

st.subheader("Example of st_table_select_cell")

# prepare an example dataframe
data = pd.DataFrame({'Dataset':['energy','traffic','syn'], 'Test':['ehistory','snapshot','aggmax'], 'PG': [3,6,9], 'TG':[2,5,7]})
st.dataframe(data)

# show table and get user selected cell
selectedCell = st_table_select_cell(data)
st.write(selectedCell)

if selectedCell:
    rowId = selectedCell['rowId']
    colIndex = selectedCell['colIndex']
    st.write(rowId, colIndex)

    # return column name of the selected cell.
    st.write(data.columns[colIndex])
    
    # return row of the selected cell as dict.
    st.write(data.iloc[int(rowId)].to_dict())
    
    # return cell content as string.
    st.write(data.iat[int(rowId), colIndex])
else:
    st.write('no select')