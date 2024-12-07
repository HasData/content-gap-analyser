import streamlit as st
import pandas as pd
from hasdata import extract_serp_via_api, extract_html_via_api, extract_text_from_html
from google_api import analyze_entities, get_entities_dataframe

@st.cache_data
def stepOne(keyword):
    with st.spinner(f"Extract SERP Results for keyword \"{keyword}\""):
        organic_results = extract_serp_via_api(keyword, has_data_api_key)

        serp_results = []
        for result in organic_results:
            serp_results.append({
                "Position": result.get("position"),
                "Source": result.get("source"),
                "Link": result.get("link"),
                "Snippet": result.get("snippet")
            })

    # Create a DataFrame from the list of results
    serp_results_df = pd.DataFrame(serp_results)

    st.write("Serp API Results:")
    st.dataframe(serp_results_df, hide_index=True)

    st.success("SERP Results Extracted!")

    return serp_results_df

@st.cache_data
def stepTwo(serp_results_df):
    content_results_placeholder = st.empty()
    content_results_df = pd.DataFrame(columns=["Position", "Link", "Content"])

    progress_bar = st.progress(0, text="Extracting page content from each result...")

    for idx, row in serp_results_df.iterrows():
        html = extract_html_via_api(row.get("Link"), has_data_api_key)
        content = extract_text_from_html(html)

        new_row = {
            "Position": row.get("Position"),
            "Link": row.get("Link"),
            "Content": content
        }

        content_results_df = pd.concat([content_results_df, pd.DataFrame([new_row])], ignore_index=True)

        # Update the placeholder with the new DataFrame
        with content_results_placeholder.container():
            st.write("Pages Content Results:")
            st.dataframe(content_results_df, hide_index=True)

        progress_bar.progress((idx + 1) / len(serp_results_df))

    st.success("Pages Content Extracted!")
    return content_results_df

@st.cache_data
def stepThree(content_results_df):
    progress_bar = st.progress(0, text="Extracting text entities from each page...")

    # Initialize an empty DataFrame to store combined entities
    combined_entity_df = pd.DataFrame(columns=["Entity", "Salience", "Page Link"])

    st.write("Entities Extraction Results:")

    # Process each page and dynamically show expanders
    for idx, row in content_results_df.iterrows():
        # Extract entities for the current page
        api_response = analyze_entities(row.get("Content"), google_nlp_engine_api_key)
        entity_df = get_entities_dataframe(api_response)

        # Add a column for the page link to track which page each entity comes from
        entity_df["Page Link"] = row.get("Link")

        # Append to the combined DataFrame
        combined_entity_df = pd.concat([combined_entity_df, entity_df], ignore_index=True)

        # Display the expander for the current page
        with st.expander(f"Entities for {row.get('Link')}"):
            st.dataframe(entity_df.drop(columns=["Page Link"]))

        # Update the progress bar
        progress_bar.progress((idx + 1) / len(content_results_df))

    # Display a success message
    st.success("Entity extraction completed for all pages!")

    return combined_entity_df

@st.cache_data
def stepFour(target_page):
    with st.spinner(f"Extract Entities for target page {target_page}:"):
        html = extract_html_via_api(target_page, has_data_api_key)
        content = extract_text_from_html(html)

        api_response = analyze_entities(content, google_nlp_engine_api_key)
        entity_df = get_entities_dataframe(api_response)

        st.write("Target Page Entities:")
        st.dataframe(entity_df)
        st.success("Entities extraction completed for target page!")

    return entity_df

@st.cache_data
def stepFive(entites_df, target_page_entity_df):
    with st.spinner("Analyzing entities across pages..."):
        # Extract top 30 entities for each link based on salience
        top_entities = (
            entites_df.sort_values(by="Salience", ascending=False)
            .groupby("Page Link")
            .head(30)
            .reset_index(drop=True)
        )

        # Flatten target page entities into a set for quick look-up
        target_entities_set = set(target_page_entity_df["Entity"])

        # Create a dictionary to count occurrences and track URLs
        entity_data = {}

        for idx, row in top_entities.iterrows():
            entity = row["Entity"]
            page_link = row["Page Link"]

            # Increment count and append URL for the entity
            if entity not in entity_data:
                entity_data[entity] = {"Count": 0, "URLs": set()}
            entity_data[entity]["Count"] += 1
            entity_data[entity]["URLs"].add(page_link)

        # Prepare the final DataFrame
        final_df_data = []
        for entity, data in entity_data.items():
            row_data = {
                "Entity": entity,
                "Count": data["Count"],
                "URLs": ", ".join(data["URLs"]),  # Convert set of URLs to a string
            }
            final_df_data.append(row_data)

        final_df = pd.DataFrame(final_df_data)

        final_df["Missed"] = final_df["Entity"].apply(
            lambda entity: entity not in target_entities_set
        )

    sorted_df = final_df.sort_values(by="Count", ascending=False)

    st.write("Final Entity Analysis:")

    def highlight_missed(s):
        return ['background-color: orange'] * len(s) if s.Missed * len(s) else [''] * len(s)

    st.dataframe(sorted_df.style.apply(highlight_missed, axis=1))

    st.success("Entity analysis completed!")

    return sorted_df

st.title('Page Content Gap Analyzer')

with st.form("setup"):
   st.write("Enter Page URL and Keyword for Analysis")
   page_url = st.text_input('Page URL')
   keyword = st.text_input('Keyword')

   st.write("Enter API Credentials")
   has_data_api_key = st.text_input('HasData API Key')
   google_nlp_engine_api_key = st.text_input('Google NLP Engine API Key')

   setup_form_submit = st.form_submit_button('Start Analysis')

if setup_form_submit and (page_url == '' or keyword == ''):
    raise ValueError('No Page URL or Keyword')

if setup_form_submit and (has_data_api_key == '' or google_nlp_engine_api_key == ''):
    raise ValueError('No HasData API Key or Google NLP Engine API Key')

if setup_form_submit:
    serp_results_df = stepOne(keyword)
    content_results_df = stepTwo(serp_results_df)
    entites_df = stepThree(content_results_df)
    target_page_entity_df = stepFour(page_url)
    final_entity_analysis_df = stepFive(entites_df, target_page_entity_df)
