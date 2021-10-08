# Copyright (c) 2021, Aakvatech Limited and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import nowdate


class RebatePolicy(Document):
    def validate(self):
        self.total_qty_achieved = 0
        for item in self.items:
            self.total_qty_achieved += item.qty_achieved
        self.percentage = self.total_qty_achieved / self.target_qty * 100

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
        str(doc.start_date) > now_date
        or str(doc.end_date) < now_date
        or doc.rebate_status in ["Completed", "Missed"]
    ):
        return
    try:
        if doc.type == "Purchase":
            process_purchase_rebate(doc)
        elif doc.type == "Sales":
            process_sales_rebate(doc)
        elif doc.type == "Promotional Sales":
            process_promotional_rebate(doc)
        frappe.db.commit()
    except Exception as e:
        frappe.msgprint(str(e))
        frappe.log_error(frappe.get_traceback(), str(e))


def process_purchase_rebate(doc):
    purchase_receipts, items_liens, items_totals = get_purchases_for_rebate(doc)
    for item in doc.items:
        item.qty_achieved = items_totals.get(item.item)
    doc.save(ignore_permissions=True)

    # print("purchase_receipts", purchase_receipts)
    # print("items_liens", items_liens)
    # print("items_totals", items_totals)


def get_purchases_for_rebate(doc):
    accepted_items = [i.item for i in doc.items]
    purchase_receipts = []
    items_liens = []
    items_totals = frappe._dict()
    init_list = []

    in_list = frappe.get_all(
        "Purchase Invoice",
        filters={
            "docstatus": 1,
            "update_stock": 1,
            "supplier": doc.supplier,
            "posting_date": ["between", [doc.start_date, doc.end_date]],
        },
        fields=["name"],
    )
    for i in in_list:
        i["doctype"] = "Purchase Invoice"
        init_list.append(i)

    res_list = frappe.get_all(
        "Purchase Receipt",
        filters={
            "docstatus": 1,
            "supplier": doc.supplier,
            "posting_date": ["between", [doc.start_date, doc.end_date]],
        },
        fields=["name"],
    )
    for r in res_list:
        r["doctype"] = "Purchase Receipt"
        init_list.append(r)

    for el in init_list:
        accepted = False
        doc = frappe.get_doc(el.doctype, el.name)
        for item in doc.items:
            if item.item_code in accepted_items:
                accepted = True
                item_dict = frappe._dict()
                item_dict.item_code = item.item_code
                item_dict.qty = item.stock_qty
                item_dict.description = item.description
                item_dict.receipt_document_type = el.doctype
                item_dict.receipt_document = el.name
                item_dict.purchase_receipt_item = item.name
                items_liens.append(item_dict)
        if accepted:
            doc_dict = frappe._dict()
            doc_dict.receipt_document_type = doc.doctype
            doc_dict.receipt_document = doc.name
            doc_dict.supplier = doc.supplier
            doc_dict.posting_date = doc.posting_date
            doc_dict.grand_total = doc.grand_total
            purchase_receipts.append(doc_dict)

    for item in items_liens:
        items_totals.setdefault(item.item_code, 0)
        items_totals[item.item_code] += item.qty

    return purchase_receipts, items_liens, items_totals


def process_sales_rebate(doc):
    pass


def process_promotional_rebate(doc):
    pass


def get_sales_for_rebate(doc):
    pass
