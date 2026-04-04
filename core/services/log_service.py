from utils.file_utils import read_file_lines


class LogService:
    def __init__(self):
        self.logs = []

    def load_files(self, file_paths):
        self.logs = []

        for path in file_paths:
            lines = read_file_lines(path)

            for line in lines:
                self.logs.append({
                    "raw": line.strip(),
                    "source": path
                })

        return self.logs