# Copyright (c) 2021, Aakvatech Limited and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import nowdate


class RebatePolicy(Document):
    def validate(self):
        pass

    def before_submit(self):
        pass

    def on_submit(self):
        pass


def process_rebates():
    now_date = nowdate()
    rebates_list = frappe.get_all(
        "Rebate Policy",
        filters={
            "start_date": ["<=", now_date],
            "end_date": [">=", now_date],
            "rebate_status": ["not in", ["Completed", "Missed"]],
        },
    )
    for reb in rebates_list:
        process_rebate(reb.name, now_date)


@frappe.whitelist()
def process_rebate(reb_name, now_date=None):
    if not now_date:
        now_date = nowdate()
    doc = frappe.get_doc("Rebate Policy", reb_name)
    if (
        doc.start_date > now_date
        or doc.end_date < now_date
        or doc.rebate_status in ["Completed", "Missed"]
    ):
        return
    if doc.type == "Purchase":
        process_purchase_rebate(doc, now_date)
    elif doc.type == "Sales":
        process_sales_rebate(doc, now_date)
    elif doc.type == "Promotional Sales":
        process_promotional_rebate(doc, now_date)


def process_purchase_rebate(doc, now_date):
    pass


def process_sales_rebate(doc, now_date):
    pass


def process_promotional_rebate(doc, now_date):
    pass
