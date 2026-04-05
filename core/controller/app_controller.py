from core.filter.filter_engine import FilterEngine


class AppController:
    def __init__(self, log_service):
        self.log_service = log_service
        self.filter_engine = FilterEngine()
        self.all_logs = []

    def load_files(self, file_paths):
        self.all_logs = self.log_service.load_files(file_paths)
        return self.all_logs

    def filter_logs(self, query: str):
        return self.filter_engine.filter_logs(self.all_logs, query)