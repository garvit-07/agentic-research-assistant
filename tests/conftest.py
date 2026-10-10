import os
import tempfile

# Must be set before the app is imported.
os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ["EMBEDDING_PROVIDER"] = "fake"
os.environ["DATA_DIR"] = tempfile.mkdtemp(prefix="ara-test-")
os.environ["API_KEY"] = ""
