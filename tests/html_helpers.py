"""Small helpers for asserting against server-rendered HTML fragments.

Several pages in this app (notifications.html, employer_notification.html,
savedJob.html) render a repeating card per item with a `data-id`/`data-*`
attribute, and rely on client-side JS to filter/highlight based on those
attributes. Since the acceptance tests drive the app over HTTP only (no JS
execution), these helpers isolate a single card's markup so assertions
about *that* card's attributes/classes don't accidentally match a sibling
card elsewhere on the page.
"""

from __future__ import annotations

import re


def item_block(page_html: str, doc_id: str, *, item_class: str = "notif-item") -> str:
    """Return the HTML fragment for one repeating card identified by
    `data-id="{doc_id}"`, precisely scoped to that card's own `<div>...
    </div>` (balancing nested divs), so trailing markup elsewhere on the
    page -- including literal `data-read="false"` strings inside inline
    `<script>` blocks -- can never leak into the match."""

    marker = f'data-id="{doc_id}"'
    delimiter = f'<div class="{item_class}'

    search_from = 0

    while True:
        start = page_html.find(delimiter, search_from)

        if start == -1:
            raise AssertionError(f'No "{item_class}" card with {marker!r} found in page')

        open_tag_end = page_html.index(">", start) + 1

        pos = open_tag_end
        depth = 1

        while depth > 0:
            next_open = page_html.find("<div", pos)
            next_close = page_html.find("</div>", pos)

            if next_close == -1:
                raise AssertionError("Unbalanced <div> while scanning page HTML")

            if next_open != -1 and next_open < next_close:
                depth += 1
                pos = next_open + len("<div")
            else:
                depth -= 1
                pos = next_close + len("</div>")

        block = page_html[start:pos]

        if marker in block:
            return block

        search_from = pos


def tab_count(page_html: str, element_id: str) -> int:
    """Read the `(N)` badge count next to a tab, e.g. id="unreadTabCount"."""

    match = re.search(rf'id="{element_id}">\((\d+)\)', page_html)
    assert match, f"{element_id} marker not found in page"
    return int(match.group(1))
