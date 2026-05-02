import os
import email
from bs4 import BeautifulSoup
import re

# -----------------------------
# AUTO PATHS (works in HW7 folder)
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_DIR = os.path.join(BASE_DIR, "trace07", "trec07p", "data")
INDEX_FILE = os.path.join(BASE_DIR, "trace07", "trec07p", "full", "index")
OUTPUT_DIR = os.path.join(BASE_DIR, "Files")

os.makedirs(OUTPUT_DIR, exist_ok=True)

url = re.compile(
    r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
    re.I
)

# -----------------------------
# LOAD LABELS (spam / ham)
# -----------------------------
def spamHam():
    labelDict = {}

    if not os.path.exists(INDEX_FILE):
        print("INDEX FILE NOT FOUND:")
        print(INDEX_FILE)
        return labelDict

    with open(INDEX_FILE, "r", encoding="utf-8", errors="ignore") as indexFile:
        for line in indexFile:
            parts = line.strip().split()

            if len(parts) < 2:
                continue

            label = parts[0]
            path = parts[1]

            # example: ../data/inmail.1
            email_id = path.split(".")[-1]

            labelDict[email_id] = label

    return labelDict


# -----------------------------
# EXTRACT EMAIL BODY
# -----------------------------
def getBody(parts):
    ret = []

    if isinstance(parts, str):
        ret.append(parts)

    elif isinstance(parts, list):
        for part in parts:
            if part.is_multipart():
                ret += getBody(part.get_payload())
            else:
                ret += getBody(part)

    else:
        try:
            ctype = parts.get_content_type()

            if ctype == "text/plain":
                ret.append(str(parts.get_payload()))

            elif ctype == "text/html":
                soup = BeautifulSoup(str(parts.get_payload()), "html.parser")
                ret.append(soup.get_text())

        except:
            pass

    return ret


# -----------------------------
# CLEAN TEXT
# -----------------------------
def clean_string(text):
    text = re.sub(r"http\S+", " ", text)
    text = re.sub(r"[^a-zA-Z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# -----------------------------
# MAIN PROCESS
# -----------------------------
def load_trec_spam_files():
    labelDict = spamHam()

    if not os.path.exists(DATA_DIR):
        print("DATA FOLDER NOT FOUND:")
        print(DATA_DIR)
        return

    files = os.listdir(DATA_DIR)
    count = 0

    for each_file in files:
        file_path = os.path.join(DATA_DIR, each_file)

        if not os.path.isfile(file_path):
            continue

        try:
            with open(file_path, "r", encoding="ISO-8859-1", errors="ignore") as Email_File:

                emailID = each_file.split(".")[-1]

                msg = email.message_from_file(Email_File)

                subject = msg["Subject"] if msg["Subject"] else ""

                body = "\n".join(
                    p for p in getBody(msg.get_payload())
                    if isinstance(p, str)
                )

                emailText = subject + "\n" + body
                emailText = clean_string(emailText)

                label = labelDict.get(emailID, "ham")

                output_file = os.path.join(OUTPUT_DIR, f"{emailID}.txt")

                with open(output_file, "w", encoding="utf-8") as eFile:
                    content = f"""<EMAILID>{emailID}</EMAILID>
<TEXT>{emailText}</TEXT>
<LABEL>{label}</LABEL>"""
                    eFile.write(content)

                count += 1

                if count % 500 == 0:
                    print("Processed:", count)

        except Exception as e:
            print("Skipped:", each_file, e)

    print("DONE")
    print("Total Processed:", count)


# -----------------------------
# RUN
# -----------------------------
load_trec_spam_files()