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


class AllwncExemptUs10(RowStructure):
    def get_start(self, pq):
        return pq(
            'LTTextLineHorizontal:contains("Less"):contains("Allowance"):contains("10")'
        )

    def get_end(self, pq):
        return pq(
            'LTTextLineHorizontal:contains("Balance"),LTTextLineHorizontal:contains("BALANCE")'
        )

    def process(self, pq):
        page = pq.parents("LTPage")
        row_keys = pq.filter(
            lambda i, el: float(el.get("x0"))
            < (float(page.attr("x0")) + float(page.attr("x1"))) / 3
        )
        txt_dict = {}
        txt_list = []
        y0 = float(page.attr.y0)
        x1 = float(page.attr.x0)
        row_keys.sort(
            key=lambda x: (
                int(pyquery.PyQuery(x, parent=row_keys).parents("LTPage").attr.pageid),
                -float(x.get("y1")),
            )
        )
        for row_key in row_keys:
            if float(row_key.get("y0")) > y0 and float(row_key.get("x1")) < x1:
                continue
            elif float(row_key.get("y0")) == y0 and float(row_key.get("x1")) > x1:
                tmpKey = txt_list.pop()
                txt_dict.pop(tmpKey)
            row_pq = get_row(pq, int(page.attr("pageid")), row_key)
            key = pyquery.PyQuery(row_key).text()
            value = row_pq.text()
            for v in filter(None, value.split(" ")):
                value = v
            value = re.sub("[^0-9\.]+\.*[^0-9\.]*", "", value)
            try:
                txt_dict[key] = float(value)
                txt_list.append(key)
                y0 = float(row_key.get("y0"))
                x1 = float(row_key.get("x1"))
            except ValueError as err:
                continue
        return txt_dict

    def extract(self, pq):
        out = super().extract(pq)
        children = out.pop("children")
        assert len(children) == 0
        return out


class DeductionUS16(AllwncExemptUs10):
    def get_start(self, pq):
        p1 = pq(
            'LTTextLineHorizontal:contains("Deduction"),LTTextLineHorizontal:contains("DEDUCTION"),LTTextLineHorizontal:contains("deduction")'
        )('LTTextLineHorizontal:contains("16")')
        if len(p1):
            return p1
        else:
            return pq(
            "LTTextLineHorizontal:contains('Deductions'),LTTextLineHorizontal:contains('DEDUCTIONS')"
        )

    def exist(self, pq):
        e = self.get_start(pq)
        if "VI-A" in e.text() or "Chapter" in e.text() or "VIA" in e.text():
            return False
        return e

    def get_end(self, pq):
        return pq('LTTextLineHorizontal:contains("Aggregate")')
    
    def process(self, pq):
        page = pq.parents("LTPage")
        row_keys = pq.filter(
            lambda i, el: float(el.get("x0"))
            < (float(page.attr("x0")) + float(page.attr("x1"))) / 3 and el.get("y1") not in self.child_ys
        )
        txt_dict = {}
        txt_list = []
        y0 = float(page.attr.y0)
        x1 = float(page.attr.x0)
        row_keys.sort(
            key=lambda x: (
                int(pyquery.PyQuery(x, parent=row_keys).parents("LTPage").attr.pageid),
                -float(x.get("y1")),
            )
        )
        for row_key in row_keys:
            if float(row_key.get("y0")) > y0 and float(row_key.get("x1")) < x1:
                continue
            elif float(row_key.get("y0")) == y0 and float(row_key.get("x1")) > x1:
                tmpKey = txt_list.pop()
                txt_dict.pop(tmpKey)
            row_pq = get_row(pq, int(page.attr("pageid")), row_key)
            key = pyquery.PyQuery(row_key).text()
            value = row_pq.text()
            for v in filter(None, value.split(" ")):
                value = v
            value = re.sub("[^0-9\.]+\.*[^0-9\.]*", "", value)
            try:
                txt_dict[key] = float(value)
                txt_list.append(key)
                y0 = float(row_key.get("y0"))
                x1 = float(row_key.get("x1"))
            except ValueError as err:
                continue
        return txt_dict
    
    def extract(self, pq):
        self.pq = self.get_pq(pq)
        available_children = []
        ext = {}
        self.child_ys = []
        for child in self.children:
            if child.exist(self.pq):
                child_ext = child.extract(self.pq)
                ext[child.key] = child_ext[child.key]
                self.child_ys.append(child.get_start(self.pq).attr.y1)
        return {
            self.key: {**self.process(self.pq), **ext}
        }

class DeductionUS16i(SimpleRowStruct):
    def get_start(self, pq):
        return pq('LTTextLineHorizontal:contains("Standard")')(':contains("16(i)")')

    def get_end(self, pq):
        return pq('LTTextLineHorizontal:contains("Aggregate")')


class DeductionUS16ii(SimpleRowStruct):
    def get_start(self, pq):
        return pq('LTTextLineHorizontal:contains("Entertainment")')('LTTextLineHorizontal:contains("allowance"),LTTextLineHorizontal:contains("Allowance")')

    def get_end(self, pq):
        return pq('LTTextLineHorizontal:contains("Aggregate")')

class DeductionUS16iii(SimpleRowStruct):
    def get_start(self, pq):
        return pq('LTTextLineHorizontal:contains("Tax")')(':contains("employment"),:contains("Employment")')

    def get_end(self, pq):
        return pq('LTTextLineHorizontal:contains("Aggregate")')

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

    allwnc_exempt_us_10 = AllwncExemptUs10("AllwncExemptUs10")
    deduction_us_16 = DeductionUS16("DeductionUS16",  children=[
        DeductionUS16i("16(i)"),
        DeductionUS16ii("16(ii)"),
        DeductionUS16iii("16(iii)")
    ])

    if gross_salary.exist(pdf.pq):
        data["GrossSalary"] = gross_salary.extract(pdf.pq)

    if allwnc_exempt_us_10.exist(pdf.pq):
        data = {**data, **allwnc_exempt_us_10.extract(pdf.pq)}
    
    if deduction_us_16.exist(pdf.pq):
        data = {**data, **deduction_us_16.extract(pdf.pq)}
    else:
        for child in deduction_us_16.children:
            if child.exist(pdf.pq):
                if deduction_us_16.key in data:
                    data[deduction_us_16.key] = {**data[deduction_us_16.key], child.key: child.extract(pdf.pq)[child.key]}
                else:
                    data[deduction_us_16.key] = {child.key: child.extract(pdf.pq)[child.key]}
    # write data into json file
    os.makedirs("extracted", exist_ok=True)
    with open(
        "extracted/{0}.json".format(pdfname.split("/")[-1].split(".")[0]), "w"
    ) as f:
        json.dump(data, f, indent=4)
