from pdfext import *


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
        t = pq(
            'LTTextLineHorizontal:contains("Balance"),LTTextLineHorizontal:contains("BALANCE")'
        )
        if len(t):
            return t
        else:
            return pq('LTTextLineHorizontal:contains("Total"):contains("salary")')

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
        es = self.get_start(pq)
        ee = self.get_end(pq)
        # print(es.text(), ee.text())
        if len(es) and len(ee):
            return (int(es.parents("LTPage").attr.pageid), -float(es.attr.y1)) < (
                int(ee.parents("LTPage").attr.pageid),
                -float(ee.attr.y1),
            )
        return False

    def get_end(self, pq):
        # return pq('LTTextLineHorizontal:contains("Aggregate")')
        return pq('LTTextLineHorizontal:contains("Income")').filter(
            ':contains("Head"),:contains("head")'
        )

    def process(self, pq):
        page = pq.parents("LTPage")
        row_keys = pq.filter(
            lambda i, el: float(el.get("x0"))
            < (float(page.attr("x0")) + float(page.attr("x1"))) / 3
            and el.get("y1") not in self.child_ys
        )
        txt_dict = {}
        txt_list = []
        y0 = float(page.attr.y0)
        x1 = float(page.attr.x0)
        row_keys.sort(
            key=lambda x: (
                int(pyquery.PyQuery(x, parent=row_keys).parents("LTPage").attr.pageid),
                -float(x.get("y1")),
                float(x.get("x0")),
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
        return {self.key: {**self.process(self.pq), **ext}}


class DeductionUS16i(SimpleRowStruct):
    def get_start(self, pq):
        return pq('LTTextLineHorizontal:contains("Standard")')(':contains("16(i"),:contains("Deduction"),:contains("deduction")')

    def get_end(self, pq):
        return pq('LTTextLineHorizontal:contains("Aggregate")')


class DeductionUS16ii(SimpleRowStruct):
    def get_start(self, pq):
        return pq('LTTextLineHorizontal:contains("Entertainment")')(
            'LTTextLineHorizontal:contains("allowance"),LTTextLineHorizontal:contains("Allowance")'
        )

    def get_end(self, pq):
        return pq('LTTextLineHorizontal:contains("Aggregate")')


class DeductionUS16iii(SimpleRowStruct):
    def get_start(self, pq):
        return pq('LTTextLineHorizontal:contains("Tax")')(
            ':contains("employment"),:contains("Employment")'
        )

    def get_end(self, pq):
        return pq('LTTextLineHorizontal:contains("Aggregate")')


class PartB(ChildOnlyRow):
    def get_start(self, pq):
        return pq("LTTextLineHorizontal").filter(
            ':contains("PART-B"),:contains("Part B")'
        )

    def get_end(self, pq):
        return pq("LTTextLineHorizontal").filter(
            ':contains("VERIFICATION"),:contains("Verification")'
        )


class PAOORBalance(SimpleRowStruct):
    def get_start(self, pq):
        return pq("LTTextLineHorizontal").filter(':contains("BALANCE")')

    def get_end(self, pq):
        return pq


class InterestUS24(SimpleRowStruct):
    def get_start(self, pq):
        return (
            pq("LTTextLineHorizontal")
            .filter(':contains("Interest")')
            .filter(':contains("24")')
        )


class PAOORDeductions(ChildOnlyRow):
    def get_pq(self, pq):
        s = self.get_start(pq)
        ed = self.get_end(pq)
        start_page = s.parents("LTPage")
        end_page = ed.parents("LTPage")
        res = pq("LTTextLineHorizontal").filter(
            lambda i, e: inRange(e, start_page, s, end_page, ed, pq)
        )
        return res

    def get_start(self, pq):
        x = (
            pq("LTTextLineHorizontal")
            .filter(':contains("DEDUCTIONS")')
            .filter(lambda i, el: "VI-A" not in d(el).text())
        )
        return x
    def get_end(self, pq):
        x = pq('LTTextLineHorizontal').filter(':contains("Income")').filter(':contains("SALARIES")')
        return x

    def process(self, pq):
        page = pq.parents("LTPage")
        row_keys = pq.filter(
            lambda i, el: float(el.get("x0"))
            < (float(page.attr("x0")) + float(page.attr("x1"))) / 3
            # and el.get("y1") not in self.child_ys
        )
        other_val = 0
        txt_list = []
        y0 = float(page.attr.y0)
        x1 = float(page.attr.x0)
        row_keys.sort(
            key=lambda x: (
                int(pyquery.PyQuery(x, parent=row_keys).parents("LTPage").attr.pageid),
                -float(x.get("y1")),
                float(x.get("x0")),
            )
        )
        for row_key in row_keys:
            if float(row_key.get("y0")) > y0 and float(row_key.get("x1")) < x1:
                continue
            elif float(row_key.get("y0")) == y0 and float(row_key.get("x1")) > x1:
                tmpKey = txt_list.pop()
                txt_dict.pop(tmpKey)
            for child in self.children:
                if child.exist(d(row_key)):
                    continue
            row_pq = get_row(pq, int(page.attr("pageid")), row_key)
            key = pyquery.PyQuery(row_key).text()
            value = row_pq.text()
            for v in filter(None, value.split(" ")):
                value = v
            value = re.sub("[^0-9\.]+\.*[^0-9\.]*", "", value)
            try:
                other_val += float(value)
                txt_list.append(key)
                y0 = float(row_key.get("y0"))
                x1 = float(row_key.get("x1"))
            except ValueError as err:
                continue
        return other_val

    def extract(self, pq):
        x = super().extract(pq)
        return {**x, "form_16_pao_or_other_deductions_others": self.process(self.pq)}


class Aggregate(SimpleRowStruct):
    def get_start(self, pq):
        return pq('LTTextLineHorizontal').filter(':contains("Aggregate")')

class OtherIncome(MultilineRowStruct):
    def get_start(self, pq):
        return pq('LTTextLineHorizontal').filter(':contains("Add")').filter(':contains("other income")')
    
    def get_end(self, pq):
        return pq('LTTextLineHorizontal').filter(':contains("GROSS TOTAL INCOME")')

class TaxDeductedPartB(SimpleRowStruct):
    def get_start(self, pq):
        return pq('LTTextLineHorizontal').filter(':contains("Less")').filter(':contains("Tax Deducted")')

class PAOORAllwncExemptUs10(SimpleRowStruct):
    def get_start(self, pq):
        return pq(
            'LTTextLineHorizontal:contains("Less"):contains("Allowance"):contains("10")'
        )
    

