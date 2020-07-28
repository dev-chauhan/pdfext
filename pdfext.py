import pdfquery
import re
import pyquery
from pyquery import PyQuery as d


def pq_multiwords(pq, element, list_of_words):
    """
    returns PyQuery element containing `element` from `pq` containing first matched
    word from `list_of_words`
    """
    return pq(
        ",".join(
            ['{0}:contains("{1}")'.format(element, word) for word in list_of_words]
        )
    )


def find_col_header(pq, headerList, is_match=lambda x: True):
    label = []
    
    for header in headerList:
        label = pq_multiwords(pq, "LTTextLineHorizontal", [header])
        if len(label):
            break

    if len(label) == 0:
        return None
    page_pq = next(label[0].iterancestors("LTPage"))
    pageNum = int(page_pq.layout.pageid)

    elements = pq(
        'LTPage[pageid="{4}"] LTTextLineHorizontal:overlaps_bbox("{0},{1},{2},{3}")'.format(
            float(label.attr("x0")),
            float(label.attr("y0")) - 25,
            float(label.attr("x1")),
            float(label.attr("y0")) - 5,
            pageNum,
        )
    )
    elements.sort(
        key=lambda x: (
            int(pyquery.PyQuery(x, parent=elements).parents("LTPage").attr.pageid),
            -float(x.get("y1")),
            float(x.get("x0")),
        )
    )
    return elements.filter(is_match)


def find_row_header(pq, headerList, is_match=lambda x: True):
    label = pq_multiwords(pq, "LTTextLineHorizontal", headerList)
    if len(label) == 0:
        return None
    page_pq = next(label[0].iterancestors("LTPage"))
    pageNum = int(page_pq.layout.pageid)

    elements = pq(
        'LTPage[pageid="{4}"] LTTextLineHorizontal:overlaps_bbox("{0},{1},{2},{3}")'.format(
            float(label.attr("x1")) + 5,
            float(label.attr("y0")),
            float(label.attr("x1")) + 60,
            float(label.attr("y1")),
            pageNum,
        )
    ).filter(is_match)
    return elements


def column_or_row(
    pq, word_list, reg=None, match_col=lambda x: True, match_row=lambda x: True
):
    """
    Find value of field of first matched field name from `word_list` of
    first matched using `find_header`, `find_row_header`, `find_in_same`
    """
    header_data = find_col_header(pq, word_list, match_col)
    row_data = find_row_header(pq, word_list, match_row)
    row_in_data = pq_multiwords(pq, "LTTextLineHorizontal", word_list)

    if reg is None:
        return header_data.text()
    try:
        word1 = re.search(reg, header_data.text())
    except AttributeError:
        word1 = None

    try:
        word2 = re.search(reg, row_data.text())
    except AttributeError:
        word2 = None

    try:
        word3 = re.search(reg, row_in_data.text())
    except AttributeError:
        word3 = None

    if word1:
        return word1.group(0)
    elif word2:
        return word2.group(0)
    elif word3:
        return word3.group(0)
    else:
        return ""


def column_and_row(pq, col_name_list, row_name_list):
    """
    col name has to be unique for entier pdf
    """
    col_el = pq_multiwords(pq, "LTTextBoxHorizontal", col_name_list)

    if len(col_el) == 0:
        return ""

    page_pq = next(col_el[0].iterancestors("LTPage"))
    pageNum = int(page_pq.layout.pageid)
    row_el = pq_multiwords(
        pq(f'LTPage[pageid="{pageNum}"]'), "LTTextLineHorizontal", row_name_list
    )
    row_el.sort(key=lambda el: abs(-float(el.get("y0")) + float(col_el.attr("y0"))))

    if len(row_el) == 0:
        return ""

    x0 = col_el.attr("x0")
    x1 = col_el.attr("x1")
    y0 = row_el.attr("y0")
    y1 = row_el.attr("y1")

    cell_el = pq(
        'LTPage[pageid="{4}"] LTTextLineHorizontal:overlaps_bbox("{0},{1},{2},{3}")'.format(
            x0, y0, x1, y1, pageNum
        )
    )

    return cell_el.text()


def get_row(pq, pageid, el):
    """
    Returns PyQuery Object with LTTextLineHorizontal elements in row containing `el` element
    """
    mid_y = (float(el.get("y0")) + float(el.get("y1"))) / 2
    if len(pq('LTPage[pageid="{0}"]'.format(pageid))):
        pq = pq('LTPage[pageid="{0}"]'.format(pageid))
    row = pq("LTTextLineHorizontal").filter(
        lambda i, e: float(e.get("x0")) >= float(el.get("x1"))
        and (
            (float(e.get("y0")) <= mid_y and float(e.get("y1")) >= mid_y)
            or (float(e.get("y1")) - mid_y >= 0 and float(e.get("y1")) - mid_y <= 15)
        )
        and float(e.get("height")) <= 2 * float(el.get("height"))
    )
    return row


def get_row_table(pq, pageid, bbox):
    """
    Returns dictionary with each key is row header and
    value is the text in respective row elements
    """
    els = pq(f"LTPage[pageid='{pageid}'] LTTextLineHorizontal").filter(
        lambda i, el: float(el.get("x0")) < (bbox["x1"] + bbox["x0"]) / 2
        and float(el.get("y1")) <= bbox["y1"]
        and float(el.get("y0")) >= bbox["y0"]
    )
    table = {}
    els.sort(key=lambda el: -float(el.get("y0")))
    for el in els:
        row = get_row(pq, pageid, el)
        nel = pyquery.PyQuery(el)
        if len(nel.text()) < 5 and not re.search("[a-z]|[A-Z]", nel.text()):
            continue
        table[nel.text()] = row.text().split(" ")
    return table


def get_row_table_start_end_keys(pq, start_list, end_list):

    start_el = pq_multiwords(pq, "LTTextLineHorizontal", start_list)
    if len(start_el) == 0:
        return {}

    start_page = next(start_el[0].iterancestors("LTPage"))

    end_el = pq_multiwords(pq, "LTTextLineHorizontal", end_list).filter(
        lambda i, el: next(el.iterancestors("LTPage")).get("pageid")
        >= start_page.get("pageid")
    )

    x0 = float(start_page.get("x0"))
    x1 = float(start_page.get("x1"))
    y0 = float(end_el.attr("y1"))
    y1 = float(start_el.attr("y1"))

    end_page = next(end_el[0].iterancestors("LTPage"))

    if start_page.get("pageid") == end_page.get("pageid"):
        bbox = {"x0": x0, "x1": x1, "y0": y0, "y1": y1}
        table = get_row_table(pq, int(start_page.get("pageid")), bbox)

    else:
        bbox1 = {"x0": x0, "x1": x1, "y0": float(start_page.get("y0")), "y1": y1}
        table = get_row_table(pq, int(start_page.get("pageid")), bbox1)
        bbox2 = {
            "x0": x0,
            "x1": x1,
            "y0": float(start_page.get("y0")),
            "y1": float(start_page.get("y1")),
        }
        for page in range(
            int(start_page.get("pageid")) + 1, int(end_page.get("pageid"))
        ):
            table = {**table, **get_row_table(pq, page, bbox2)}
        bbox3 = {"x0": x0, "x1": x1, "y0": y0, "y1": float(end_page.get("y1"))}
        table = {**table, **get_row_table(pq, int(end_page.get("pageid")), bbox3)}

    return table


def inRange(el, start_page, start_pq, end_page, end_pq, pq):
    e = pyquery.PyQuery(el, parent=pq)
    page = e.parents("LTPage")
    if page.attr.pageid == start_page.attr.pageid:
        if page.attr.pageid == end_page.attr.pageid:
            return (
                float(e.attr.y0) > float(end_pq.attr.y1) - 5
                and float(e.attr.y1) <= float(start_pq.attr.y1) + 5
            )
        else:
            return float(e.attr.y1) <= float(start_pq.attr.y1) + 5
    elif page.attr.pageid == end_page.attr.pageid:
        return float(e.attr.y0) > float(end_pq.attr.y1) - 5
    elif end_page.attr.pageid is None or (
        int(page.attr.pageid) < int(end_page.attr.pageid)
        and int(page.attr.pageid) > int(start_page.attr.pageid)
    ):
        return True
    else:
        return False


def multilineProcess(self, pq):
    page = pq.parents("LTPage")
    row_keys = pq.filter(
        lambda i, el: float(el.get("x0"))
        < (float(page.attr("x0")) + float(page.attr("x1"))) / 3
    )
    txt_list = []
    y0 = float(page.attr.y0)
    x1 = float(page.attr.x0)
    row_keys.sort(key=lambda x: float(x.get("y1")))
    for row_key in row_keys:
        if float(row_key.get("y0")) > y0 and float(row_key.get("x1")) < x1:
            continue
        elif float(row_key.get("y0")) == y0 and float(row_key.get("x1")) > x1:
            txt_list.pop()
        row_pq = get_row(pq, int(page.attr("pageid")), row_key)
        txt_list.append(row_pq.text())
        y0 = float(row_key.get("y0"))
        x1 = float(row_key.get("x1"))
    txt = ""
    for t in txt_list:
        txt += t
    txt = re.sub("[^0-9\.]+\.*[^0-9\.]*", "", txt)
    try:
        return float(txt)
    except ValueError as err:
        return None


class RowStructure:
    def __init__(self, key, children=[]):
        self.key = key
        self.children = children

    def get_start(self, pq):
        raise NotImplementedError

    def get_end(self, pq):
        raise NotImplementedError

    def process(self, pq):
        raise NotImplementedError

    def exist(self, pq):
        return self.get_start(pq)

    def get_pq(self, pq):
        start_pq = self.get_start(pq)
        end_pq = self.get_end(pq)
        end_pq = end_pq.filter(
            lambda i, el: (
                int(d(el, parent=end_pq).parents("LTPage").attr.pageid),
                -float(el.get("y1")),
            )
            > (int(start_pq.parents("LTPage").attr.pageid), -float(start_pq.attr.y1))
        )
        start_page = start_pq.parents("LTPage")
        end_page = end_pq.parents("LTPage")
        res = pq("LTTextLineHorizontal").filter(
            lambda i, e: inRange(e, start_page, start_pq, end_page, end_pq, pq)
        )
        res.sort(
            key=lambda x: (
                int(pyquery.PyQuery(x, parent=res).parents("LTPage").attr.pageid),
                -float(x.get("y1")),
                float(x.get("x0")),
            )
        )
        return res

    def extract(self, pq):
        self.pq = self.get_pq(pq)
        available_children = []
        for child in self.children:
            if child.exist(self.pq):
                available_children.append(child)

        return {
            self.key: self.process(self.pq),
            "children": [child.extract(self.pq) for child in available_children],
        }


class ChildOnlyRow(RowStructure):
    
    def extract(self, pq):
        self.pq = self.get_pq(pq)
        available_children = []
        for child in self.children:
            if child.exist(self.pq):
                available_children.append(child)

        return {
            self.key: {
                child.key: child.extract(self.pq)[child.key] for child in available_children
            }
        }


class SimpleRowStruct(RowStructure):
    def process(self, pq):
        row_pq = get_row(
            pq, int(pq.parents("LTPage").attr("pageid")), (self.get_start(pq))[0]
        )
        # print("row_pq", (self.get_start(pq))[0].text)
        txt = re.sub("[^0-9\.]+\.*[^0-9\.]*", "", row_pq.text())
        try:
            return float(txt)
        except ValueError as err:
            return None
    
    def get_end(self, pq):
        return pq

    def extract(self, pq):
        self.pq = self.get_pq(pq)
        available_children = []
        for child in self.children:
            if child.exist(self.pq):
                available_children.append(child)

        if len(self.children) == 0:
            return {self.key: self.process(self.pq)}
        return {
            self.key: self.process(self.pq),
            "children": [child.extract(self.pq) for child in available_children],
        }


class MultilineRowStruct(RowStructure):
    def process(self, pq):
        page = pq.parents("LTPage")
        row_keys = pq.filter(
            lambda i, el: float(el.get("x0"))
            < (float(page.attr("x0")) + float(page.attr("x1"))) / 3
        )
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

        if self.key == "17(1)":
            print(row_keys.text())
        for row_key in row_keys:
            if float(row_key.get("y0")) > y0 and float(row_key.get("x1")) < x1:
                continue
            elif float(row_key.get("y0")) == y0 and float(row_key.get("x1")) > x1:
                txt_list.pop()
            row_pq = get_row(pq, int(page.attr("pageid")), row_key)
            txt_list.append(row_pq.text())
            y0 = float(row_key.get("y0"))
            x1 = float(row_key.get("x1"))
        txt = ""
        for t in txt_list:
            txt += t
        txt = re.sub("[^0-9\.]+\.*[^0-9\.]*", "", txt)
        try:
            return float(txt)
        except ValueError as err:
            return None
