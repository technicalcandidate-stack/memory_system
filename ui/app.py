"""Streamlit chat interface - Gemini style with chat sessions."""
import streamlit as st
import pandas as pd
import sys
from pathlib import Path
from sqlalchemy import text
from datetime import datetime
import uuid

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.executor import execute_with_retry
from config.settings import DEFAULT_COMPANY_ID
from config.database import get_db_session
from memory.conversation_memory import ConversationMemoryManager
from graph.orchestrator import MultiAgentOrchestrator

# Initialize global memory manager
if "memory_manager" not in st.session_state:
    st.session_state.memory_manager = ConversationMemoryManager()

# Page configuration
st.set_page_config(
    page_title="Insurance Intelligence",
    page_icon="",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Gemini-style Dark CSS
st.markdown("""
<style>
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Global dark background */
    .stApp {
        background-color: #121212 !important;
    }

    /* Main container */
    .main .block-container {
        padding-top: 3rem;
        max-width: 768px !important;
        padding-bottom: 10rem;
        background-color: #121212 !important;
    }

    /* Sidebar - Dark theme */
    [data-testid="stSidebar"] {
        background-color: #1e1e1e !important;
        padding: 1rem;
        border-right: 1px solid #3d3d3d;
    }

    [data-testid="stSidebar"] * {
        color: #e3e3e3 !important;
    }

    [data-testid="stSidebar"] > div:first-child {
        background-color: #1e1e1e !important;
    }

    /* New Chat Button - Dark style */
    .new-chat-container {
        margin-bottom: 1.5rem;
    }

    div[data-testid="stButton"] button {
        width: 100%;
        background-color: #2d2d2d !important;
        color: #e3e3e3 !important;
        border: none !important;
        border-radius: 24px !important;
        padding: 10px 20px !important;
        font-weight: 500 !important;
        font-size: 14px !important;
        transition: background-color 0.2s !important;
    }

    div[data-testid="stButton"] button:hover {
        background-color: #3d3d3d !important;
    }

    /* Chat sessions list */
    .chat-session-item {
        padding: 8px 12px;
        margin: 4px 0;
        border-radius: 8px;
        cursor: pointer;
        font-size: 13px;
        background-color: transparent;
        transition: background-color 0.2s;
    }

    .chat-session-item:hover {
        background-color: #2d2d2d;
    }

    .chat-session-item.active {
        background-color: #3d3d3d;
        font-weight: 500;
    }

    /* Main chat area background */
    .main {
        background-color: #121212;
    }

    /* All text in main area */
    .main * {
        color: #e3e3e3 !important;
    }

    /* Chat messages */
    [data-testid="stChatMessage"] {
        background-color: transparent !important;
        padding: 1.25rem 0 !important;
        border: none !important;
    }

    /* User message bubble */
    [data-testid="stChatMessage"][data-testid*="user"] {
        background-color: #2d2d2d !important;
        border-radius: 20px !important;
        padding: 12px 16px !important;
        margin-left: 20% !important;
    }

    /* Assistant message */
    [data-testid="stChatMessage"][data-testid*="assistant"] {
        background-color: transparent !important;
        padding: 12px 0 !important;
    }

    /* Chat input - Dark style */
    .stChatInput {
        border-top: 1px solid #3d3d3d !important;
        padding-top: 1rem !important;
        background-color: #121212 !important;
    }

    .stChatInput textarea {
        border-radius: 24px !important;
        border: 1px solid #3d3d3d !important;
        padding: 12px 20px !important;
        font-size: 14px !important;
        background-color: #1e1e1e !important;
        color: #e3e3e3 !important;
    }

    .stChatInput textarea:focus {
        border-color: #4a8cf7 !important;
        box-shadow: 0 0 0 1px #4a8cf7 !important;
    }

    /* Expanders */
    .streamlit-expanderHeader {
        font-size: 13px !important;
        color: #b3b3b3 !important;
        border-radius: 8px !important;
        padding: 8px 12px !important;
        background-color: #1e1e1e !important;
        border: 1px solid #3d3d3d !important;
    }

    .streamlit-expanderHeader:hover {
        background-color: #2d2d2d !important;
    }

    /* Expander content */
    .streamlit-expanderContent {
        background-color: #1e1e1e !important;
        border: 1px solid #3d3d3d !important;
        color: #e3e3e3 !important;
    }

    /* Download button */
    .stDownloadButton button {
        background-color: #4a8cf7 !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 20px !important;
        padding: 8px 20px !important;
        font-weight: 500 !important;
        font-size: 13px !important;
    }

    .stDownloadButton button:hover {
        background-color: #3a7ce0 !important;
    }

    /* Welcome screen */
    .welcome-container {
        text-align: center;
        padding: 4rem 2rem;
    }

    .welcome-title {
        font-size: 2rem;
        font-weight: 400;
        color: #e3e3e3;
        margin-bottom: 1rem;
    }

    .welcome-subtitle {
        font-size: 1rem;
        color: #b3b3b3;
        margin-bottom: 2rem;
    }

    /* Company selector */
    [data-testid="stSidebar"] .stSelectbox {
        margin-bottom: 1rem;
    }

    /* Selectbox styling */
    [data-testid="stSidebar"] .stSelectbox > div > div {
        background-color: #2d2d2d !important;
        color: #e3e3e3 !important;
        border: 1px solid #3d3d3d !important;
    }

    /* Dividers */
    hr {
        border: none !important;
        border-top: 1px solid #3d3d3d !important;
        margin: 1rem 0 !important;
    }

    /* Sidebar sections */
    .sidebar-section {
        margin-bottom: 1.5rem;
    }

    .sidebar-section-title {
        font-size: 11px;
        font-weight: 600;
        color: #b3b3b3;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 0.5rem;
        padding: 0 12px;
    }

    /* Code blocks */
    pre {
        background-color: #1e1e1e !important;
        border: 1px solid #3d3d3d !important;
    }

    code {
        color: #e3e3e3 !important;
        background-color: #1e1e1e !important;
    }

    /* Dataframe */
    [data-testid="stDataFrame"] {
        background-color: #1e1e1e !important;
    }

    [data-testid="stDataFrame"] * {
        color: #e3e3e3 !important;
    }

    /* Markdown content */
    .stMarkdown {
        color: #e3e3e3 !important;
    }

    /* Success/Error/Warning messages */
    .stSuccess {
        background-color: #1e3a1e !important;
        color: #90ee90 !important;
    }

    .stError {
        background-color: #3a1e1e !important;
        color: #ff6b6b !important;
    }

    .stWarning {
        background-color: #3a3a1e !important;
        color: #ffd700 !important;
    }

    .stInfo {
        background-color: #1e2a3a !important;
        color: #87ceeb !important;
    }

    /* Spinner */
    .stSpinner > div {
        border-top-color: #4a8cf7 !important;
    }

    /* Force all containers to dark background */
    section[data-testid="stSidebar"] > div {
        background-color: #1e1e1e !important;
    }

    [data-testid="stAppViewContainer"] {
        background-color: #121212 !important;
    }

    [data-testid="stHeader"] {
        background-color: #121212 !important;
    }

    [data-testid="stToolbar"] {
        background-color: #121212 !important;
    }

    /* All divs in main area */
    .main > div {
        background-color: #121212 !important;
    }

    /* Ensure chat message containers have consistent background */
    [data-testid="stVerticalBlock"] {
        background-color: transparent !important;
    }

    /* Chat message content background */
    [data-testid="stChatMessageContent"] {
        background-color: transparent !important;
    }

    /* Input area background */
    [data-testid="InputInstructions"] {
        background-color: #121212 !important;
    }

    /* Dropdown menus dark theme */
    [data-testid="stSelectbox"] div[data-baseweb="select"] {
        background-color: #2d2d2d !important;
    }

    /* Dropdown menu items */
    [role="listbox"] {
        background-color: #2d2d2d !important;
    }

    [role="option"] {
        background-color: #2d2d2d !important;
        color: #e3e3e3 !important;
    }

    [role="option"]:hover {
        background-color: #3d3d3d !important;
    }

    /* Spinner background */
    [data-testid="stStatusWidget"] {
        background-color: #121212 !important;
    }

    /* All text color override */
    p, span, div, label, h1, h2, h3, h4, h5, h6 {
        color: #e3e3e3 !important;
    }

    /* Button text specifically */
    button span {
        color: #e3e3e3 !important;
    }

    /* Expander arrow color */
    [data-testid="stExpander"] details summary svg {
        color: #b3b3b3 !important;
    }

    /* Fix chat input container background */
    [data-testid="stBottom"] {
        background-color: #121212 !important;
    }

    [data-testid="stBottom"] > div {
        background-color: #121212 !important;
    }

    /* Fix any remaining background color issues */
    section[data-testid="stMain"] {
        background-color: #121212 !important;
    }

    section[data-testid="stMain"] > div {
        background-color: #121212 !important;
    }

    /* Ensure bottom area matches */
    .stChatFloatingInputContainer {
        background-color: #121212 !important;
    }

    /* Fix bottom padding area */
    [data-testid="stChatInput"] > div {
        background-color: #121212 !important;
    }
</style>
""", unsafe_allow_html=True)

# Function to load companies
@st.cache_data(ttl=600)
def load_companies():
    """Load list of companies from database."""
    try:
        session = get_db_session()
        portfolio_ids = [29447, 29430, 29354, 29322, 29270, 29263, 29230, 29088, 29057, 29000,
                        28956, 28952, 28880, 28811, 29626, 29618, 29610, 29594, 29576, 29565,
                        29564, 29604, 29595, 29560, 29548, 29546, 29525]

        query = text("""
            SELECT id, company_name
            FROM public.companies
            WHERE id = ANY(:ids)
            ORDER BY company_name
        """)

        result = session.execute(query, {"ids": portfolio_ids})
        companies = [{"id": row[0], "name": row[1] or f"Company {row[0]}"} for row in result]
        session.close()
        return companies
    except Exception as e:
        return [{"id": DEFAULT_COMPANY_ID, "name": "Guardian Families Homecare LLC"}]

# Initialize session state
if "chat_sessions" not in st.session_state:
    st.session_state.chat_sessions = {}
if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = None
if "current_company_id" not in st.session_state:
    st.session_state.current_company_id = DEFAULT_COMPANY_ID

def create_new_chat_session(company_id):
    """Create a new chat session."""
    session_id = str(uuid.uuid4())
    st.session_state.chat_sessions[session_id] = {
        "id": session_id,
        "company_id": company_id,
        "messages": [],
        "created_at": datetime.now(),
        "title": "New Chat"
    }
    st.session_state.current_session_id = session_id

    # Initialize LangChain memory for this session
    st.session_state.memory_manager.get_memory(session_id)

    return session_id

def get_session_title(session):
    """Get a title for the chat session based on first message."""
    if session["messages"]:
        first_user_msg = next((m for m in session["messages"] if m["role"] == "user"), None)
        if first_user_msg:
            title = first_user_msg["content"][:40]
            return title + "..." if len(first_user_msg["content"]) > 40 else title
    return "New Chat"

# Sidebar
with st.sidebar:
    st.markdown("### Insurance Intelligence")
    st.markdown("")

    # New Chat button
    if st.button("✨ New Chat", key="new_chat_btn"):
        companies = load_companies()
        company_options = {comp['name']: comp['id'] for comp in companies}
        default_company_name = next(
            (comp['name'] for comp in companies if comp['id'] == DEFAULT_COMPANY_ID),
            list(company_options.keys())[0] if company_options else None
        )
        if default_company_name:
            company_id = company_options[default_company_name]
            create_new_chat_session(company_id)
            st.rerun()

    st.markdown("---")

    # Company selector
    st.markdown('<div class="sidebar-section-title">Select Company</div>', unsafe_allow_html=True)
    companies = load_companies()
    company_options = {comp['name']: comp['id'] for comp in companies}

    default_company_name = next(
        (comp['name'] for comp in companies if comp['id'] == st.session_state.current_company_id),
        list(company_options.keys())[0] if company_options else None
    )

    selected_company_name = st.selectbox(
        "Company",
        options=list(company_options.keys()),
        index=list(company_options.keys()).index(default_company_name) if default_company_name in company_options else 0,
        label_visibility="collapsed",
        key="company_selector"
    )

    company_id = company_options[selected_company_name]

    # If company changed, update current session or create new one
    if company_id != st.session_state.current_company_id:
        st.session_state.current_company_id = company_id
        if st.session_state.current_session_id:
            st.session_state.chat_sessions[st.session_state.current_session_id]["company_id"] = company_id

    st.markdown("---")

    # Chat sessions list
    if st.session_state.chat_sessions:
        st.markdown('<div class="sidebar-section-title">Recent Chats</div>', unsafe_allow_html=True)

        # Sort sessions by creation time (newest first)
        sorted_sessions = sorted(
            st.session_state.chat_sessions.values(),
            key=lambda x: x["created_at"],
            reverse=True
        )

        for session in sorted_sessions[:10]:  # Show last 10 chats
            session_title = get_session_title(session)
            is_active = session["id"] == st.session_state.current_session_id

            if st.button(
                f"💬 {session_title}",
                key=f"session_{session['id']}",
                use_container_width=True,
                type="primary" if is_active else "secondary"
            ):
                st.session_state.current_session_id = session["id"]
                st.session_state.current_company_id = session["company_id"]
                st.rerun()

# Main chat area
if not st.session_state.current_session_id or st.session_state.current_session_id not in st.session_state.chat_sessions:
    # Welcome screen - no active session
    st.markdown("""
        <div class="welcome-container">
            <div class="welcome-title"> Insurance Intelligence</div>
            <div class="welcome-subtitle">Ask questions about your accounts in natural language</div>
        </div>
    """, unsafe_allow_html=True)

    # Auto-create first session on first message
else:
    # Display current session
    current_session = st.session_state.chat_sessions[st.session_state.current_session_id]

    # Display chat history
    for message in current_session["messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask a question..."):
    # Create session if none exists
    if not st.session_state.current_session_id:
        create_new_chat_session(company_id)
        current_session = st.session_state.chat_sessions[st.session_state.current_session_id]
    else:
        current_session = st.session_state.chat_sessions[st.session_state.current_session_id]

    # Add user message
    current_session["messages"].append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # Get conversation history from LangChain memory
                conversation_history = st.session_state.memory_manager.get_conversation_history(
                    current_session["id"]
                )

                # Use MultiAgentOrchestrator for routing between SQL and Document agents
                orchestrator = MultiAgentOrchestrator(company_id=current_session["company_id"])
                result = orchestrator.process_query(
                    user_question=prompt,
                    session_id=current_session["id"],
                    conversation_history=conversation_history
                )
            except Exception as e:
                st.error(f"Error executing query: {str(e)}")
                import traceback
                st.code(traceback.format_exc(), language="python")
                result = {
                    "success": False,
                    "error": str(e),
                    "sql": "",
                    "natural_response": f"An error occurred: {str(e)}"
                }

        if result["success"]:
            # Natural language response
            if "natural_response" in result and result["natural_response"]:
                st.markdown(result["natural_response"])

            # Trajectory - show the LLM's thinking process
            if "trajectory" in result and result["trajectory"]:
                with st.expander("🧠 Agent Trajectory (LLM Thinking Process)"):
                    traj = result["trajectory"]

                    # Agent Routing Decision
                    st.markdown("### 🔀 Agent Routing")
                    route = traj.get('route_decision', 'unknown')
                    route_emoji = {"sql_only": "💾", "document_search": "📄", "hybrid": "🔀", "unknown": "❓"}
                    st.markdown(f"**Route:** {route_emoji.get(route, '❓')} `{route}`")

                    # Execution Path - which agents were invoked
                    exec_path = traj.get('execution_path', [])
                    if exec_path:
                        path_display = " → ".join(exec_path)
                        st.markdown(f"**Execution Path:** {path_display}")

                    st.markdown("---")

                    # Detected Skill (for SQL agent)
                    st.markdown(f"**🎯 Detected Skill:** {traj.get('detected_skill', 'N/A')}")
                    st.markdown(f"**🔄 Attempts:** {traj.get('attempts', 'N/A')}")
                    st.markdown(f"**📊 Rows Returned:** {traj.get('rows_returned', 'N/A')}")

                    st.markdown("---")
                    st.markdown("**💭 LLM Reasoning (Why these tables/columns):**")
                    st.markdown(f"> {traj.get('reasoning', 'N/A')}")

                    st.markdown("---")
                    st.markdown("**📖 LLM Explanation (What the query does):**")
                    st.markdown(f"> {traj.get('explanation', 'N/A')}")

                    st.markdown("---")
                    st.markdown("**🔍 Generated SQL Query:**")
                    st.code(traj.get('sql_generated', 'N/A'), language="sql")

            # Query details
            if "metadata_summary" in result and result["metadata_summary"]:
                with st.expander("📋 Query Details"):
                    st.markdown(result["metadata_summary"])

            # SQL
            with st.expander("📝 View SQL"):
                st.code(result["sql"], language="sql")

            # Raw data
            if result["results"]:
                with st.expander(f"📊 Raw Data ({len(result['results'])} rows)"):
                    df = pd.DataFrame(result["results"])
                    st.dataframe(df, use_container_width=True)

                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name=f"results_{current_session['company_id']}.csv",
                        mime="text/csv"
                    )

            response_text = result.get("natural_response", "Query completed.")
        else:
            # Error
            st.error("I couldn't answer that question.")
            if result.get("natural_response"):
                st.markdown(result["natural_response"])

            with st.expander("🔍 Debug Info"):
                st.warning(f"**Error:** {result['error']}")
                if result["sql"]:
                    st.code(result["sql"], language="sql")

            response_text = result.get("natural_response", "Error occurred.")

        # Save to session
        current_session["messages"].append({
            "role": "assistant",
            "content": response_text
        })

        # Update LangChain memory
        st.session_state.memory_manager.add_exchange(
            current_session["id"],
            prompt,
            response_text
        )

        # Update session title if first message
        if len(current_session["messages"]) == 2:  # First Q&A
            current_session["title"] = get_session_title(current_session)