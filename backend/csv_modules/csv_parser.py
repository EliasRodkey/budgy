#!python3
import csv
import io

_DELIMITERS = (",", ";", "\t")


def detect_delimiter(text: str) -> str:
    """Sniff the delimiter from the first 4KB of text. Falls back to comma."""
    try:
        dialect = csv.Sniffer().sniff(text[:4096], delimiters=",\t;|")
        return dialect.delimiter
    except csv.Error:
        return ","


def unwrap_row_quotes(text: str) -> str:
    """
    Some CSV exports (e.g. Google Sheets) wrap each entire row in double quotes:
        "Date,Item,Category,MOP,Cost"
        "1/1/26,Uber,Bolt,Apple Card,$35.26"
    Standard parsers treat each row as a single quoted field, producing one column.
    Detect this by checking whether a single-column parse yields a header that itself
    contains a delimiter, then strip the outer quotes and re-parse with the correct delimiter.
    """
    reader = csv.DictReader(io.StringIO(text))
    _ = list(reader)
    headers = list(reader.fieldnames or [])
    if len(headers) != 1:
        return text
    inner = headers[0]
    delimiter = next((d for d in _DELIMITERS if d in inner), None)
    if not delimiter:
        return text
    lines = [line.rstrip("\r\n") for line in text.splitlines() if line.strip()]
    return "\n".join(
        line[1:-1].replace('""', '"') if line.startswith('"') and line.endswith('"') else line
        for line in lines
    )
