"""Conversation memory manager using LangChain."""
from typing import Dict, List, Optional
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.messages import HumanMessage, AIMessage
from config.settings import MEMORY_WINDOW_SIZE


class ConversationMemoryManager:
    """
    Manage conversation memory per session using LangChain.

    Each chat session gets its own isolated memory instance.
    Memory is stored in a buffer with a configurable window size.
    """

    def __init__(self, window_size: int = None):
        """
        Initialize the memory manager.

        Args:
            window_size: Number of conversation turns to remember (default from settings)
        """
        self.window_size = window_size or MEMORY_WINDOW_SIZE
        self.memories: Dict[str, ConversationBufferWindowMemory] = {}

    def get_memory(self, session_id: str) -> ConversationBufferWindowMemory:
        """
        Get or create memory for a session.

        Args:
            session_id: Unique session identifier

        Returns:
            LangChain ConversationBufferWindowMemory instance
        """
        if session_id not in self.memories:
            self.memories[session_id] = ConversationBufferWindowMemory(
                k=self.window_size,  # Number of exchanges to remember
                return_messages=True,
                memory_key="chat_history",
                input_key="question",
                output_key="answer"
            )

        return self.memories[session_id]

    def add_exchange(
        self,
        session_id: str,
        user_question: str,
        assistant_response: str
    ) -> None:
        """
        Add a question-answer exchange to session memory.

        Args:
            session_id: Unique session identifier
            user_question: User's question
            assistant_response: Assistant's response
        """
        memory = self.get_memory(session_id)
        memory.save_context(
            {"question": user_question},
            {"answer": assistant_response}
        )

        # Log memory update
        print("\n💾 MEMORY UPDATE:")
        print(f"   Session ID: {session_id}")
        print(f"   Question Added: {user_question[:80]}...")
        print(f"   Response Added: {assistant_response[:80]}...")

        # Show current memory state
        history = self.get_conversation_history(session_id)
        print(f"   Total Exchanges in Memory: {len(history)}")
        print(f"   Memory Window Size: {self.window_size}")

    def get_conversation_history(self, session_id: str, log_retrieval: bool = False) -> List[Dict[str, str]]:
        """
        Get conversation history as list of Q&A pairs.

        Args:
            session_id: Unique session identifier
            log_retrieval: Whether to log memory retrieval (default: False)

        Returns:
            List of {'question': ..., 'answer': ...} dictionaries
        """
        if session_id not in self.memories:
            if log_retrieval:
                print("\n📚 MEMORY RETRIEVAL:")
                print(f"   Session ID: {session_id}")
                print("   Status: No previous conversation history")
            return []

        memory = self.get_memory(session_id)
        history = memory.load_memory_variables({})
        messages = history.get("chat_history", [])

        # Convert LangChain messages to simple Q&A format
        qa_pairs = []
        for i in range(0, len(messages), 2):
            if i + 1 < len(messages):
                human_msg = messages[i]
                ai_msg = messages[i + 1]

                if isinstance(human_msg, HumanMessage) and isinstance(ai_msg, AIMessage):
                    qa_pairs.append({
                        "question": human_msg.content,
                        "answer": ai_msg.content
                    })

        # Log memory retrieval if requested
        if log_retrieval:
            print("\n📚 MEMORY RETRIEVAL:")
            print(f"   Session ID: {session_id}")
            print(f"   Total Exchanges Retrieved: {len(qa_pairs)}")
            if qa_pairs:
                print("\n   Previous Conversation Context:")
                for idx, exchange in enumerate(qa_pairs, 1):
                    print(f"   [{idx}] Q: {exchange['question'][:60]}...")
                    print(f"       A: {exchange['answer'][:60]}...")

        return qa_pairs

    def get_conversation_history_raw(self, session_id: str) -> List:
        """
        Get raw conversation history as LangChain messages.

        Args:
            session_id: Unique session identifier

        Returns:
            List of LangChain message objects
        """
        if session_id not in self.memories:
            return []

        memory = self.get_memory(session_id)
        history = memory.load_memory_variables({})
        return history.get("chat_history", [])

    def clear_session(self, session_id: str) -> None:
        """
        Clear memory for a specific session.

        Args:
            session_id: Unique session identifier
        """
        if session_id in self.memories:
            del self.memories[session_id]

    def clear_all(self) -> None:
        """Clear all session memories."""
        self.memories.clear()

    def get_session_count(self) -> int:
        """Get number of active sessions with memory."""
        return len(self.memories)

    def session_exists(self, session_id: str) -> bool:
        """
        Check if a session has memory.

        Args:
            session_id: Unique session identifier

        Returns:
            True if session exists, False otherwise
        """
        return session_id in self.memories