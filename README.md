## pdfext.py

A PyQuery object is an object on which we can query for elements in xml tree similar to jQuery

pdfquery constructs xml tree from elements captured by pdfminer like, LTTextLine, LTPage, etc from given pdf.

**`find_row_header`**

returns `PyQuery` object containing `element`'s from `pq` containing first matched word from `list_of_words`

### inputs

`pq`: _PyQuery object_

`element`: _xml element name_

`list_of_words`: _list of possible keys to be matched_

```
function pq_multiwords(pq, element, list_of_words):

    return Union of queries for each word in list_of_words which is a PyQuery object containing elements which contains a word which is in list_of_words

    // by default PyQuery object has attributes of first element from xml tree in PyQuery object so we do not need to filter out specifically first element - union will also work
```

**`find_col_header`**

returns a `PyQuery` object which contains elements which are just below the first matched word from `col_name_list`

### inputs

`pq`: _PyQuery object_

`headerList`: _list of words along which value should exist_

`is_match`: _Boolean function which can be passed to filter using elements returning `True` value_

```
function find_col_header(pq, headerList, is_match=lambda x: True):

    label = pq_multiwords(pq, "LTTextLineHorizontal", headerList)

    if label is empty return None

    pageNum := page number on which label is located

    elements := query on label object for elements which overlaps bbox which is atleast 5 and atmax 30 point below label and has same width as label (element should only overlap not necessary that they should be contained in that bbox) filtered using is_match function

    return elements
```

**`find_row_header`**

Returns `PyQuery` Object having xml element on the right side of the given row header.

### inputs

`pq`: _PyQuery object_

`headerList`: _list of words along which value should exist_

`is_match`: _Boolean function which can be passed to filter using elements returning `True` value_

```
function find_row_header(pq, headerList, is_match=lambda x: True):

    label = pq_multiwords(pq, "LTTextLineHorizontal", headerList)

    if label is empty return None

    pageNum := page number on which label exist

    elements := query on label object for elements which overlaps bbox which is atleast 5 and atmax 60 point on right side of the label and has same height as label (element should only overlap not necessary that they should be contained in that bbox) filtered using is_match function

    return elements
```

**`column_or_row`**

Returns string matching the regex from the text or the entire text contained in the xml element on the right side or below of the given word.

### inputs

`pq`: _PyQuery object_

`word_list`: _list of words below or along which value should exist_

`reg`: _string representing regex which matches desired value_

```

function column_or_row(pq, word_list, reg=None):

    // find elements which are below word_list
    header_data = find_header(pq, word_list)

    // find elements which are along (right hand side) word_list
    row_data = find_row_header(pq, word_list)

    // find elements which are on the same element (TAN: <Tan number>, here as there is no line between value and key pdfminer (called by pdfquery lib) will parse this whole string as one element)
    row_in_data = pq_multiwords(pq, 'LTTextLineHorizontal', word_list)

    if no regex is given return text found below the word_list

    word1 := matched string with regex which is below the word_list or None

    word2 := matched string with regex which is along (right hand side) the word_list or None

    word3 := matched string with regex which is on the same element containing the word_list or None

    return the first non None value from word1, word2 and word3. if all are None return empty string
```

**`column_and_row`**

Returns the text contained in the xml element on the intersection of the element containing column name and the element containing row name.

### inputs

`pq`: _PyQuery object_

`col_name_list`: _list of words which are possible as column name_

`row_name_list`: _list of words which are possible as row name_

```
function column_and_row(pq, col_name_list, row_name_list):

    col_el = pq_multiwords(pq, "LTTextBoxHorizontal", col_name_list)

    if col_el is empty return empty string

    pageNum := page number on which label exist

    row_el = pq_multiwords(
        pq(f'LTPage[pageid="{pageNum}"]'), "LTTextLineHorizontal", row_name_list
    )  // find row_el on same page number

    // sort based on its distance from column element (because this way we can get nearest element from column name containig row name, as by default PyQuery uses attributes of first element from queried elements)
    row_el.sort(key=lambda el: abs(-float(el.get("y0")) + float(col_el.attr("y0"))))

    if row_el is empty return empty string

    x0 = col_el.attr("x0")  // use x-coordinates of column element
    x1 = col_el.attr("x1")
    y0 = row_el.attr("y0")  // use y-coordinats of row element
    y1 = row_el.attr("y1")

    cell_el := query for elements which overlaps above mentioned coordinates

    return text from queried cell_el
```

**`get_row`**

Returns `PyQuery` Object having all xml elements which are on the right side of the given xml element.

### inputs

`pq`: _PyQuery object_

`pageid`: _page number of the given xml element_

`el`: _xml element_

```
function getRow(pq, pageid, el):
    return query on pq for elements from which middle horizontal line of el passes through or at max 15 points above middle horizontal line of el and has width less than twice of el
```

**`get_row_table`**

Returns a python dictionary containing keys of row table contained in given bbox of pdf as key of dictionary and values as value of that key in the python dictionary

### inputs

`pq`: _PyQuery object_

`pageid`: _page number of the given xml element_

`bbox`: _python dictionary haivng keys "x0", "x1", "y0", "y1" representing bbox where (x0, y0) is lower left corner and (x1, y1) is top right corner_

```
function get_row_table(pq, pageid, bbox):

    els := query over pq for text elements contained in left half of bbox (left half is considered because all row keys start from left of the page and go towards right of the page, we can also reduce half to one thired or fourth etc, as we find best)

    sort els as they appear on pdf page from top to bottom

    table := empty dictionary

    for el in els:
        row = get_row(pq, pageid, el)
        nel = pyqyery.PyQuery(el) // convert xml element to pyquery object

        if el does not contain any letter as text we will throw that element

        table[nel.text()] = row.text().split(" ")

    return table
```

**`get_row_table_start_end_keys`**

Returns a python dictionary containing keys of row table, recognised by given the start string and the end string, of the pdf as key of dictionary and values as value of that key in the python dictionary

### inputs

`pq`: _PyQuery object_

`start_list`: _list of possible words as the start of row table_

`end_list`: _list of possible words as the end of row table_

```
function get_row_table_start_end_keys(pq, start_list, end_list):

    start_el = pq_multiwords(pq, "LTTextLineHorizontal", start_list)

    if start_el is empty return empty dictionary

    start_page := LTPage (page element) xml element on which start_el exist

    end_el = pq_multiwords(pq, "LTTextLineHorizontal", end_list).filter(
        lambda i, el: next(el.iterancestors("LTPage")).get("pageid")
        >= start_page.get("pageid")
    ) // text elements containing end words and occures after start element

    x0 = float(start_page.get("x0"))  // start of page on x-axis
    x1 = float(start_page.get("x1"))  // end of page on x-axis
    y0 = float(end_el.attr("y1"))  // start of row table on y-axis on start page
    y1 = float(start_el.attr("y1"))  // end of row table on y-axis on end page

    end_page := LTPage (page element) xml element on which end_el exist

    if row table is on one page:
        table = get_row_table(pq, <page number>, <box containing row table>)

    else:
        extract table from start page
        extract table from middle pages
        extract table from end page
        merge all the dictionaries

    return table
```
