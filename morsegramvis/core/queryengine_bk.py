from pandas.api.types import (
    is_categorical_dtype,
    is_datetime64_any_dtype,
    is_numeric_dtype,
    is_object_dtype,
)
import pandas as pd
from sklearn.neighbors import NearestNeighbors
import streamlit as st
import argparse
import seaborn as sns
import matplotlib.pyplot as plt
import os
import plotly.express as px


APP_NAME = "MorseGramVis"


def export_data(df: pd.DataFrame):
    """
    Export data to csv

    Args:
        df (pd.DataFrame): Dataframe to export
    """
    # ask file path to save
    file_path = st.text_input("File path to save", "<Directory Path>/data.csv")

    # button to download csv
    if st.button("Download CSV"):
        # check base path
        folder = os.path.dirname(file_path)
        if os.path.exists(folder):
            df.to_csv(file_path, index=False)
            st.success("File saved successfully")
        else:
            st.error("Please enter a valid file path")

# plt.style.use("ggplot")
# setting default value for page
st.set_page_config(page_title="Query Engine")

# streamlit run queryengine.py -- --csv_loc=particle_stats.csv

parser = argparse.ArgumentParser()
parser.add_argument('--csv', type=str, default='default')
# # write output to txt
# f = open("output.txt", "w")
# f.write(str(sys.argv[1:]))
# f.close()
args = parser.parse_args()

# add a dropdown to select page in the sidebar
page = st.sidebar.selectbox(
    "Select page",
    ("Data Exploration",
    "Similar Particles Search",
    "Graph NN logs")
)

if page == "Data Exploration":

    is_file_uploaded = False

    # read csv
    try:
        df = pd.read_csv(args.csv)
        is_file_uploaded = True
    except:
        # file picker to upload csv
        data_file = st.file_uploader("Upload CSV", type=["csv"])
        if data_file is not None:
            df = pd.read_csv(data_file)
            is_file_uploaded = True
            

    def filter_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """
        Adds a UI on top of a dataframe to let viewers filter columns

        Args:
            df (pd.DataFrame): Original dataframe

        Returns:
            pd.DataFrame: Filtered dataframe
        """
        modify = st.checkbox("Add filters")

        if not modify:
            return df

        df = df.copy()

        # Try to convert datetimes into a standard format (datetime, no timezone)
        for col in df.columns:
            if is_object_dtype(df[col]):
                try:
                    df[col] = pd.to_datetime(df[col])
                except Exception:
                    pass

            if is_datetime64_any_dtype(df[col]):
                df[col] = df[col].dt.tz_localize(None)

        modification_container = st.container()

        with modification_container:
            to_filter_columns = st.multiselect("Filter dataframe on", df.columns)
            for column in to_filter_columns:
                left, right = st.columns((1, 20))
                # Treat columns with < 10 unique values as categorical
                if is_categorical_dtype(df[column]) or df[column].nunique() < 10:
                    user_cat_input = right.multiselect(
                        f"Values for {column}",
                        df[column].unique(),
                        default=list(df[column].unique()),
                    )
                    df = df[df[column].isin(user_cat_input)]
                elif is_numeric_dtype(df[column]):
                    _min = float(df[column].min())
                    _max = float(df[column].max())
                    step = (_max - _min) / 100
                    user_num_input = right.slider(
                        f"Values for {column}",
                        min_value=_min,
                        max_value=_max,
                        value=(_min, _max),
                        step=step,
                    )
                    df = df[df[column].between(*user_num_input)]
                elif is_datetime64_any_dtype(df[column]):
                    user_date_input = right.date_input(
                        f"Values for {column}",
                        value=(
                            df[column].min(),
                            df[column].max(),
                        ),
                    )
                    if len(user_date_input) == 2:
                        user_date_input = tuple(map(pd.to_datetime, user_date_input))
                        start_date, end_date = user_date_input
                        df = df.loc[df[column].between(start_date, end_date)]
                else:
                    user_text_input = right.text_input(
                        f"Substring or regex in {column}",
                    )
                    if user_text_input:
                        df = df[df[column].astype(str).str.contains(user_text_input)]

        return df

    st.title(APP_NAME + " - Data Exploration")
    st.write(
        """
        """
    )

    if not is_file_uploaded:
        st.error("Please upload a file to proceed")
        st.stop()

    # # multi-select feature to select columns
    selected_columns = st.multiselect(
        "Select columns to display",
        df.columns, default=[a for a in df.columns]
    )

    new_df = filter_dataframe(df[selected_columns])
    st.dataframe(new_df)

    # show number of rows and columns
    st.write(f"Number of rows: {new_df.shape[0]}")
    st.write(f"Number of columns: {new_df.shape[1]}")

    export_data(new_df)

    st.write("""---""")

    # Histogram

    st.subheader("Histogram")
    st.header("Distribution of columns")
    hist_valid_cols = [col for col in new_df.columns if is_numeric_dtype(new_df[col])]
    # # create single-select for columns
    hist_col = st.selectbox("Select column", hist_valid_cols)

    if not hist_col:
        st.error("Please select at least one column to display")
    else:
        # # histogram
        fig, ax = plt.subplots(figsize=(10, 10))
        st.write(sns.histplot(data=new_df[hist_col], ax=ax))
        st.pyplot(fig)

    st.write("""---""")

    # scatter plot
    st.subheader("Scatter Plot")

    # create multi-select for columns
    x_axis = st.selectbox("X axis", new_df.columns)
    y_axis = st.selectbox("Y axis", new_df.columns)

    # # scatter plot
    fig, ax = plt.subplots(figsize=(10, 10))
    st.write(sns.scatterplot(x=x_axis, y=y_axis, data=new_df, ax=ax))
    st.pyplot(fig)

    st.write("""---""")

    # heatmap

    st.subheader("Heatmap")
    st.header("Correlation between columns")
    cmap = st.selectbox("Select color map", ["coolwarm", "magma", "viridis"])
    # # heatmap
    fig, ax = plt.subplots(figsize=(10, 10))
    valid_cols = [col for col in new_df.columns if is_numeric_dtype(new_df[col])]
    st.write(sns.heatmap(new_df[valid_cols].corr(), ax=ax, cmap=cmap))
    st.pyplot(fig)

    st.write("""---""")

elif page == "Similar Particles Search":
    st.title(APP_NAME + " - Similar Particles Search")
    st.write(
        """
        """
    )

    # read csv
    df = pd.read_csv(args.csv)
    cp_ids = df['cp_id'].copy()
    df = df[['EI', 'FI', 'S', 'C']] # only use these columns
    
    # perform Nearest Neighbors sklearn

    # select number of neighbors
    n_neighbors = st.slider("Number of neighbors", 1, 100, 5)

    # input to choose algorithm
    algorithm = st.selectbox("Algorithm", ("auto", "ball_tree", "kd_tree", "brute"))

    nbrs = NearestNeighbors(n_neighbors=n_neighbors, algorithm=algorithm).fit(df)
    distances, indices = nbrs.kneighbors(df)

    # input to select cp_id from cp_ids
    cp_id = st.selectbox("Select cp_id", cp_ids)

    # get index of cp_id
    cp_id_index = cp_ids[cp_ids == cp_id].index[0]

    # get indices of neighbors
    neighbors = indices[cp_id_index]

    # get cp_ids of neighbors
    neighbors_cp_ids = cp_ids[neighbors]
    # neighbors distances
    neighbors_distances = distances[cp_id_index]

    # df of neighbors
    neighbors_df = pd.DataFrame({'cp_id': neighbors_cp_ids, 'distance': neighbors_distances})

    st.write(neighbors_df)

    export_data(neighbors_df)

elif page == "Graph NN logs":

    st.title(APP_NAME + " - Graph Neural Network Logs")
    st.write(
        """
        """
    )

    # load file
    files = st.file_uploader("Upload file", type="csv", accept_multiple_files=True)

    # display plots for each file column wise
    if files is not None:
        logs_data = []
        for file in files:

            # get file name
            file_name = file.name

            # load log data
            log_data = pd.read_csv(file)

            # append log data to list
            logs_data.append([log_data, file_name])

        if len(logs_data) > 0:

            # display plots for each file separately in a column layout
            col1, col2 = st.columns(2)
            with col1:
                st.header("Train/Test Accuracy")
                # Create line chart for train and test accuracy
                accuracy_chart = px.line(logs_data[0][0], x='epoch', y=['train_accuracy', 'test_accuracy'], 
                                        title=logs_data[0][1])
                st.plotly_chart(accuracy_chart)

                st.header("Train/Test Loss")
                # Create line chart for train and test loss
                loss_chart = px.line(logs_data[0][0], x='epoch', y=['train_loss', 'test_loss'], 
                                    title=logs_data[0][1])
                st.plotly_chart(loss_chart)

            with col2:
                st.header("Train/Test Accuracy")
                # Create line chart for train and test accuracy
                accuracy_chart = px.line(logs_data[1][0], x='epoch', y=['train_accuracy', 'test_accuracy'],
                                        title=logs_data[1][1])
                st.plotly_chart(accuracy_chart)

                st.header("Train/Test Loss")
                # Create line chart for train and test loss
                loss_chart = px.line(logs_data[1][0], x='epoch', y=['train_loss', 'test_loss'],
                                        title=logs_data[1][1])
                st.plotly_chart(loss_chart)
        
        else:
            st.error("Please upload a file")
            
