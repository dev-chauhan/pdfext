import sys
from extract import extract_from_pdf
import json
import os
"""
python main.py <pdf path>

extracted data will be stored in extracted directory
"""

if __name__ == "__main__":

    pdfname = sys.argv[1]  # get pdf name from arguments
    data = extract_from_pdf(pdfname, pdfname)
    os.makedirs("extracted", exist_ok=True)
    
    with open(
        "extracted/{0}.json".format(pdfname.split("/")[-1].split(".")[0]), "w"
    ) as f:
        json.dump(data, f, indent=4)
