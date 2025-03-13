import os
import requests
import warnings
import logging
import streamlit as st
from typing import List, Dict, Any
import pandas as pd
import io
from langchain.globals import set_verbose
from langchain_community.document_loaders import WebBaseLoader
from chains import Chain
from portfolio import Portfolio
from utils import clean_text
import re
from urllib.parse import urlparse
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Suppress specific warnings
warnings.filterwarnings("ignore", message="USER_AGENT environment variable not set")

# Constants
DEFAULT_USER_AGENT = "ColdEmailSynthesizer/1.0"
REQUIRED_COLUMNS = ['Techstack', 'Links']
DEFAULT_CONTEXT = """I am the founder and lead developer at QuantumCode Solutions, a boutique software development agency specializing in custom enterprise applications and digital transformation solutions. Over the past five years, we've helped more than 30 companies modernize their tech infrastructure and streamline operations through innovative software solutions. Our expertise spans from robust backend systems to intuitive user interfaces, with a particular focus on AI-driven analytics and cloud migration. We pride ourselves on delivering scalable, maintainable code that grows with our clients' businesses. Some of our notable clients include FinTech startups like PayStream and enterprise clients such as Global Logistics Inc. We're particularly interested in partnering with forward-thinking companies in the healthcare, finance, and logistics sectors who are looking to leverage technology as a competitive advantage."""

def initialize_session_state():
    """Initialize all session state variables."""
    if "USER_AGENT" not in st.session_state:
        os.environ["USER_AGENT"] = DEFAULT_USER_AGENT
        st.session_state.USER_AGENT_set = True
        logger.info(f"USER_AGENT set to: {os.getenv('USER_AGENT')}")
    
    # Initialize other session state variables
    defaults = {
        "context": "",
        "portfolio_data": None,
        "email_generation_triggered": False,
        "generation_history": [],
        "dark_mode": True
    }
    
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value


def is_valid_url(url: str) -> bool:
    """Validate if a string is a properly formatted URL."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc]) and result.scheme in ['http', 'https']
    except:
        return False


def validate_portfolio_data(df: pd.DataFrame) -> List[str]:
    """Validate the portfolio data format and content."""
    errors = []
    
    # Check columns
    if not all(col in df.columns for col in REQUIRED_COLUMNS):
        errors.append(f"File must have these columns: {', '.join(REQUIRED_COLUMNS)}")
        return errors
    
    # Check content
    for idx, row in df.iterrows():
        # Check for empty values
        if pd.isna(row['Techstack']) or pd.isna(row['Links']):
            errors.append(f"Row {idx + 1}: Empty values not allowed")
            continue
            
        # Validate tech stack format
        if ' | ' not in str(row['Techstack']):
            errors.append(f"Row {idx + 1}: Tech stack must contain technologies separated by ' | '")
        
        # Validate URL
        if not is_valid_url(str(row['Links'])):
            errors.append(f"Row {idx + 1}: Invalid URL format in '{row['Links']}'")
    
    return errors


def get_css_styles(dark_mode: bool = True) -> str:
    """Return CSS styles based on theme preference."""
    if dark_mode:
        return """
        <style>
        /* Base theme override */
        .stApp {
              background: hsla(270, 94%, 25%, 1);
              background: linear-gradient(135deg, hsla(270, 94%, 25%, 1) 20%, hsla(158, 94%, 49%, 1) 100%);
              background: -moz-linear-gradient(315deg, hsla(270, 94%, 25%, 1) 20%, hsla(158, 94%, 49%, 1) 100%);
              background: -webkit-linear-gradient(315deg, hsla(270, 94%, 25%, 1) 20%, hsla(158, 94%, 49%, 1) 100%);
        }
        
        /* Headers and text */
        h1, h2, h3 {
            color: #4CAF50 !important;
            font-family: 'Space Mono', monospace;
        }
        
        /* Input fields */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea {
            background: rgba(16, 24, 39, 0.8) !important;
            border: 1px solid rgba(138, 43, 226, 0.3) !important;
            color: #4CAF50 !important;
            border-radius: 10px !important;
        }
        
        .stTextInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus {
            border-color: #4CAF50 !important;
            box-shadow: 0 0 15px rgba(76, 175, 80, 0.3) !important;
        }
        
        /* Buttons */
        .stButton > button {
            background: linear-gradient(135deg, #4CAF50, #2196F3) !important;
            color: white !important;
            border: none !important;
            padding: 10px 20px !important;
            border-radius: 10px !important;
            transition: all 0.3s ease !important;
            transform: skew(-10deg) !important;
        }
        
        .stButton > button:hover {
            transform: skew(-10deg) translateY(-2px) !important;
            box-shadow: 0 0 20px rgba(76, 175, 80, 0.5) !important;
        }
        
        /* File uploader */
        .stUploadButton {
            background: rgba(16, 24, 39, 0.8) !important;
            border: 2px dashed rgba(76, 175, 80, 0.5) !important;
            border-radius: 10px !important;
            padding: 20px !important;
        }
        
        /* Data editor/table */
        .stDataFrame {
            background: rgba(16, 24, 39, 0.6) !important;
            border: 1px solid rgba(138, 43, 226, 0.2) !important;
            border-radius: 10px !important;
        }
        
        /* Tab styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background-color: transparent;
        }
        
        .stTabs [data-baseweb="tab"] {
            background-color: rgba(16, 24, 39, 0.8) !important;
            border-radius: 10px !important;
            border: 1px solid rgba(76, 175, 80, 0.3) !important;
            color: #4CAF50 !important;
            padding: 10px 20px !important;
        }
        
        .stTabs [aria-selected="true"] {
            background-color: rgba(76, 175, 80, 0.2) !important;
            border-color: #4CAF50 !important;
        }
        
        /* Success/Error messages */
        .stSuccess, .stError {
            background-color: rgba(16, 24, 39, 0.8) !important;
            border: 1px solid rgba(76, 175, 80, 0.3) !important;
            border-radius: 10px !important;
            color: #4CAF50 !important;
        }
        
        /* Code blocks */
        .stCodeBlock {
            background: rgba(16, 24, 39, 0.9) !important;
            border: 1px solid rgba(76, 175, 80, 0.3) !important;
            border-radius: 10px !important;
        }
        
        /* Context example box */
        .context-example {
            background: rgba(16, 24, 39, 0.8);
            border: 1px solid rgba(76, 175, 80, 0.3);
            border-radius: 10px;
            padding: 20px;
            margin: 10px 0;
            color: #4CAF50;
        }
        
        /* History item styling */
        .history-item {
            background: rgba(16, 24, 39, 0.7);
            border: 1px solid rgba(76, 175, 80, 0.2);
            border-radius: 10px;
            padding: 15px;
            margin: 10px 0;
        }
        
        .history-item h4 {
            color: #4CAF50;
            margin-top: 0;
        }
        
        /* Loading animation */
        .stSpinner {
            border-color: #4CAF50 !important;
        }
        
        /* Scrollbar */
        ::-webkit-scrollbar {
            width: 10px;
            background: transparent;
        }
        
        ::-webkit-scrollbar-thumb {
            background: rgba(76, 175, 80, 0.3);
            border-radius: 5px;
        }
        
        /* Alien glow effect for headers */
        @keyframes alienGlow {
            0% { text-shadow: 0 0 5px #4CAF50, 0 0 10px #4CAF50; }
            50% { text-shadow: 0 0 10px #4CAF50, 0 0 20px #4CAF50; }
            100% { text-shadow: 0 0 5px #4CAF50, 0 0 10px #4CAF50; }
        }
        
        h1 {
            animation: alienGlow 2s infinite;
        }
        </style>
        """
    else:
        # Light theme styles
        return """
        <style>
        /* Light theme */
        .stApp {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        }
        
        h1, h2, h3 {
            color: #2C3E50 !important;
            font-family: 'Roboto', sans-serif;
        }
        
        /* Input fields */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea {
            background: rgba(255, 255, 255, 0.9) !important;
            border: 1px solid rgba(44, 62, 80, 0.2) !important;
            color: #2C3E50 !important;
            border-radius: 8px !important;
        }
        
        /* Buttons */
        .stButton > button {
            background: linear-gradient(135deg, #3498DB, #2980B9) !important;
            color: white !important;
            border: none !important;
            border-radius: 8px !important;
            transition: all 0.3s ease !important;
        }
        
        /* Context example box */
        .context-example {
            background: rgba(255, 255, 255, 0.9);
            border: 1px solid rgba(44, 62, 80, 0.2);
            border-radius: 8px;
            padding: 20px;
            margin: 10px 0;
            color: #2C3E50;
        }
        
        /* History item styling */
        .history-item {
            background: rgba(255, 255, 255, 0.9);
            border: 1px solid rgba(44, 62, 80, 0.2);
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
        }
        
        .history-item h4 {
            color: #3498DB;
            margin-top: 0;
        }
        </style>
        """


def create_example_template() -> str:
    """Create an example CSV template for users to download."""
    template_data = """Techstack,Links
React | TypeScript | AWS Lambda,https://example.com/fintech-dashboard
Node.js | Express | MongoDB,https://example.com/logistics-tracking-system
Python | Django | PostgreSQL | Docker,https://example.com/healthcare-analytics-platform
React Native | Firebase | GraphQL,https://example.com/mobile-payment-app
Angular | .NET Core | Azure | SQL Server,https://example.com/enterprise-management-system
Vue.js | Laravel | MySQL | Redis,https://example.com/ecommerce-platform
Python | TensorFlow | AWS | Kubernetes,https://example.com/predictive-analytics-tool
Java | Spring Boot | Hibernate | Kafka,https://example.com/data-streaming-solution"""
    return template_data


def extract_and_generate_email(llm: Chain, portfolio: Portfolio, url: str, context: str) -> Dict[str, Any]:
    """Extract job data and generate email based on portfolio matches."""
    try:
        # Load and clean webpage content
        loader = WebBaseLoader([url])
        data = clean_text(loader.load()[0].page_content)
        
        logger.info(f"Successfully extracted data from URL: {url}")
        
        # Extract jobs from the data
        jobs = llm.extract_jobs(data)
        
        if not jobs:
            logger.warning(f"No jobs extracted from URL: {url}")
            return {"success": False, "error": "No jobs could be extracted from the provided URL."}
        
        results = []
        for job_index, job in enumerate(jobs):
            skills = job.get('skills', [])
            
            # Find matching portfolio items
            links = portfolio.query_links(skills)
            
            # Generate email
            email = llm.write_mail(job, links, context)
            
            job_result = {
                "job_title": job.get("title", f"Job {job_index+1}"),
                "skills": skills,
                "matching_links": links,
                "email": email
            }
            results.append(job_result)
        
        return {"success": True, "results": results}
        
    except Exception as e:
        logger.error(f"Error in extract_and_generate_email: {str(e)}")
        logger.error(traceback.format_exc())
        return {"success": False, "error": str(e), "traceback": traceback.format_exc()}


def display_generation_history(history: List[Dict[str, Any]]):
    """Display the history of generated emails."""
    if not history:
        st.info("No emails have been generated yet.")
        return
        
    for i, item in enumerate(history):
        with st.expander(f"Generation #{i+1}: {item.get('url', 'Unknown URL')}"):
            if item.get("success", False):
                for job_result in item.get("results", []):
                    st.markdown(f"#### {job_result.get('job_title', 'Job')}")
                    st.markdown("**Matched Skills:**")
                    st.write(", ".join(job_result.get("skills", [])))
                    st.markdown("**Portfolio Links Used:**")
                    st.write(", ".join(job_result.get("matching_links", [])))
                    st.markdown("**Generated Email:**")
                    st.code(job_result.get("email", ""), language='markdown')
            else:
                st.error(f"Failed: {item.get('error', 'Unknown error')}")


def create_streamlit_app(llm: Chain, portfolio: Portfolio, clean_text_func):
    """Main function to create the Streamlit application."""
    # Initialize session state
    initialize_session_state()
    
    # Set page config
    st.set_page_config(
        page_title="Cold Email Synthesizer", 
        page_icon="🌌", 
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Apply CSS theme
def create_streamlit_app(llm: Chain, portfolio: Portfolio, clean_text_func):
    """Main function to create the Streamlit application."""
    # Initialize session state
    initialize_session_state()
    
    # Set page config
    st.set_page_config(
        page_title="Cold Email Synthesizer", 
        page_icon="🌌", 
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Apply CSS theme
    st.markdown(get_css_styles(st.session_state.dark_mode), unsafe_allow_html=True)

    # App title and description
    st.markdown("<h1 style='text-align: center; font-size: 2.5em;'>🌌 Cold Email Synthesizer</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #4CAF50; font-size: 1.2em;'>GenAI-Enhanced Synthesizing Protocol</p>", unsafe_allow_html=True)

    # Sidebar for theme switch and other global settings
    with st.sidebar:
        st.markdown("### ⚙️ Global Settings")
        
        # Theme toggle
        theme_toggle = st.toggle("Enable Dark Mode", value=st.session_state.dark_mode)
        if theme_toggle != st.session_state.dark_mode:
            st.session_state.dark_mode = theme_toggle
            st.rerun()
            
        # Debug toggle
        debug_mode = st.toggle("Enable Debug Mode", value=False)
        if debug_mode:
            set_verbose(True)
        else:
            set_verbose(False)
            
        # Log metrics
        st.markdown("### 📊 Metrics")
        st.markdown(f"**Emails Generated:** {len(st.session_state.generation_history)}")
        if st.session_state.generation_history:
            last_gen = st.session_state.generation_history[-1].get('timestamp', 'Unknown')
            st.markdown(f"**Last Generation:** {last_gen}")

    # Create tabs with theme
    tab1, tab2, tab3 = st.tabs(["Configuration Matrix", "Email Synthesizer", "History"])

    # Configuration Matrix Tab
    with tab1:
        st.markdown("### Enter Your Context")
        
        # Example context
        if st.button("Use Example Context"):
            st.session_state.context = DEFAULT_CONTEXT
            st.rerun()
        
        st.markdown("""
        <div class="context-example">
        <strong>Context Guidelines:</strong>
        <ul>
        <li>Describe your company and its services</li>
        <li>Explain what makes your company unique</li>
        <li>Mention any notable achievements or clients</li>
        <li>Define your target audience</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)

        # Context input
        st.session_state.context = st.text_area(
            "Initialize Your Context",
            value=st.session_state.context,
            height=200,
            help="Describe your company, services, and how you want to present yourself in the cold emails",
            key="context_input"
        )
             
        st.markdown("### Upload Your Portfolio")
        st.markdown("Synchronize your Portfolio (in CSV format)")
        
        # Upload portfolio CSV
        col1, col2 = st.columns([3, 1])
        with col1:
            uploaded_file = st.file_uploader(
                "Initialize Data Transfer", 
                type=['csv'], 
                key="portfolio_upload"
            )
        
        with col2:
            st.download_button(
                label="Download Template",
                data=create_example_template(),
                file_name="portfolio_template.csv",
                mime="text/csv"
            )
        
        # Process uploaded portfolio
        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)
                errors = validate_portfolio_data(df)
                
                if errors:
                    st.error("Portfolio Synchronization Failed:")
                    for error in errors:
                        st.error(error)
                else:
                    st.success("Portfolio Successfully Integrated!")
                    
                    # Display and allow editing of the portfolio
                    st.markdown("### Portfolio Preview")
                    edited_df = st.data_editor(
                        df,
                        num_rows="dynamic",
                        use_container_width=True,
                        hide_index=True,
                        key="portfolio_editor"
                    )

                    # Save edited portfolio
                    if st.button("Commit Synchronization"):
                        st.session_state.portfolio_data = edited_df
                        st.success("Synchronization State Successfully Updated!")

            except Exception as e:
                st.error(f"Synchronization Error: {str(e)}")
                if debug_mode:
                    st.code(traceback.format_exc())

    # Email Synthesizer Tab
    with tab2:
        # Validation checks
        if not st.session_state.context:
            st.warning("Entity Parameters Not Initialized! Please enter your context in the Configuration Matrix tab.")
            st.stop()
            
        if st.session_state.portfolio_data is None:
            st.warning("Portfolio Not Synchronized! Please upload your portfolio data in the Configuration Matrix tab.")
            st.stop()

        # Load portfolio data
        try:
            portfolio.load_custom_portfolio(st.session_state.portfolio_data)
        except Exception as e:
            st.error(f"Portfolio Integration Error: {str(e)}")
            if debug_mode:
                st.code(traceback.format_exc())
            st.stop()

        # URL input
        st.markdown("### Target URL")
        url_input = st.text_input(
            "Enter Job Posting URL", 
            placeholder="https://example.com/job-posting",
            help="Input the URL of the job posting you want to analyze"
        )
        
        # Optional URL validation
        if url_input and not is_valid_url(url_input):
            st.warning("The URL format appears to be invalid. Please enter a valid URL starting with http:// or https://")
        
        # Generate email button
        col1, col2 = st.columns([1, 3])
        with col1:
            generate_email_button = st.button("🚀 Synthesize Email", use_container_width=True)
        
        # Process email generation
        if generate_email_button and url_input:
            with st.spinner('Initializing Cold Email Protocol...'):
                # Record start time for metrics
                import datetime
                start_time = datetime.datetime.now()
                
                # Generate email
                result = extract_and_generate_email(
                    llm, 
                    portfolio, 
                    url_input, 
                    st.session_state.context
                )
                
                # Calculate processing time
                processing_time = (datetime.datetime.now() - start_time).total_seconds()
                
                # Add to history
                result["url"] = url_input
                result["timestamp"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                result["processing_time"] = processing_time
                st.session_state.generation_history.append(result)
                
                # Display results
                if result["success"]:
                    st.success(f"Email synthesis completed in {processing_time:.2f} seconds!")
                    
                    # Display each job result
                    for job_result in result["results"]:
                        st.markdown(f"### 📧 Email for: {job_result.get('job_title', 'Job')}")
                        
                        # Display skills and links
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown("**Matched Skills:**")
                            st.write(", ".join(job_result.get("skills", [])))
                        with col2:
                            st.markdown("**Portfolio Links Used:**")
                            st.write(", ".join(job_result.get("matching_links", [])))
                        
                        # Display generated email
                        st.markdown("**Generated Email:**")
                        email_text = job_result.get("email", "")
                        st.code(email_text, language='markdown')
                        
                        # Add copy button
                        st.download_button(
                            label="📋 Copy Email",
                            data=email_text,
                            file_name="cold_email.txt",
                            mime="text/plain",
                            key=f"download_{job_result.get('job_title', 'job')}"
                        )
                else:
                    st.error(f"Email synthesis failed: {result.get('error', 'Unknown error')}")
                    if debug_mode and "traceback" in result:
                        st.code(result["traceback"])

    # History Tab
    with tab3:
        st.markdown("### 📜 Email Generation History")
        
        # Clear history button
        if st.session_state.generation_history:
            if st.button("🗑️ Clear History"):
                st.session_state.generation_history = []
                st.success("History cleared successfully!")
                st.rerun()
        
        # Display history
        display_generation_history(st.session_state.generation_history)


def main():
    """Main entry point for the application."""
    try:
        # Initialize components
        llm = Chain()
        portfolio = Portfolio()
        
        # Create and run the Streamlit app
        create_streamlit_app(llm, portfolio, clean_text)
        
    except Exception as e:
        st.error(f"Application Error: {str(e)}")
        st.error(traceback.format_exc())


if __name__ == "__main__":
    main()