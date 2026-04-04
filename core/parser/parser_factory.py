from core.parser.base_parser import BaseParser
from core.parser.csv_parser import CSVParser
from core.parser.json_parser import JSONParser
from core.parser.sql_parser import SQLParser
from core.parser.text_parser import TextParser
from core.parser.xml_parser import XMLParser


class ParserFactory:
    def __init__(self):
        self.text_parser = TextParser()
        self.json_parser = JSONParser()
        self.csv_parser = CSVParser()
        self.xml_parser = XMLParser()
        self.sql_parser = SQLParser()

    def get_parser(self, file_path: str) -> BaseParser:
        lower_path = file_path.lower()

        if lower_path.endswith(".json"):
            return self.json_parser

        if lower_path.endswith(".csv"):
            return self.csv_parser

        if lower_path.endswith(".xml"):
            return self.xml_parser

        if lower_path.endswith(".sql"):
            return self.sql_parser

        if lower_path.endswith(".log") or lower_path.endswith(".txt"):
            return self.text_parser

        return self.text_parser