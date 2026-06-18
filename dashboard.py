import streamlit as st
import os
import pandas as pd
import database
import analyzer
import requests

st.set_page_config(page_title="ATR Intelligence (Local)", layout="wide", page_icon="🏢")

# Initialize DB
if 'db_initialized' not in st.session_state:
    database.init_db()
    st.session_state['db_initialized'] = True

# Custom CSS
st.markdown("""
<style>
    .success-card { background-color: #0d2b1d; color: #e2e8f0; padding: 15px; border-radius: 8px; border: 1px solid #22c55e; margin-bottom: 10px; }
    .metric-container { background-color: #1e293b; padding: 10px; border-radius: 8px; text-align: center; border: 1px solid #334155; }
    .stButton>button { width: 100%; background-color: #22c55e; color: #ffffff; font-weight: bold; }
    .stButton>button:hover { background-color: #16a34a; color: #ffffff; }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("https://www.india.gov.in/sites/upload_files/npi/files/logo.png", width=150) # Use a more stable government logo or local fallback
    st.header("🤖 Local Intelligence")
    
    app_mode = st.radio("Analysis Mode", ["General Intelligence", "Vigilance Angle Identification", "DARPG Pendency Resolution"])
    ai_provider = st.selectbox("AI Provider", ["Google Gemini", "Groq (Llama 3)"])
    

    # API Key Input
    provider_name = "Gemini" if ai_provider == "Google Gemini" else "Groq"
    api_key = st.text_input(f"{provider_name} API Key", value=os.environ.get(f"{provider_name.upper()}_API_KEY", ""), type="password", help=f"Enter your personal {provider_name} API Key")
    uploaded_files = st.file_uploader("Upload ATR PDFs", type=["pdf"], accept_multiple_files=True)
    
    if st.button("📡 Test Connection"):
        try:
            if ai_provider == "Google Gemini":
                url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
                resp = requests.get(url, timeout=5)
            else:
                url = "https://api.groq.com/openai/v1/models"

                headers = {"Authorization": f"Bearer {api_key}"}
                resp = requests.get(url, headers=headers, timeout=5)
                
            if resp.status_code == 200:
                st.success(f"Connected! {provider_name} API Valid.")
            else:
                st.error(f"Error {resp.status_code}: {resp.text}")
        except Exception as e:
            st.error(f"Connection Failed: {e}")

    st.divider()

    if st.button("🗑️ Clear Database Data"):
        database.clear_db()
        st.success("Database cleared!")
        st.rerun()

    st.divider()
    
    if st.button("🚀 Start Batch Analysis"):
        if not uploaded_files:
            st.error("Please upload at least one PDF file.")
        else:
            st.info(f"Queued {len(uploaded_files)} files...")
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Ensure DB is ready
            database.init_db()
            
            import tempfile
            with tempfile.TemporaryDirectory() as tmpdirname:
                for i, uploaded_file in enumerate(uploaded_files):
                    filename = uploaded_file.name
                    filepath = os.path.join(tmpdirname, filename)
                    
                    # Save uploaded file to temp directory
                    with open(filepath, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                        
                    status_text.text(f"Processing: {filename}")
                    
                    # Run Analysis depending on mode
                    prov_key = "gemini" if ai_provider == "Google Gemini" else "groq"
                    
                    if app_mode == "General Intelligence":
                        result = analyzer.analyze_atr(filepath, api_key=api_key, provider=prov_key)
                        if result.get("status") == "error":
                            st.error(f"Error processing {filename}: {result.get('error')}")
                            continue
                        database.save_result(filename, result)
                    elif app_mode == "Vigilance Angle Identification":
                        result = analyzer.analyze_vigilance(filepath, api_key=api_key, provider=prov_key)
                        if result.get("status") == "error":
                            st.error(f"Error processing {filename}: {result.get('error')}")
                            continue
                        database.save_vigilance_result(filename, result)
                    else:
                        result = analyzer.analyze_darpg_routing(filepath, api_key=api_key, provider=prov_key)
                        if result.get("status") == "error":
                            st.error(f"Error processing {filename}: {result.get('error')}")
                            continue
                        database.save_routing_result(filename, result)
                    
                    progress_bar.progress((i + 1) / len(uploaded_files))
            
            status_text.success("Batch Processing Complete!")
            # We don't rerun immediately so the user can read the error messages.
            # They can refresh or click another button to clear.

# Main Area
if app_mode == "General Intelligence":
    st.title("🏛️ Grievance Intelligence (Gemini API)")

    database.init_db()
    df = database.get_all_results()

    if df.empty:
        st.info("👋 Welcome! Ensure your Gemini API Key is valid in the sidebar, then click 'Start Batch Analysis'.")
    else:
        # Top Stats
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1: st.metric("Files Analyzed", len(df))
        with c2: st.metric("Success Stories", len(df[df['is_success_story'] == 1]))
        with c3: 
            if 'grievance_type' in df.columns:
                st.metric("Suggestions/Reqs", len(df[df['grievance_type'].isin(['Suggestion', 'Request'])]))
            else:
                st.metric("Avg Desks", f"{df['desk_count'].mean():.1f}")
        with c4: st.metric("Avg Desks", f"{df['desk_count'].mean():.1f}")
        with c5: st.metric("Avg Ping-Pongs", f"{df['ping_pong_count'].mean():.1f}")

        st.divider()

        # Success Stories
        st.subheader("✨ Success Stories")
        success_df = df[df['is_success_story'] == 1]
        
        if len(success_df) > 0:
            for _, row in success_df.iterrows():
                with st.container():
                    # Use headline if available, else ID
                    title = row['success_headline'] if pd.notna(row.get('success_headline')) and row['success_headline'] else f"✅ {row['grievance_id']}"
                    
                    # Narrative only
                    narrative = row['success_narrative'] if pd.notna(row.get('success_narrative')) else "Narrative not available."

                    st.markdown(f"""
                    <div class="success-card">
                        <h4>{title}</h4>
                        <p>{narrative}</p>
                        <p style="font-size: 0.8em; color: #cbd5e1; margin-top: 10px;">ID: {row['grievance_id']} | Desk Count: {row['desk_count']}</p>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.caption("No success stories identified yet.")

        # Intelligent Summaries Viewer
        st.divider()
        st.subheader("🧠 Intelligent Summaries Viewer")
        
        valid_ids = df[df['grievance_id'].notna()]['grievance_id'].unique()
        if len(valid_ids) > 0:
            selected_id = st.selectbox("Select a Grievance ID to view intelligence", valid_ids)
            selected_row = df[df['grievance_id'] == selected_id].iloc[0]
            
            st.markdown("#### 🗣️ Citizen Request")
            issue_text = selected_row.get('intelligent_issue_summary')
            st.info(issue_text if pd.notna(issue_text) and issue_text else "Not available.")
            
            st.markdown("#### 👮 Officer Action (Last Remarks)")
            officer_text = selected_row.get('intelligent_officer_summary')
            st.success(officer_text if pd.notna(officer_text) and officer_text else "Not available.")
            
            st.markdown("#### ⭐ Citizen Feedback")
            feedback_text = selected_row.get('intelligent_citizen_feedback_summary')
            st.warning(feedback_text if pd.notna(feedback_text) and feedback_text else "Not available.")
            
            st.divider()
            st.markdown("#### 🔍 Extra Insights")
            
            c1, c2, c3 = st.columns(3)
            with c1:
                st.write("**Sentiments**")
                st.caption(f"Citizen Initial: {selected_row.get('citizen_sentiment', 'N/A')}")
                st.caption(f"Officer Tone: {selected_row.get('officer_tone', 'N/A')}")
                st.caption(f"Citizen Feedback: {selected_row.get('citizen_feedback_sentiment', 'N/A')}")
            with c2:
                st.write("**Delay Analysis**")
                st.caption(f"Root Cause: {selected_row.get('delay_root_cause', 'N/A')}")
                st.caption(f"Jurisdiction Accuracy: {selected_row.get('jurisdiction_accuracy', 'N/A')}")
                
            with c3:
                st.write("**Classification**")
                st.caption(f"Theme: {selected_row.get('standardized_theme', 'N/A')}")
                urg = selected_row.get('urgency_score')
                urg_str = f"{urg}/5" if pd.notna(urg) else "N/A"
                st.caption(f"Urgency Score: {urg_str}")
            
            sys_issue = selected_row.get('is_systemic_issue')
            if pd.notna(sys_issue) and sys_issue == 1.0: # sqlite booleans are often floats/ints in pd
                st.error(f"🚨 **Systemic Issue Flagged:** {selected_row.get('policy_recommendation', 'No recommendation provided.')}")
        else:
            st.caption("No grievance IDs available to display summaries.")

        # Data Table
        st.divider()
        st.subheader("📋 Detailed Registry")
        columns_to_show = [
            'grievance_id', 'status', 'grievance_type', 'has_attachment', 'is_success_story', 'desk_count', 
            'bottleneck_desk', 'resolved_desk', 'citizen_feedback', 'ping_pong_desks',
            'standardized_theme', 'urgency_score', 'is_systemic_issue',
            'intelligent_issue_summary', 'intelligent_officer_summary'
        ]
        # Filter only existing columns just in case
        columns_to_show = [c for c in columns_to_show if c in df.columns]

        c_exp1, c_exp2 = st.columns([4, 1])
        with c_exp1:
            st.caption("Review extracted data below. You can download this table for detailed reporting.")
        with c_exp2:
            import io
            try:
                buffer = io.BytesIO()
                df[columns_to_show].to_excel(buffer, index=False)
                st.download_button(
                    label="📥 Download as Excel",
                    data=buffer.getvalue(),
                    file_name="general_intelligence.xlsx",
                    mime="application/vnd.ms-excel"
                )
            except ImportError:
                csv_data = df[columns_to_show].to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download as CSV",
                    data=csv_data,
                    file_name="general_intelligence.csv",
                    mime="text/csv"
                )

        st.dataframe(
            df[columns_to_show],
            use_container_width=True
        )

elif app_mode == "Vigilance Angle Identification":
    st.title("🕵️ Vigilance Angle Identification")

    database.init_db()
    df = database.get_all_results()
    
    if df.empty or 'is_vigilance' not in df.columns:
        st.info("👋 Welcome! Ensure your Gemini API Key is valid in the sidebar, then click 'Start Batch Analysis' to check for vigilance angles.")
    else:
        valid_df = df[df['is_vigilance'].notna()]
        
        c1, c2, c3 = st.columns(3)
        with c1: st.metric("Files Analyzed for Vigilance", len(valid_df))
        with c2: st.metric("Vigilance Cases Identified (Yes)", len(valid_df[valid_df['is_vigilance'].astype(str).str.lower() == 'yes']))
        with c3: st.metric("Not Vigilance Cases (No)", len(valid_df[valid_df['is_vigilance'].astype(str).str.lower() == 'no']))

        st.divider()
        st.subheader("🕵️ Vigilance Analysis Results")
        
        if len(valid_df) > 0:
            for _, row in valid_df.iterrows():
                is_vig = str(row['is_vigilance']).strip().capitalize()
                color = "#dc2626" if is_vig == "Yes" else "#16a34a" # Red for vigilance, Green for no vigilance
                
                st.markdown(f'''
                <div style="background-color: #1e293b; color: #e2e8f0; padding: 15px; border-radius: 8px; border: 1px solid {color}; margin-bottom: 10px;">
                    <h4>ID: {row["grievance_id"]}</h4>
                    <p><strong>Vigilance Angle:</strong> <span style="color: {color}; font-weight: bold;">{is_vig}</span></p>
                    <p><strong>Reasoning:</strong> {row["vigilance_reasoning"]}</p>
                </div>
                ''', unsafe_allow_html=True)
        else:
            st.info("No vigilance analysis performed yet. Go to sidebar and Start Batch Analysis under this mode.")

elif app_mode == "DARPG Pendency Resolution":
    st.title("🏛️ DARPG Pendency Resolution")

    database.init_db()
    df = database.get_all_results()
    
    if df.empty or 'routing_action' not in df.columns:
        st.info("👋 Welcome! Ensure your Gemini API Key is valid in the sidebar, then click 'Start Batch Analysis' to run DARPG routing analysis.")
    else:
        valid_df = df[df['routing_action'].notna()]
        
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1: st.metric("Analyzed", len(valid_df))
        with c2: st.metric("DARPG (Dispose)", len(valid_df[valid_df['routing_action'].astype(str).str.lower() == 'dispose']))
        with c3: st.metric("Transfers", len(valid_df[valid_df['routing_action'].astype(str).str.lower() == 'transfer']))
        
        # SQLite booleans usually come back as 1.0 or 0.0 or True/False in pandas depending on driver
        ping_pongs = valid_df[valid_df['is_ping_pong_flag'] == True] if valid_df['is_ping_pong_flag'].dtype == bool else valid_df[valid_df['is_ping_pong_flag'] == 1]
        negligence = valid_df[valid_df['negligence_flag'] == True] if valid_df['negligence_flag'].dtype == bool else valid_df[valid_df['negligence_flag'] == 1]
        
        with c4: st.metric("Ping-Pong Flags", len(ping_pongs))
        with c5: st.metric("Negligence Flags", len(negligence))

        st.divider()
        
        cols_to_export = [
            'grievance_id', 'grievance_type', 'has_attachment', 'complainant_name', 'routing_action', 'transfer_to_dept',
            'draft_atr_remarks', 'is_ping_pong_flag', 'negligence_flag',
            'desk_count', 'ping_pong_count', 'delay_root_cause', 'standardized_theme', 'urgency_score'
        ]
        cols_to_export = [c for c in cols_to_export if c in valid_df.columns]
        
        export_df = valid_df[cols_to_export]
        
        st.subheader("📋 Routing & Resolution Data")
        
        c1, c2 = st.columns([4, 1])
        with c1:
            st.caption("Review extracted data below. You can download this table for detailed reporting.")
        with c2:
            import io
            try:
                buffer = io.BytesIO()
                export_df.to_excel(buffer, index=False)
                st.download_button(
                    label="📥 Download as Excel",
                    data=buffer.getvalue(),
                    file_name="darpg_routing_analysis.xlsx",
                    mime="application/vnd.ms-excel"
                )
            except ImportError:
                csv_data = export_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download as CSV (Missing openpyxl)",
                    data=csv_data,
                    file_name="darpg_routing_analysis.csv",
                    mime="text/csv"
                )

        st.dataframe(export_df, use_container_width=True)
