"""Streamlit chat interface - Gemini style with chat sessions."""
import streamlit as st
import streamlit_modal as modal
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

    /* Sidebar text color */
    [data-testid="stSidebar"] * {
        color: #e3e3e3 !important;
    }

    /* Main area buttons - not sidebar */
    .main div[data-testid="stButton"] button {
        background-color: #2d2d2d !important;
        color: #e3e3e3 !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 10px 20px !important;
        font-weight: 500 !important;
        font-size: 14px !important;
        transition: background-color 0.2s !important;
    }

    .main div[data-testid="stButton"] button:hover {
        background-color: #3d3d3d !important;
    }

    .main div[data-testid="stButton"] button[kind="primary"] {
        background-color: #4a8cf7 !important;
    }

    .main div[data-testid="stButton"] button[kind="primary"]:hover {
        background-color: #3a7ce0 !important;
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
        display: none;
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

    /* ==================== ChatGPT-Style Sidebar ==================== */

    /* Sidebar base - darker background like ChatGPT */
    [data-testid="stSidebar"] {
        background-color: #171717 !important;
        padding: 0 !important;
        border-right: none !important;
    }

    [data-testid="stSidebar"] > div:first-child {
        background-color: #171717 !important;
        padding: 12px 12px 0 12px !important;
    }

    /* New Chat Button - ChatGPT style with border */
    [data-testid="stSidebar"] > div > div > div > div > button:first-of-type {
        background-color: transparent !important;
        border: 1px solid #3d3d3d !important;
        border-radius: 8px !important;
        padding: 12px 16px !important;
        margin: 8px 0 !important;
        width: 100% !important;
        text-align: left !important;
        font-size: 14px !important;
        font-weight: 400 !important;
        color: #e3e3e3 !important;
        transition: background-color 0.15s ease !important;
    }

    [data-testid="stSidebar"] > div > div > div > div > button:first-of-type:hover {
        background-color: #2d2d2d !important;
    }

    /* Chats section header */
    .chats-header {
        font-size: 12px;
        font-weight: 500;
        color: #8e8ea0 !important;
        padding: 16px 12px 8px 12px;
        text-transform: none;
        letter-spacing: 0;
    }

    /* Chat list container - full width */
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
        gap: 2px !important;
    }

    /* Chat session container - single box style */
    [data-testid="stSidebar"] [data-testid="stHorizontalBlock"] {
        gap: 0 !important;
        margin: 2px 8px !important;
        padding: 0 !important;
        background-color: transparent !important;
        border-radius: 8px !important;
        overflow: hidden !important;
    }

    [data-testid="stSidebar"] [data-testid="stHorizontalBlock"]:hover {
        background-color: #212121 !important;
    }

    /* Active session - slightly lighter background */
    [data-testid="stSidebar"] [data-testid="stHorizontalBlock"]:has(button[kind="primary"]) {
        background-color: #2a2a2a !important;
    }

    /* Session name button - takes most of the space */
    [data-testid="stSidebar"] [data-testid="stHorizontalBlock"] > div:first-child {
        flex: 1 !important;
        min-width: 0 !important;
    }

    [data-testid="stSidebar"] [data-testid="stHorizontalBlock"] > div:first-child button {
        background-color: transparent !important;
        border: none !important;
        border-radius: 0 !important;
        padding: 8px 10px !important;
        font-size: 12px !important;
        font-weight: 400 !important;
        color: #b3b3b3 !important;
        text-align: left !important;
        transition: none !important;
        width: 100% !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
    }

    [data-testid="stSidebar"] [data-testid="stHorizontalBlock"] > div:first-child button:hover {
        background-color: transparent !important;
    }

    /* Active session text color */
    [data-testid="stSidebar"] [data-testid="stHorizontalBlock"] > div:first-child button[kind="primary"] {
        background-color: transparent !important;
        color: #e3e3e3 !important;
        font-weight: 400 !important;
    }

    /* Menu button (⋮) - inside the box */
    [data-testid="stSidebar"] [data-testid="stHorizontalBlock"] > div:last-child {
        flex: 0 0 auto !important;
        width: auto !important;
    }

    [data-testid="stSidebar"] [data-testid="stHorizontalBlock"] > div:last-child button {
        background-color: transparent !important;
        border: none !important;
        padding: 8px 10px !important;
        font-size: 14px !important;
        opacity: 0;
        min-width: auto !important;
        width: auto !important;
        border-radius: 0 !important;
        color: #8e8ea0 !important;
    }

    [data-testid="stSidebar"] [data-testid="stHorizontalBlock"]:hover > div:last-child button {
        opacity: 1;
    }

    [data-testid="stSidebar"] [data-testid="stHorizontalBlock"] > div:last-child button:hover {
        background-color: #3d3d3d !important;
        border-radius: 4px !important;
    }

    /* Delete option - appears below, no icon */
    .sidebar-delete-option {
        margin: 0 8px 4px 8px !important;
    }

    .sidebar-delete-option button {
        background-color: #2a2a2a !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 6px 12px !important;
        font-size: 12px !important;
        color: #b3b3b3 !important;
        text-align: left !important;
    }

    .sidebar-delete-option button:hover {
        background-color: #3d3d3d !important;
        color: #ff6b6b !important;
    }

    /* Confirmation dialog */
    [data-testid="stSidebar"] .stWarning {
        background-color: #2d2d2d !important;
        border: none !important;
        border-radius: 8px !important;
        margin: 4px 8px !important;
        padding: 10px !important;
        font-size: 12px !important;
    }

    /* Company selector section */
    .company-selector-section {
        padding: 12px;
        border-bottom: 1px solid #2d2d2d;
        margin-bottom: 8px;
    }

    /* Hide default hr dividers in sidebar */
    [data-testid="stSidebar"] hr {
        display: none !important;
    }

    /* Selectbox in sidebar */
    [data-testid="stSidebar"] .stSelectbox {
        margin: 8px 0 !important;
    }

    [data-testid="stSidebar"] .stSelectbox > div > div {
        background-color: #2d2d2d !important;
        border: 1px solid #3d3d3d !important;
        border-radius: 8px !important;
    }

    /* Info box for locked company */
    [data-testid="stSidebar"] .stAlert {
        background-color: #2d2d2d !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 10px 12px !important;
    }

    /* Modal popup box background */
    [role="dialog"] > div:last-child {
        background-color: #2d2d2d !important;
        padding: 24px !important;
    }

    /* Make modal content area include buttons */
    [role="dialog"] section[data-testid="stVerticalBlock"] {
        background-color: #2d2d2d !important;
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
if "delete_menu_open" not in st.session_state:
    st.session_state.delete_menu_open = None  # Session ID of open menu
if "confirm_delete" not in st.session_state:
    st.session_state.confirm_delete = None  # Session ID pending confirmation
if "show_company_warning" not in st.session_state:
    st.session_state.show_company_warning = False  # Show company change popup

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

def get_session_title(session, company_id_to_name):
    """Get a title for the chat session based on company name."""
    company_id = session.get("company_id")
    if company_id and company_id in company_id_to_name:
        company_name = company_id_to_name[company_id]
        # Truncate company name if too long
        if len(company_name) > 30:
            return company_name[:27] + "..."
        return company_name
    return f"Company {company_id}" if company_id else "New Chat"


def delete_chat_session(session_id):
    """Delete a chat session."""
    if session_id in st.session_state.chat_sessions:
        del st.session_state.chat_sessions[session_id]
        # Clear memory for this session
        st.session_state.memory_manager.clear_session(session_id)
        st.session_state.memory_manager.clear_all_agent_memories(session_id)
        # If deleted session was active, switch to another or create new
        if st.session_state.current_session_id == session_id:
            if st.session_state.chat_sessions:
                # Switch to most recent session
                sorted_sessions = sorted(
                    st.session_state.chat_sessions.values(),
                    key=lambda x: x["created_at"],
                    reverse=True
                )
                st.session_state.current_session_id = sorted_sessions[0]["id"]
                st.session_state.current_company_id = sorted_sessions[0]["company_id"]
            else:
                st.session_state.current_session_id = None

# Load companies data
companies = load_companies()
company_options = {comp['name']: comp['id'] for comp in companies}
company_id_to_name = {comp['id']: comp['name'] for comp in companies}

# Check if current session has messages (locked to company)
current_session_has_messages = (
    st.session_state.current_session_id and
    st.session_state.current_session_id in st.session_state.chat_sessions and
    len(st.session_state.chat_sessions[st.session_state.current_session_id].get("messages", [])) > 0
)

# Sidebar
with st.sidebar:
    # Sidebar title - centered
    st.markdown("<h3 style='text-align: center; margin-bottom: 16px;'>Insurance Intelligence</h3>", unsafe_allow_html=True)

    # New Chat button - ChatGPT style
    if st.button("+ New chat", key="new_chat_btn", use_container_width=True):
        default_company_name = next(
            (comp['name'] for comp in companies if comp['id'] == DEFAULT_COMPANY_ID),
            list(company_options.keys())[0] if company_options else None
        )
        if default_company_name:
            company_id = company_options[default_company_name]
            create_new_chat_session(company_id)
            st.rerun()

    # Company selector - always show but trigger popup if session is locked
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

    selected_company_id = company_options[selected_company_name]

    # Handle company change
    if selected_company_id != st.session_state.current_company_id:
        if current_session_has_messages:
            # Session is locked - show warning popup
            st.session_state.show_company_warning = True
            st.session_state.pending_company_id = selected_company_id
        else:
            # No messages yet - allow company change
            st.session_state.current_company_id = selected_company_id
            if st.session_state.current_session_id and st.session_state.current_session_id in st.session_state.chat_sessions:
                st.session_state.chat_sessions[st.session_state.current_session_id]["company_id"] = selected_company_id

    # Use the current company_id for queries
    company_id = st.session_state.current_company_id

    # Chat sessions list
    if st.session_state.chat_sessions:
        st.markdown('<div class="chats-header">Chats</div>', unsafe_allow_html=True)

        # Sort sessions: current session first, then by creation time (newest first)
        current_id = st.session_state.current_session_id
        sorted_sessions = sorted(
            st.session_state.chat_sessions.values(),
            key=lambda x: (x["id"] != current_id, -x["created_at"].timestamp()),
        )

        for session in sorted_sessions[:10]:  # Show last 10 chats
            session_title = get_session_title(session, company_id_to_name)
            is_active = session["id"] == st.session_state.current_session_id
            menu_open = st.session_state.delete_menu_open == session["id"]
            confirm_open = st.session_state.confirm_delete == session["id"]

            # Create columns for chat item and menu button
            col1, col2 = st.columns([5, 1])

            with col1:
                if st.button(
                    session_title,
                    key=f"session_{session['id']}",
                    use_container_width=True,
                    type="primary" if is_active else "secondary",
                ):
                    st.session_state.current_session_id = session["id"]
                    st.session_state.current_company_id = session["company_id"]
                    st.session_state.delete_menu_open = None
                    st.session_state.confirm_delete = None
                    st.rerun()

            with col2:
                # Toggle menu on click
                if st.button("⋮", key=f"menu_{session['id']}", help="Options"):
                    if menu_open:
                        st.session_state.delete_menu_open = None
                    else:
                        st.session_state.delete_menu_open = session["id"]
                        st.session_state.confirm_delete = None
                    st.rerun()

            # Show delete option if menu is open
            if menu_open and not confirm_open:
                if st.button("Delete", key=f"delete_option_{session['id']}", use_container_width=True):
                    st.session_state.confirm_delete = session["id"]
                    st.session_state.delete_menu_open = None
                    st.rerun()

            # Delete confirmation is now handled via modal popup outside sidebar

# Delete confirmation modal - define outside the condition
delete_modal = modal.Modal("Delete Chat", key="delete_modal", padding=20, max_width=400)

# Trigger modal open when confirm_delete is set
if st.session_state.confirm_delete and not delete_modal.is_open():
    delete_modal.open()

# Clear state if modal was closed externally (clicked outside)
if not delete_modal.is_open() and st.session_state.confirm_delete:
    st.session_state.confirm_delete = None

# Modal content - always define this
if delete_modal.is_open():
    session_to_delete = st.session_state.confirm_delete
    session_title = ""
    if session_to_delete and session_to_delete in st.session_state.chat_sessions:
        session_title = get_session_title(st.session_state.chat_sessions[session_to_delete], company_id_to_name)

    with delete_modal.container():
        st.markdown(f"""
            <div style="text-align: center; padding: 10px 0 20px 0;">
                <div style="font-size: 14px; color: #b3b3b3; margin-bottom: 8px;">Are you sure you want to delete</div>
                <div style="font-size: 16px; font-weight: 500; color: #e3e3e3;">"{session_title}"?</div>
            </div>
        """, unsafe_allow_html=True)

        bcol1, bcol2 = st.columns(2)
        with bcol1:
            if st.button("Delete", key="confirm_delete_yes", type="primary", use_container_width=True):
                delete_chat_session(session_to_delete)
                st.session_state.confirm_delete = None
                delete_modal.close()
                st.rerun()
        with bcol2:
            if st.button("Cancel", key="confirm_delete_no", use_container_width=True):
                st.session_state.confirm_delete = None
                delete_modal.close()
                st.rerun()

# Company change warning modal - no close button
company_modal = modal.Modal("Company Locked", key="company_modal", padding=20, max_width=420)

# Trigger modal open when show_company_warning is set
if st.session_state.show_company_warning and not company_modal.is_open():
    company_modal.open()

# Clear state if modal was closed externally (clicked outside)
if not company_modal.is_open() and st.session_state.show_company_warning:
    st.session_state.show_company_warning = False
    st.session_state.pending_company_id = None

# Modal content
if company_modal.is_open():
    current_company_name = company_id_to_name.get(st.session_state.current_company_id, "Unknown")
    pending_company_name = company_id_to_name.get(
        st.session_state.get("pending_company_id", st.session_state.current_company_id),
        "Unknown"
    )

    with company_modal.container():
        st.markdown(f"""
            <div style="text-align: center; padding: 10px 0 20px 0;">
                <div style="font-size: 14px; color: #b3b3b3; margin-bottom: 8px;">This chat is specific to</div>
                <div style="font-size: 18px; font-weight: 600; color: #4a8cf7; margin-bottom: 16px;">{current_company_name}</div>
                <div style="font-size: 14px; color: #b3b3b3;">To chat about <strong style="color: #e3e3e3;">{pending_company_name}</strong>, please start a new chat.</div>
            </div>
        """, unsafe_allow_html=True)

        if st.button("Start New Chat", key="dialog_new_chat", type="primary", use_container_width=True):
            pending_id = st.session_state.get("pending_company_id", DEFAULT_COMPANY_ID)
            create_new_chat_session(pending_id)
            st.session_state.current_company_id = pending_id
            st.session_state.show_company_warning = False
            st.session_state.pending_company_id = None
            company_modal.close()
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
                # Get conversation history from LangChain memory (kept for compatibility)
                conversation_history = st.session_state.memory_manager.get_conversation_history(
                    current_session["id"]
                )

                # Get agent-specific memories
                agent_memories = st.session_state.memory_manager.get_all_agent_memories(
                    current_session["id"]
                )

                # Use MultiAgentOrchestrator for routing between SQL and Document agents
                orchestrator = MultiAgentOrchestrator(company_id=current_session["company_id"])
                result = orchestrator.process_query(
                    user_question=prompt,
                    session_id=current_session["id"],
                    conversation_history=conversation_history,
                    agent_memories=agent_memories
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

        # Update LangChain memory (main conversation)
        st.session_state.memory_manager.add_exchange(
            current_session["id"],
            prompt,
            response_text
        )

        # Persist agent-specific memories from the result
        if "agent_memories" in result:
            agent_memories = result["agent_memories"]
            session_id = current_session["id"]

            # Update each agent's memory with new entries
            for agent_name, memory_entries in agent_memories.items():
                if memory_entries:
                    # Get the last entry (the new one from this execution)
                    # We compare with what was passed in to find new entries
                    current_stored = st.session_state.memory_manager.get_agent_history(session_id, agent_name)
                    new_entries = memory_entries[len(current_stored):]

                    for entry in new_entries:
                        st.session_state.memory_manager.add_agent_exchange(
                            session_id,
                            agent_name,
                            entry.get("question", ""),
                            entry.get("answer", "")
                        )

        # Update session title if first message
        if len(current_session["messages"]) == 2:  # First Q&A
            companies = load_companies()
            company_id_to_name = {comp['id']: comp['name'] for comp in companies}
            current_session["title"] = get_session_title(current_session, company_id_to_name)