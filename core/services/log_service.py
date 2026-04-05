from core.models.log_entry import LogEntry
from core.parser.parser_factory import ParserFactory


class LogService:
    def __init__(self):
        self.logs: list[LogEntry] = []
        self.parser_factory = ParserFactory()
        self.last_file_entry_counts: dict[str, int] = {}

    def load_files(self, file_paths: list[str]) -> list[LogEntry]:
        self.logs = []
        self.last_file_entry_counts = {}

        for file_path in file_paths:
            parser = self.parser_factory.get_parser(file_path)

            try:
                entries = parser.parse(file_path)

                for entry in entries:
                    entry.source_file = file_path

                self.logs.extend(entries)
                self.last_file_entry_counts[file_path] = len(entries)

            except Exception as error:
                print(f"Error parsing '{file_path}': {error}")
                self.last_file_entry_counts[file_path] = 0

        return self.logs