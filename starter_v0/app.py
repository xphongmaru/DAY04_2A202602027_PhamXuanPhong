import streamlit as st
import os
import json
import sys
import io

# Force UTF-8 encoding for stdout and stderr on Windows to avoid CharMap errors safely
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

from datetime import datetime
from pathlib import Path
from typing import Any

from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import build_artifact_version, artifact_version_dict
from chat import run_model_tool_loop, trim_history, assistant_tool_message, tool_results_message, execute_tool_call

# Setup roots
ROOT = Path(__file__).parent
ARTIFACTS_DIR = ROOT / "artifacts"
TRANSCRIPTS_DIR = ROOT / "transcripts"
TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
load_lab_env(ROOT)

# Page configuration with premium layout
st.set_page_config(
    page_title="Research Agent Terminal",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom premium CSS
st.markdown("""
<style>
    .reportview-container {
        background: linear-gradient(to right, #0f2027, #203a43, #2c5364);
        color: white;
    }
    .stChatFloatingInputContainer {
        background-color: transparent !important;
    }
    .tool-card {
        border-radius: 8px;
        padding: 12px;
        margin: 8px 0px;
        border-left: 5px solid #00c9ff;
        background-color: #1e293b;
        color: #e2e8f0;
    }
    .tool-name {
        font-weight: bold;
        color: #38bdf8;
    }
    .tool-args {
        font-family: monospace;
        background-color: #0f172a;
        padding: 4px 8px;
        border-radius: 4px;
        color: #f1f5f9;
        font-size: 0.85em;
    }
    .tool-status-ok {
        color: #4ade80;
        font-weight: bold;
    }
    .tool-status-err {
        color: #f87171;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# App Title & Header
st.title("🤖 Research Agent UI")
st.markdown("### Evidence-driven Prompt Engineering & Tool Calling Monitor")
st.markdown("---")

# Initialize Sidebar Controls
st.sidebar.image("https://img.icons8.com/nolan/128/bot.png", width=80)
st.sidebar.header("Configuration & Versioning")

version_option = st.sidebar.selectbox(
    "Select Agent Version",
    ["v3", "v2", "v1", "v0"],
    index=0,
    help="Version matches the system prompt and tool definitions."
)

provider_option = st.sidebar.selectbox(
    "Select Provider",
    ["openai", "gemini", "openrouter"],
    index=0,
    help="Defaults to openai (which maps to NVIDIA API in this environment)."
)

max_rounds = st.sidebar.slider("Max Tool Call Rounds", 1, 10, 4)
history_window = st.sidebar.slider("History Message Window", 1, 10, 5)

# Load selected version system prompt and tools
system_prompt_path = ARTIFACTS_DIR / "system_prompt.md"
tools_path = ARTIFACTS_DIR / "tools.yaml"

if system_prompt_path.exists() and tools_path.exists():
    system_prompt = system_prompt_path.read_text(encoding="utf-8")
    tool_declarations = load_tool_declarations(tools_path)
    openai_tools = to_openai_tools(tool_declarations)
    artifact_version = build_artifact_version(version_option, system_prompt_path, tools_path)
    
    # Show metadata in Sidebar
    st.sidebar.markdown("---")
    st.sidebar.subheader("Metadata Registry")
    st.sidebar.info(f"**Version**: `{artifact_version.artifact_version}`")
    st.sidebar.text(f"Prompt Hash:\n{artifact_version.prompt_hash[:16]}...")
    st.sidebar.text(f"Tools Hash:\n{artifact_version.tools_hash[:16]}...")
    
    # Add a reset button
    if st.sidebar.button("Clear Chat Session", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.messages = []
        st.session_state.awaiting_input = False
        st.session_state.pending_tool_events = []
        st.rerun()
else:
    st.error("System prompt or tools.yaml missing in artifacts directory.")
    st.stop()

# Initialize session state for conversation
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []  # format: [{"role": "user"|"assistant", "content": "...", "tool_events": [...]}]
if "messages" not in st.session_state:
    st.session_state.messages = []      # formatted for LLM: [{"role": "user"|"assistant"|"system", "content": "..."}]
if "awaiting_input" not in st.session_state:
    st.session_state.awaiting_input = False
if "pending_tool_events" not in st.session_state:
    st.session_state.pending_tool_events = []

# Display current chat logs
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        # Show trace details if there are tool events
        if msg.get("tool_events"):
            with st.expander("🔍 Show Tool Execution Trace", expanded=False):
                for event in msg["tool_events"]:
                    st.markdown(
                        f"""
                        <div class="tool-card">
                            <b>[TOOL]</b> <span class="tool-name">{event['tool']}</span><br/>
                            <b>Arguments:</b> <span class="tool-args">{json.dumps(event['args'], ensure_ascii=False)}</span><br/>
                            <b>Result:</b> {json.dumps(event['result'], ensure_ascii=False)}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

# Get LLM response
def get_agent_response(user_input: str):
    provider = make_provider(provider_option)
    
    # Prepare payload
    messages = [
        {"role": "system", "content": system_prompt},
        *trim_history(st.session_state.messages, history_window),
        {"role": "user", "content": user_input}
    ]
    
    with st.spinner("Agent is reasoning and invoking tools..."):
        try:
            result = run_model_tool_loop(
                provider=provider,
                messages=messages,
                tools=openai_tools,
                model=None,
                max_tool_rounds=max_rounds
            )
            return result
        except Exception as e:
            st.error(f"Error executing agent loop: {str(e)}")
            return None

# Chat input from user
user_query = st.chat_input("Enter your research request here...")

if user_query:
    # 1. Display User Message
    st.session_state.chat_history.append({"role": "user", "content": user_query})
    st.session_state.messages.append({"role": "user", "content": user_query})
    st.rerun()

# If user query was just added and agent hasn't responded yet
if len(st.session_state.chat_history) > 0 and st.session_state.chat_history[-1]["role"] == "user":
    user_input = st.session_state.chat_history[-1]["content"]
    
    # Run loop
    result = get_agent_response(user_input)
    
    if result:
        status = result["status"]
        assistant_text = result["assistant_text"]
        tool_events = result["tool_events"]
        
        # Display response
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": assistant_text,
            "tool_events": tool_events
        })
        
        st.session_state.messages.append({"role": "assistant", "content": assistant_text})
        
        # Save transcript
        timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
        transcript_path = TRANSCRIPTS_DIR / f"{version_option}_{provider_option}_{timestamp}.transcript.json"
        transcript_payload = {
            "version": version_option,
            "provider": provider_option,
            "artifact_version": artifact_version.artifact_version,
            "prompt_hash": artifact_version.prompt_hash,
            "tools_hash": artifact_version.tools_hash,
            "query": user_input,
            "status": status,
            "response": assistant_text,
            "tool_events": tool_events,
            "timestamp": datetime.now().isoformat()
        }
        transcript_path.write_text(json.dumps(transcript_payload, ensure_ascii=False, indent=2), encoding="utf-8")
        
        st.rerun()
