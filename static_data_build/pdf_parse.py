"""
ACARS Server
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries
import os
import re
from pathlib import Path
from typing import Dict, List

# Third Party Libraries
import camelot
import pandas as pd
from loguru import logger

PWD = Path(os.path.dirname(__file__))


class PdfParser:
    """Parses a PDF"""

    def __init__(self, file_path:str, pages:str="all") -> None:
        logger.debug(file_path)
        self.file_path = file_path
        self.page_range = pages
        self._read_pdf()

    def _read_pdf(self) -> None:
        """Reads the specified PDF pages and then exports"""
        logger.info(f"Starting Camelot for pages {self.page_range}...")
        tables = camelot.read_pdf(self.file_path, pages=self.page_range)

        # Read the tables into a df
        logger.info("Reading tables into a df...")
        df = pd.concat([t.df for t in tables], ignore_index=True)

        # Remove line breaks inside all cells
        df = df.replace(r"\n", " ", regex=True)

        logger.info("Writing to 'temp_output.csv'")
        df.to_csv("temp_output.csv", index=False)

        logger.info("Running csv Cleaner...")
        self._csv_cleaner()

    def _csv_cleaner(self):
        """Cleans the csv"""
        logger.info("Reading 'temp_output.csv'")
        with open("temp_output.csv", "r", encoding="utf-8") as file:
            header = ""
            lines_out:Dict[str, List[str]] = {}
            counter = 0
            for line in file.readlines():
                if line.startswith("Ref"):
                    if line == header:
                        continue
                    header = line
                    counter += 1
                    lines_out[str(counter)] = [line]
                if header != "" and re.match(r"^[UD]M.*", line):
                    lines_out[str(counter)].append(line)

        logger.info("Writing cleaned data to csv...")
        for key, data in lines_out.items():
            write_path = os.path.join(PWD, "built_data", f"output_{key}.csv")
            with open(write_path, "w+", encoding="utf-8") as file:
                file.writelines(data)
            logger.success(f"Written to {write_path}")

pdf_path = os.path.join(PWD.parent, "reference_docs", "gold_2edition.pdf")
p = PdfParser(pdf_path, "214-266")
