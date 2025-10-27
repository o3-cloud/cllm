"""
Tests for conversation management functionality.

These tests verify the Conversation and ConversationManager classes
as specified in ADR-0007: Conversation Threading and Context Management.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from cllm.conversation import Conversation, ConversationManager


class TestConversation:
    """Test suite for Conversation dataclass."""

    def test_conversation_creation(self):
        """Test basic conversation creation."""
        conv = Conversation(id="test-conv", model="gpt-4")
        assert conv.id == "test-conv"
        assert conv.model == "gpt-4"
        assert conv.messages == []
        assert isinstance(conv.metadata, dict)

    def test_conversation_with_messages(self):
        """Test conversation creation with initial messages."""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]
        conv = Conversation(id="test", model="gpt-4", messages=messages)
        assert len(conv.messages) == 2
        assert conv.messages == messages

    def test_add_message(self):
        """Test adding messages to a conversation."""
        conv = Conversation(id="test", model="gpt-4")
        conv.add_message("user", "Hello, world!")
        assert len(conv.messages) == 1
        assert conv.messages[0]["role"] == "user"
        assert conv.messages[0]["content"] == "Hello, world!"

    def test_add_multiple_messages(self):
        """Test adding multiple messages."""
        conv = Conversation(id="test", model="gpt-4")
        conv.add_message("user", "First message")
        conv.add_message("assistant", "Response")
        conv.add_message("user", "Follow-up")

        assert len(conv.messages) == 3
        assert conv.messages[0]["role"] == "user"
        assert conv.messages[1]["role"] == "assistant"
        assert conv.messages[2]["role"] == "user"

    def test_get_messages(self):
        """Test retrieving all messages."""
        messages = [{"role": "user", "content": "Test"}]
        conv = Conversation(id="test", model="gpt-4", messages=messages)
        retrieved = conv.get_messages()
        assert retrieved == messages

    def test_to_dict(self):
        """Test conversion to dictionary."""
        conv = Conversation(id="test", model="gpt-4")
        conv.add_message("user", "Hello")
        data = conv.to_dict()

        assert data["id"] == "test"
        assert data["model"] == "gpt-4"
        assert len(data["messages"]) == 1
        assert "created_at" in data
        assert "updated_at" in data
        assert "metadata" in data

    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "id": "test",
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Hello"}],
            "created_at": "2025-10-27T10:00:00Z",
            "updated_at": "2025-10-27T10:00:00Z",
            "metadata": {"total_tokens": 100},
        }
        conv = Conversation.from_dict(data)

        assert conv.id == "test"
        assert conv.model == "gpt-4"
        assert len(conv.messages) == 1
        assert conv.total_tokens == 100

    def test_total_tokens_property(self):
        """Test total tokens property."""
        conv = Conversation(id="test", model="gpt-4")
        assert conv.total_tokens == 0

        conv.total_tokens = 150
        assert conv.total_tokens == 150
        assert conv.metadata["total_tokens"] == 150

    def test_updated_at_changes_on_add_message(self):
        """Test that updated_at timestamp changes when adding messages."""
        conv = Conversation(id="test", model="gpt-4")
        initial_updated_at = conv.updated_at

        # Small delay to ensure timestamp changes
        import time

        time.sleep(0.01)
        conv.add_message("user", "Hello")

        assert conv.updated_at != initial_updated_at


class TestConversationManager:
    """Test suite for ConversationManager."""

    @pytest.fixture
    def temp_storage(self):
        """Create a temporary storage directory for tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def manager(self, temp_storage):
        """Create a ConversationManager with temporary storage."""
        return ConversationManager(storage_dir=temp_storage)

    def test_manager_initialization(self, temp_storage):
        """Test manager initialization creates storage directory."""
        manager = ConversationManager(storage_dir=temp_storage)
        assert manager.storage_dir == temp_storage
        assert temp_storage.exists()

    def test_manager_default_storage_precedence_local(self, tmp_path, monkeypatch):
        """Test manager prefers local .cllm directory when it exists."""
        # Create a temporary directory with .cllm folder
        local_cllm = tmp_path / ".cllm"
        local_cllm.mkdir()

        # Change to that directory
        monkeypatch.chdir(tmp_path)

        manager = ConversationManager()
        expected_path = tmp_path / ".cllm" / "conversations"
        assert manager.storage_dir == expected_path

    def test_manager_default_storage_precedence_global(self, tmp_path, monkeypatch):
        """Test manager falls back to home directory when no local .cllm exists."""
        # Change to a temp directory without .cllm folder
        monkeypatch.chdir(tmp_path)

        manager = ConversationManager()
        expected_path = Path.home() / ".cllm" / "conversations"
        assert manager.storage_dir == expected_path

    def test_generate_id(self, manager):
        """Test UUID-based ID generation."""
        conv_id = manager._generate_id()
        assert conv_id.startswith("conv-")
        assert len(conv_id) == 13  # "conv-" + 8 hex chars

    def test_generate_id_uniqueness(self, manager):
        """Test that generated IDs are unique."""
        id1 = manager._generate_id()
        id2 = manager._generate_id()
        assert id1 != id2

    def test_validate_id_valid(self, manager):
        """Test ID validation with valid IDs."""
        # Should not raise
        manager._validate_id("valid-id-123")
        manager._validate_id("test_conversation")
        manager._validate_id("conv-abc123")

    def test_validate_id_invalid_characters(self, manager):
        """Test ID validation rejects invalid characters."""
        with pytest.raises(ValueError, match="Invalid conversation ID"):
            manager._validate_id("invalid id with spaces")

        with pytest.raises(ValueError, match="Invalid conversation ID"):
            manager._validate_id("invalid/id/slashes")

        with pytest.raises(ValueError, match="Invalid conversation ID"):
            manager._validate_id("invalid@id.com")

    def test_validate_id_empty(self, manager):
        """Test ID validation rejects empty strings."""
        with pytest.raises(ValueError, match="cannot be empty"):
            manager._validate_id("")

    def test_create_conversation_with_auto_id(self, manager):
        """Test creating conversation with auto-generated ID."""
        conv = manager.create()
        assert conv.id.startswith("conv-")
        assert len(conv.id) == 13

    def test_create_conversation_with_custom_id(self, manager):
        """Test creating conversation with user-specified ID."""
        conv = manager.create(conversation_id="my-conversation")
        assert conv.id == "my-conversation"

    def test_create_conversation_with_model(self, manager):
        """Test creating conversation with model specified."""
        conv = manager.create(conversation_id="test", model="gpt-4")
        assert conv.id == "test"
        assert conv.model == "gpt-4"

    def test_create_conversation_invalid_id(self, manager):
        """Test that invalid IDs are rejected."""
        with pytest.raises(ValueError, match="Invalid conversation ID"):
            manager.create(conversation_id="invalid id!")

    def test_create_conversation_duplicate_id(self, manager):
        """Test that duplicate IDs are rejected."""
        conv = manager.create(conversation_id="test")
        manager.save(conv)  # Save to disk so it exists
        with pytest.raises(ValueError, match="already exists"):
            manager.create(conversation_id="test")

    def test_save_and_load_conversation(self, manager):
        """Test saving and loading a conversation."""
        conv = manager.create(conversation_id="test", model="gpt-4")
        conv.add_message("user", "Hello")
        conv.add_message("assistant", "Hi there!")

        manager.save(conv)

        loaded = manager.load("test")
        assert loaded.id == conv.id
        assert loaded.model == conv.model
        assert len(loaded.messages) == 2
        assert loaded.messages[0]["content"] == "Hello"

    def test_save_creates_json_file(self, manager, temp_storage):
        """Test that save creates a JSON file."""
        conv = manager.create(conversation_id="test")
        manager.save(conv)

        filepath = temp_storage / "test.json"
        assert filepath.exists()

        # Verify JSON is well-formed
        with open(filepath, "r") as f:
            data = json.load(f)
        assert data["id"] == "test"

    def test_save_atomic_write(self, manager, temp_storage):
        """Test that save uses atomic write (temp file + rename)."""
        conv = manager.create(conversation_id="test")

        # Simulate partial write failure
        original_replace = Path.replace

        def mock_replace(self, target):
            # Verify temp file exists before rename
            assert self.suffix == ".tmp"
            assert self.exists()
            original_replace(self, target)

        with patch.object(Path, "replace", mock_replace):
            manager.save(conv)

        # Verify final file exists and temp file is cleaned up
        assert (temp_storage / "test.json").exists()
        assert not (temp_storage / "test.json.tmp").exists()

    def test_load_nonexistent_conversation(self, manager):
        """Test loading a conversation that doesn't exist."""
        with pytest.raises(FileNotFoundError, match="not found"):
            manager.load("nonexistent")

    def test_load_malformed_json(self, manager, temp_storage):
        """Test loading a conversation with malformed JSON."""
        # Create a malformed JSON file
        filepath = temp_storage / "malformed.json"
        with open(filepath, "w") as f:
            f.write("{invalid json")

        with pytest.raises(ValueError, match="Malformed conversation"):
            manager.load("malformed")

    def test_exists(self, manager):
        """Test checking if a conversation exists."""
        assert not manager.exists("test")

        conv = manager.create(conversation_id="test")
        manager.save(conv)

        assert manager.exists("test")

    def test_delete_conversation(self, manager, temp_storage):
        """Test deleting a conversation."""
        conv = manager.create(conversation_id="test")
        manager.save(conv)

        assert (temp_storage / "test.json").exists()

        manager.delete("test")

        assert not (temp_storage / "test.json").exists()

    def test_delete_nonexistent_conversation(self, manager):
        """Test deleting a conversation that doesn't exist."""
        with pytest.raises(FileNotFoundError, match="not found"):
            manager.delete("nonexistent")

    def test_list_conversations_empty(self, manager):
        """Test listing conversations when none exist."""
        conversations = manager.list_conversations()
        assert conversations == []

    def test_list_conversations_single(self, manager):
        """Test listing a single conversation."""
        conv = manager.create(conversation_id="test", model="gpt-4")
        conv.add_message("user", "Hello")
        manager.save(conv)

        conversations = manager.list_conversations()
        assert len(conversations) == 1
        assert conversations[0]["id"] == "test"
        assert conversations[0]["model"] == "gpt-4"
        assert conversations[0]["message_count"] == 1

    def test_list_conversations_multiple(self, manager):
        """Test listing multiple conversations."""
        for i in range(3):
            conv = manager.create(conversation_id=f"test-{i}", model="gpt-4")
            conv.add_message("user", f"Message {i}")
            manager.save(conv)

        conversations = manager.list_conversations()
        assert len(conversations) == 3

    def test_list_conversations_sorted_by_updated(self, manager):
        """Test that conversations are sorted by updated_at (most recent first)."""
        import time

        # Create conversations with slight delays
        conv1 = manager.create(conversation_id="first", model="gpt-4")
        manager.save(conv1)

        time.sleep(0.01)

        conv2 = manager.create(conversation_id="second", model="gpt-4")
        manager.save(conv2)

        time.sleep(0.01)

        conv3 = manager.create(conversation_id="third", model="gpt-4")
        manager.save(conv3)

        conversations = manager.list_conversations()
        assert conversations[0]["id"] == "third"
        assert conversations[1]["id"] == "second"
        assert conversations[2]["id"] == "first"

    def test_list_conversations_skips_malformed(self, manager, temp_storage):
        """Test that list_conversations skips malformed JSON files."""
        # Create a valid conversation
        conv = manager.create(conversation_id="valid")
        manager.save(conv)

        # Create a malformed JSON file
        malformed_path = temp_storage / "malformed.json"
        with open(malformed_path, "w") as f:
            f.write("{invalid")

        # Should only return the valid conversation
        conversations = manager.list_conversations()
        assert len(conversations) == 1
        assert conversations[0]["id"] == "valid"

    def test_save_and_load_preserves_metadata(self, manager):
        """Test that metadata is preserved across save/load."""
        conv = manager.create(conversation_id="test")
        conv.total_tokens = 500
        conv.metadata["tags"] = ["code-review", "python"]

        manager.save(conv)
        loaded = manager.load("test")

        assert loaded.total_tokens == 500
        assert loaded.metadata["tags"] == ["code-review", "python"]

    def test_conversation_roundtrip(self, manager):
        """Test complete roundtrip: create, modify, save, load."""
        # Create conversation
        conv = manager.create(conversation_id="roundtrip", model="claude-3-opus")

        # Add messages
        conv.add_message("user", "What is Python?")
        conv.add_message(
            "assistant",
            "Python is a high-level programming language.",
        )
        conv.add_message("user", "Tell me more")

        # Set metadata
        conv.total_tokens = 250

        # Save
        manager.save(conv)

        # Load
        loaded = manager.load("roundtrip")

        # Verify everything matches
        assert loaded.id == "roundtrip"
        assert loaded.model == "claude-3-opus"
        assert len(loaded.messages) == 3
        assert loaded.total_tokens == 250
        assert loaded.messages[0]["content"] == "What is Python?"
        assert loaded.messages[1]["role"] == "assistant"
        assert loaded.messages[2]["content"] == "Tell me more"
