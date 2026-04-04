class AppController:
    def __init__(self, log_service):
        self.log_service = log_service

    def load_files(self, file_paths):
        return self.log_service.load_files(file_paths)