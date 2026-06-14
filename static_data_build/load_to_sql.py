"""
ACARS Server
SQL Connection and Models
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries
import csv
import os
import re
from pathlib import Path

# Third Party Libraries
from dotenv import load_dotenv
from loguru import logger
from sqlmodel import Session, SQLModel, create_engine, text
from sqlalchemy.exc import ProgrammingError

# Local Libraries
from acars_server.databases import CPDLCTypes

PWD = Path(os.path.dirname(__file__))
load_dotenv(os.path.join(PWD.parent, "acars_server", ".env"))

DATABASE_HOST = os.getenv("MYSQL_HOST", "localhost")
DATABASE_PORT = int(os.getenv("MYSQL_PORT", "3306"))
DATABASE_NAME = os.getenv("MYSQL_DB", "acars")
DATABASE_USER = os.getenv("MYSQL_USER", "acars")
DATABASE_PASSWORD = os.getenv("MYSQL_PASSWORD")

DATABASE_URL = (
    f"mysql+pymysql://{DATABASE_USER}:{DATABASE_PASSWORD}"
    f"@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

with engine.begin() as conn:
    try:
        conn.execute(text("TRUNCATE TABLE cpdlctypes"))
    except ProgrammingError as exc:
        logger.warning(
            "Skipping truncate for cpdlctypes due to ProgrammingError: {}", exc
        )

SQLModel.metadata.create_all(engine)
session = Session(engine)

data_to_build = [
    os.path.join(PWD, "built_data", "output_1.csv"),
    os.path.join(PWD, "built_data", "output_2.csv")
]

for file in data_to_build:
    logger.debug(file)
    line_one = True
    with open(file, "r", encoding="utf-8") as f:
        read_csv = csv.DictReader(f)
        for line in read_csv:
            # Extract Ref
            ref = re.match(r"^([UD]M)\s*([0-9]{1,3}[a-z]{0,2})$", line["Ref"])

            if ref:
                data = {
                    "direction": ref.group(1),
                    "reference_number": f"{ref.group(1)}{ref.group(2)}",
                    "message_intent": line["Message Intent"],
                    "message_element": line["Message Element"],
                    "response_type": line["Resp"],
                    "fans_1_a": False,
                    "fans_1_a_atn_b1": False,
                    "atn_b1": False
                }

                # Extract Data Link Systems
                if line.get("Data link system"):
                    if "FANS 1/A- ATN B1" in line["Data link system"]:
                        data["fans_1_a_atn_b1"] = True
                    if re.match(r"FANS 1/A(?!-)", line["Data link system"]):
                        data["fans_1_a"] = True
                    if re.match(r"(?<=A-\s)ATN B1", line["Data link system"]):
                        data["atn_b1"] = True
                else:
                    data["fans_1_a_atn_b1"] = True
                    data["fans_1_a"] = True
                    data["atn_b1"] = True

                db_add = CPDLCTypes.model_validate(data)
                session.add(db_add)
                session.commit()
                session.refresh(db_add)
