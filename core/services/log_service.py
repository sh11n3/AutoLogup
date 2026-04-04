from core.models.log_entry import LogEntry
from core.parser.parser_factory import ParserFactory


class LogService:
    def __init__(self):
        self.logs: list[LogEntry] = []
        self.parser_factory = ParserFactory()

    def load_files(self, file_paths: list[str]) -> list[LogEntry]:
        self.logs = []

        for file_path in file_paths:
            parser = self.parser_factory.get_parser(file_path)

            try:
                entries = parser.parse(file_path)
                self.logs.extend(entries)
            except Exception as error:
                print(f"Error parsing '{file_path}': {error}")

        return self.logs