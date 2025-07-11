import streamlit as st
import pandas as pd
import io

#Configuration
DOMAINS = ["CDC", "RDC", "SC", "LINT", "CQ", "SENTRY", "DFT", "SAFECONNECT", "CQMAI"]

#Parse text file
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

def unpivot_and_save(wide_df):
    records = []
    for _, row in wide_df.iterrows():
        varname = row[('Variable Name', '')]
        _type = row[('Type', '')]
        description = row[('Description', '')]
        origin = row[('CDC', 'VarType')]  # assuming uniform origin

        line = f"{varname},{_type},{origin},\"{description}\""

        domain_parts = []
        for domain in DOMAINS:
            value = row.get((domain, 'Value'), '')
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
        updated_content = unpivot_and_save(edited_df)
        st.download_button(
            label="Download .txt file",
            data=updated_content,
            file_name="updated_config.txt",
            mime="text/plain"
        )
else:
    st.info("Please upload a .txt configuration file to begin.")
