import pdfquery
import re
import sys
from pdfext import *
import json
import os

"""
python main.py <pdf path>

extracted data will be stored in extracted directory
"""


def getCombinedRows(data, matchList, sequential=True):
    if not sequential:
        raise NotImplementedError
    matchIdx = 0
    rowList = []
    for key in data:
        if matchIdx >= len(matchList):
            break
        if matchList[matchIdx](key):
            rowList.append([key])
            matchIdx += 1
        elif matchIdx != 0:
            rowList[-1].append(key)
    return rowList


class grossSalary(SimpleRowStruct):
    def get_start(self, pq):
        return pq('LTTextLineHorizontal:contains("Gross Salary")')

    def get_end(self, pq):
        return pq(
            'LTTextLineHorizontal:contains("Less"):contains("Allowance"):contains("10")'
        )


class grossSalary171(MultilineRowStruct):
    def get_start(self, pq):
        return pq('LTTextLineHorizontal:contains("17(1)")')

    def get_end(self, pq):
        return pq('LTTextLineHorizontal:contains("17(2)")')


class grossSalary172(MultilineRowStruct):
    def get_start(self, pq):
        return pq('LTTextLineHorizontal:contains("17(2)")')

    def get_end(self, pq):
        return pq('LTTextLineHorizontal:contains("17(3)")')


class grossSalary173(MultilineRowStruct):
    def get_start(self, pq):
        return pq('LTTextLineHorizontal:contains("17(3)")')

    def get_end(self, pq):
        return pq('LTTextLineHorizontal:contains("Total")')


class grossSalaryTotal(SimpleRowStruct):
    def get_start(self, pq):
        return pq('LTTextLineHorizontal:contains("Total")')

    def get_end(self, pq):
        return pq(
            'LTTextLineHorizontal:contains("Less"):contains("Allowance"):contains("10")'
        )


if __name__ == "__main__":

    pdfname = sys.argv[1]  # get pdf name from arguments
    pdf = pdfquery.PDFQuery(pdfname)  # PDFQuery object
    pdf.load()  # creates xml tree from given pdf using elements identified by pdfminer library in pdf
    print(pdfname)
    data = {
        "NameOfEmployer": column_or_row(
            pdf.pq,  # PyQuery object on which we can query for elements similar to jQuery syntax
            [
                "Name and address of the Employer",
                "Name and Address of the Employer",
                "Deductor Name",
            ],  # list of possible keywords below or along which we want to find the value
            "[A-Za-z ]{9}[A-Za-z ]*",  # regex matching the value we want, default is any pattern (e.g. "*")
        ),
        "PANOfDeductor": column_or_row(
            pdf.pq, ["PAN of the Deductor"], "[A-Z]{5}[0-9]{4}[A-Z]{1}"
        ),
        "TANOfDeductor": column_or_row(
            pdf.pq, ["TAN of the Deductor", "TAN"], "[A-Z]{4}[0-9]{5}[A-Z]{1}"
        ),
        "PANOfEmployee": column_or_row(
            pdf.pq, ["PAN of the Employee", "Emp. PAN"], "[A-Z]{5}[0-9]{4}[A-Z]{1}"
        ),
        "AssessmentYear": column_or_row(pdf.pq, ["Assessment Year"], "[0-9]{4}-[0-9]*"),
        "TDSOnSalary": column_and_row(
            pdf.pq,
            [
                "Amount of tax deposited",
                "Amount of tax deducted/remitted",
            ],  # possible column names
            ["Total"],  # possible row names
        ),
        **get_row_table_start_end_keys(
            pdf.pq, ["FORM NO.12BA"], ["Declaration by Employer",],
        ),
    }

    gross_salary = grossSalary(
        "GrossSalary",
        children=[
            grossSalary171("17(1)"),
            grossSalary172("17(2)"),
            grossSalary173("17(3)"),
            grossSalaryTotal("Total"),
        ],
    )

    if gross_salary.exist(pdf.pq):
        data["GrossSalary"] = gross_salary.extract(pdf.pq)

    # write data into json file
    os.makedirs("extracted", exist_ok=True)
    with open(
        "extracted/{0}.json".format(pdfname.split("/")[-1].split(".")[0]), "w"
    ) as f:
        json.dump(data, f, indent=4)
