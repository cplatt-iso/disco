# app/services/cstore_scp.py
import os
import json
import logging
from pynetdicom import (
    AE, evt, VerificationPresentationContexts,
    StoragePresentationContexts
)
from pydicom.dataset import Dataset
from app.services.rule_engine import RuleEvaluator
from app.db import SessionLocal
from app.services import ruleset_api

CONFIG_FILE = "app/config/cstore.json"

logging.basicConfig(level=logging.INFO)

def load_config():
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Could not load config: {e}")
        return {"ae_title": "DISCO_STORESCP", "port": 11112, "storage_dir": "dicom_inbound"}

def handle_store(event, storage_dir):
    if not os.path.exists(storage_dir):
        os.makedirs(storage_dir)

    ds = event.dataset
    ds.file_meta = event.file_meta

    try:
        calling_ae = event.assoc.requestor.ae_title
        port = str(event.assoc.requestor.address)
    except Exception as e:
        logging.warning(f"Could not extract AE details: {e}")
        calling_ae = "UNKNOWN"
        port = "0"

    context = {
        "ae_title": calling_ae,
        "port": port,
    }

    db = SessionLocal()
    evaluator = RuleEvaluator(db)

    for ruleset in ruleset_api.get_all_rulesets(db):
        logging.debug(f"Evaluating ruleset {ruleset.id}: {ruleset.name}")
        evaluator.evaluate_ruleset(ruleset.id, context, ds)

    sop_instance_uid = ds.SOPInstanceUID
    out_path = os.path.join(storage_dir, f"{sop_instance_uid}.dcm")
    ds.save_as(out_path, write_like_original=False)

    db.close()
    logging.debug(f"Context received: {context}")
    logging.info(f"Stored and transformed DICOM: {out_path}")

    return 0x0000

def start_dicom_listener():
    config = load_config()
    ae_title = config.get("ae_title", "DISCO_STORESCP")
    listen_port = config.get("port", 11112)
    storage_dir = config.get("storage_dir", "dicom_inbound")

    ae = AE(ae_title=ae_title)

    for cx in StoragePresentationContexts:
        ae.add_supported_context(cx.abstract_syntax)
    for cx in VerificationPresentationContexts:
        ae.add_supported_context(cx.abstract_syntax)

    handlers = [(evt.EVT_C_STORE, lambda e: handle_store(e, storage_dir))]

    logging.info(f"Starting DICOM Listener on port {listen_port} as AE '{ae_title}'...")
    ae.start_server(("", listen_port), block=True, evt_handlers=handlers)

if __name__ == "__main__":
    start_dicom_listener()

