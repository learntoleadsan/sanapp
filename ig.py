import pandas as pd
import plotly.graph_objects as go
import plotly.subplots as sp
import streamlit as st

# Load the data
df = pd.read_csv(r'C:\GENAI\rocketramp\Project_Quantum_Leap.csv')

# Display the column names to check for the correct ones
# st.write("Column Names:", df.columns)

# Filter relevant contact owners
contact_owners = ['dan@rocketramp.ai', 'adam@rocketramp.ai', 'alex@rocketramp.ai', 'chris@rocketramp.ai']
df = df[df['Contact Owner'].isin(contact_owners)]

# Parse date columns
date_columns = ['Opp Created Date', 'Discovery Date', 'Demo Date', 'Proposal date', 'Technical Validation Date', 'Closed Won', 'Closed Lost Date']
for col in date_columns:
    df[col] = pd.to_datetime(df[col], errors='coerce')

# Combine Closed Won and Closed Lost into a single column
df['Final Date'] = df[['Closed Won', 'Closed Lost Date']].min(axis=1)

# Calculate the number of days from "Opp Created Date"
df['Days to Discovery'] = (df['Discovery Date'] - df['Opp Created Date']).dt.days
df['Days to Demo'] = (df['Demo Date'] - df['Opp Created Date']).dt.days
df['Days to Proposal'] = (df['Proposal date'] - df['Opp Created Date']).dt.days
df['Days to Validation'] = (df['Technical Validation Date'] - df['Opp Created Date']).dt.days
df['Days to Final'] = (df['Final Date'] - df['Opp Created Date']).dt.days

# Calculate summary statistics for each owner
summary_df = df.groupby('Contact Owner').agg({
    'Days to Discovery': ['mean', 'median', 'min', 'max'],
    'Days to Demo': ['mean', 'median', 'min', 'max'],
    'Days to Proposal': ['mean', 'median', 'min', 'max'],
    'Days to Validation': ['mean', 'median', 'min', 'max'],
    'Days to Final': ['mean', 'median', 'min', 'max'],
    'Opp Created Date': 'count'
}).rename(columns={'Opp Created Date': 'Total Opportunities'}).reset_index()

# Flatten the MultiIndex columns
summary_df.columns = ['_'.join(col).strip() if col[1] else col[0] for col in summary_df.columns.values]

# Calculate company averages
company_avg = summary_df.mean(axis=0, numeric_only=True).to_frame().T
company_avg['Contact Owner'] = 'Avg for the Company'

# Calculate average for contact owners
owners_avg = summary_df[summary_df['Contact Owner'] != 'Avg for the Company'].mean(axis=0, numeric_only=True).to_frame().T
owners_avg['Contact Owner'] = 'Avg for Contact Owners'

# Append company averages and owners averages to summary_df
summary_df = pd.concat([summary_df, company_avg, owners_avg], ignore_index=True)

# Define stages for iteration
stages = ['Days to Discovery_mean', 'Days to Demo_mean', 'Days to Proposal_mean', 'Days to Validation_mean', 'Days to Final_mean']

# Contact Owner filter above the chart
selected_owners = st.multiselect("Select Contact Owners:", contact_owners, default=contact_owners)

# Filter the summary dataframe based on selected owners
filtered_summary_df = summary_df[summary_df['Contact Owner'].isin(selected_owners + ['Avg for the Company', 'Avg for Contact Owners'])]

# Create the interactive line chart for summary statistics
fig_summary = sp.make_subplots(rows=5, cols=1, shared_xaxes=True, vertical_spacing=0.02)

for i, stage in enumerate(stages):
    stage_name = stage.replace('_mean', '')
    fig_summary.add_trace(
        go.Scatter(x=filtered_summary_df[stage], y=filtered_summary_df['Contact Owner'], mode='lines+markers', name=f'{stage_name} (Mean)'),
        row=i+1, col=1
    )
    fig_summary.update_yaxes(title_text=f'{stage_name} (Mean Days)', row=i+1, col=1)

# Highlight top performers in summary chart
top_performers = summary_df.nlargest(2, 'Days to Final_mean')
for owner in top_performers['Contact Owner']:
    for i, stage in enumerate(stages):
        stage_name = stage.replace('_mean', '')
        fig_summary.add_trace(
            go.Scatter(
                x=filtered_summary_df[filtered_summary_df['Contact Owner'] == owner][stage],
                y=filtered_summary_df[filtered_summary_df['Contact Owner'] == owner]['Contact Owner'],
                name=f'Top Performer: {owner} ({stage_name})',
                line=dict(color='gold', width=4)
            ),
            row=i+1, col=1
        )

fig_summary.update_layout(
    height=800,
    title_text='Average Number of Days to Progress Through Stages by Contact Owner',
    showlegend=False,
    template='plotly_white'
)

# Display in Streamlit
st.title("Performance Comparison Between Owners")

# Display the summary statistics chart
st.write("### Average Number of Days to Progress Through Stages by Owner")
st.plotly_chart(fig_summary)

# Display the summary DataFrame
st.write("### Summary Data")
st.dataframe(summary_df)

# Show detailed data for each stage
st.write("### Detailed Data for Each Stage")
detailed_data = df[df['Contact Owner'].isin(contact_owners)]
st.dataframe(detailed_data)
