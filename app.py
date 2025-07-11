import streamlit as st
import pandas as pd

#Configuration
DOMAINS = ["CDC", "RDC", "SC", "LINT", "CQ", "SENTRY", "DFT", "SAFECONNECT", "CQMAI"]

#Parse uploaded file
def parse_and_widen(file_content):
    rows = []
    lines = file_content.decode("utf-8").splitlines()
    for line in lines:
        parts = line.strip().split(',')
        varname = parts[0]
        _type = parts[1]
        origin = parts[2]
        description = parts[3].strip('"')
        domain_values = dict(p.split(':') for p in parts[4:])

        row = {
            ('Variable Name', ''): varname,
            ('Type', ''): _type,
            ('Description', ''): description,
        }

        for domain in DOMAINS:
            row[(domain, 'VarType')] = origin
            value = domain_values.get(domain, "")
            if domain in ["SAFECONNECT", "CQMAI"] and value == "":
                value = "reporting"
            row[(domain, 'Value')] = value

        rows.append(row)

    columns = pd.MultiIndex.from_tuples(rows[0].keys())
    df = pd.DataFrame(rows, columns=columns)
    return df

def unpivot_and_save(df):
    # Flatten MultiIndex columns if needed
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = ['_'.join(col).strip('_') for col in df.columns]

    # Clean column names: strip spaces and underscores
    df.columns = [col.strip().replace(" ", "").replace("__", "_") for col in df.columns]

    def find_col(possible_names):
        for name in possible_names:
            if name in df.columns:
                return name
        st.error(f"Available columns: {df.columns.tolist()}")
        raise KeyError(f"Could not find any of: {possible_names}")

    records = []
    for _, row in df.iterrows():
        varname_col = find_col(["Variable Name", "VariableName", "Variable_Name", "Variable Name_", "VariableName_"])
        type_col = find_col(["Type", "Type_"])
        desc_col = find_col(["Description", "Description_"])
        origin_col = find_col(["CDC VarType", "CDC_VarType", "CDCVarType"])

        varname = row[varname_col]
        _type = row[type_col]
        description = row[desc_col]
        origin = row[origin_col]

        line = f"{varname},{_type},{origin},\"{description}\""

        domain_parts = []
        for domain in DOMAINS:
            value_col = f"{domain}_Value"
            value = row.get(value_col, "")
            domain_parts.append(f"{domain}:{value}")

        line += "," + ",".join(domain_parts)
        records.append(line)

    return "\n".join(records)

#Streamlit UI
st.set_page_config(layout="wide")
st.title("Config Editor")

uploaded_file = st.file_uploader("Upload a config .txt file", type=["txt"])

if uploaded_file:
    df = parse_and_widen(uploaded_file.read())

    edited_df = st.data_editor(
        df,
        use_container_width=True,
        height=750,
        num_rows="dynamic"
    )

    if st.button("Download Updated File"):
        st.write("Column names after editing:")
        st.write(edited_df.columns.tolist())  # Show what's actually in the DataFrame

        try:
            updated_content = unpivot_and_save(edited_df)
            st.download_button(
                label="Download .txt file",
                data=updated_content,
                file_name="updated_config.txt",
                mime="text/plain"
            )
        except Exception as e:
            st.error(f"Error: {e}")
