import re
import xml.etree.ElementTree as ET

from core.models.log_entry import LogEntry
from core.parser.base_parser import BaseParser
from core.parser.normalizer import Normalizer


class XMLParser(BaseParser):
    def __init__(self):
        self.normalizer = Normalizer()

    def parse(self, file_path: str) -> list[LogEntry]:
        entries: list[LogEntry] = []

        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
        except Exception as error:
            print(f"Error parsing XML file '{file_path}': {error}")
            return []

        record_elements = self._find_record_elements(root)

        for element in record_elements:
            data = self._element_to_dict(element)
            if not data:
                continue

            raw = self._element_to_raw_string(element)

            entry = self.normalizer.normalize(
                data=data,
                raw=raw,
                source_file=file_path,
            )
            entries.append(entry)

        return entries

    def _find_record_elements(self, root: ET.Element) -> list[ET.Element]:
        children = list(root)

        if not children:
            return [root]

        tag_counts: dict[str, int] = {}
        for child in children:
            tag = self._strip_namespace(child.tag)
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

        repeated_tags = {tag for tag, count in tag_counts.items() if count > 1}

        if repeated_tags:
            records = []
            for child in children:
                child_tag = self._strip_namespace(child.tag)
                if child_tag in repeated_tags:
                    records.append(child)
            return records

        return [root]

    def _element_to_dict(self, element: ET.Element, parent_key: str = "") -> dict:
        data: dict = {}
        current_tag = self._strip_namespace(element.tag)

        if parent_key:
            base_key = f"{parent_key}.{current_tag}"
        else:
            base_key = current_tag

        for attr_name, attr_value in element.attrib.items():
            key = f"{base_key}.@{attr_name}"
            data[key] = attr_value

        text = (element.text or "").strip()
        children = list(element)

        if text and not children:
            data[base_key] = text

        for child in children:
            child_data = self._element_to_dict(child, base_key)
            data.update(child_data)

        return data

    def _element_to_raw_string(self, element: ET.Element) -> str:
        try:
            raw_xml = ET.tostring(element, encoding="unicode")
            raw_xml = raw_xml.strip()

            # Alle Zeilenumbrüche + überflüssige Leerzeichen zwischen Tags entfernen
            raw_xml = re.sub(r">\s+<", "><", raw_xml)

            # Mehrfache Whitespaces innerhalb der Zeile reduzieren
            raw_xml = re.sub(r"\s+", " ", raw_xml)

            return raw_xml.strip()
        except Exception:
            return ""

    def _strip_namespace(self, tag: str) -> str:
        if "}" in tag:
            return tag.split("}", 1)[1]
        return tag