from core.filter.filter_engine import FilterEngine


class AppController:
    def __init__(self, log_service):
        # The controller is the small coordination layer between the UI and the
        # underlying services. The window talks to this object instead of dealing
        # with parsing and filtering internals directly.
        self.log_service = log_service
        self.filter_engine = FilterEngine()
        self.all_logs = []

    def load_files(self, file_paths):
        # Keep the full result of the last load operation in memory.
        # Later filters always work against this full dataset, not only against
        # whatever subset is currently visible in the UI.
        self.all_logs = self.log_service.load_files(file_paths)
        return self.all_logs

    def filter_logs(self, query: str):
        # Apply the current filter query to the complete in-memory dataset.
        # This avoids compounding filters accidentally when the user edits
        # the query multiple times.
        return self.filter_engine.filter_logs(self.all_logs, query)

    def get_last_file_entry_counts(self):
        # Expose the per-file parse counts so the UI can show a small summary
        # after loading multiple files at once.
        return self.log_service.last_file_entry_counts
