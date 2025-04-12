# app/services/cstore_scp.py
import os
import json
import logging
from pynetdicom import (
    AE, evt, VerificationPresentationContexts,
    StoragePresentationContexts
)
# Import the rule evaluator
from app.services.rule_engine import RuleEvaluator
# Import the database session factory
from app.db import SessionLocal
# --- Updated Import: Import CRUD module specifically and alias it ---
from app.crud import ruleset as ruleset_crud
# --- End Update ---

# Define path relative to project root or use environment variables for flexibility
CONFIG_FILE = os.getenv('CSTORE_CONFIG_PATH', 'app/config/cstore.json')

# Setup logging for this specific service
logger = logging.getLogger(__name__)
if not logger.hasHandlers(): # Avoid duplicate handlers if root logger is configured
    log_handler = logging.StreamHandler()
    log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    log_handler.setFormatter(log_formatter)
    logger.addHandler(log_handler)
    logger.setLevel(logging.INFO) # Set desired level

# --- Configuration Loading ---

DEFAULT_CONFIG = {
    "ae_title": "DISCO_STORESCP",
    "port": 11112,
    "bind_address": "0.0.0.0",        # Default bind address
    "max_pdu_size": 116794,           # Default Max PDU Size (adjust as needed)
    "storage_dir": "dicom_inbound"    # Default storage directory
}

def load_config():
    """Loads C-STORE configuration from JSON file, applying defaults for missing keys."""
    try:
        with open(CONFIG_FILE, "r") as f:
            loaded_config = json.load(f)
        config = DEFAULT_CONFIG.copy()
        config.update(loaded_config)
        logger.info(f"Successfully loaded C-STORE configuration from {CONFIG_FILE}")
        return config
    except FileNotFoundError:
        logger.warning(f"C-STORE configuration file {CONFIG_FILE} not found. Using default configuration.")
        return DEFAULT_CONFIG.copy()
    except json.JSONDecodeError:
        logger.error(f"Error decoding JSON from {CONFIG_FILE}. Using default configuration.")
        return DEFAULT_CONFIG.copy()
    except Exception as e:
        logger.error(f"Could not load C-STORE configuration from {CONFIG_FILE}: {e}. Using default configuration.", exc_info=True)
        return DEFAULT_CONFIG.copy()

# --- Event Handlers ---

def handle_store(event, storage_dir):
    """
    Handle a C-STORE request event.

    Saves the received DICOM dataset and triggers the rule engine evaluation.
    """
    logger.debug("Received C-STORE request event.")
    # Ensure storage directory exists
    try:
        os.makedirs(storage_dir, exist_ok=True)
    except OSError as e:
        logger.error(f"Could not create storage directory {storage_dir}: {e}. Aborting storage.")
        return 0xA700 # Return failure status - Refused: Out of Resources

    ds = event.dataset
    ds.file_meta = event.file_meta # Keep the file meta info

    # Extract context information
    try:
        assoc = event.assoc
        calling_ae = assoc.requestor.ae_title
        calling_host = assoc.requestor.address
        calling_port = assoc.requestor.port
    except Exception as e:
        logger.warning(f"Could not extract full association details: {e}", exc_info=True)
        calling_ae, calling_host, calling_port = "UNKNOWN", "UNKNOWN", 0

    context = {
        "calling_ae_title": calling_ae,
        "calling_host": calling_host,
        "calling_port": str(calling_port),
    }
    logger.debug(f"C-STORE Request Context: {context}")

    # Process with Rule Engine
    db = SessionLocal()
    evaluator = RuleEvaluator(db) # Assuming RuleEvaluator takes the session
    try:
        # --- Updated Ruleset Fetching using alias ---
        logger.debug("Fetching all rulesets from database...")
        all_rulesets = ruleset_crud.get_rulesets(db) # Use the alias
        # --- End Update ---

        if not all_rulesets:
             logger.info("No active rulesets found in the database to evaluate.")
        else:
            logger.info(f"Found {len(all_rulesets)} ruleset(s) to evaluate.")
            for ruleset in all_rulesets:
                logger.debug(f"Evaluating ruleset ID:{ruleset.id} Name:'{ruleset.name}'")
                evaluator.evaluate_ruleset(ruleset.id, context, ds) # Adjust if evaluator needs the full object
    except Exception as e:
        # --- Updated Error Logging ---
        # Log the specific error related to rule evaluation
        logger.error(f"Error during rule evaluation phase: {e}", exc_info=True)
        # --- End Update ---
        # Decide if this constitutes a storage failure. If evaluation is critical,
        # you might return a processing failure status code here.
        # return 0xC001 # Example: Processing Failure
    finally:
        logger.debug("Closing database session for C-STORE handler.")
        db.close() # Ensure DB session is closed

    # Save the dataset (potentially modified by rules)
    # This happens even if rule evaluation had an error, unless we explicitly returned above
    try:
        sop_instance_uid = getattr(ds, 'SOPInstanceUID', None)
        if not sop_instance_uid:
             logger.error("Received dataset missing SOPInstanceUID. Cannot generate filename.")
             return 0xA900

        safe_sop_instance_uid = str(sop_instance_uid).replace(os.sep, '_').replace('\0', '')
        out_path = os.path.join(storage_dir, f"{safe_sop_instance_uid}.dcm")

        ds.save_as(out_path, write_like_original=False)
        logger.info(f"Stored DICOM file: {out_path}")
    except AttributeError as ae:
         logger.error(f"Dataset missing required attribute for saving: {ae}", exc_info=True)
         return 0xA900
    except Exception as e:
        logger.error(f"Failed to save DICOM file to {out_path}: {e}", exc_info=True)
        return 0xC001

    # Return a success status
    logger.debug("C-STORE request handled successfully.")
    return 0x0000

# --- SCP Server ---

def start_dicom_listener():
    """Configures and starts the DICOM C-STORE SCP listener."""
    logger.info("Initializing DICOM C-STORE SCP listener...")
    config = load_config()

    # Retrieve configuration values
    ae_title = config.get("ae_title")
    listen_port = config.get("port")
    storage_dir = config.get("storage_dir")
    bind_address = config.get("bind_address")
    max_pdu_size = config.get("max_pdu_size")

    # Create and configure the Application Entity (AE)
    try:
        ae = AE(ae_title=ae_title)
        ae.maximum_pdu_size = max_pdu_size
        ae.supported_contexts = StoragePresentationContexts
        ae.supported_contexts.extend(VerificationPresentationContexts)
        handlers = [(evt.EVT_C_STORE, lambda event: handle_store(event, storage_dir))]

    except Exception as config_e:
         logger.critical(f"Failed to configure pynetdicom AE: {config_e}", exc_info=True)
         raise

    # Log the final configuration being used
    logger.info("--- Starting DICOM C-STORE SCP ---")
    logger.info(f"  AE Title:       {ae_title}")
    logger.info(f"  Listen Address: {bind_address}:{listen_port}")
    logger.info(f"  Max PDU Size:   {ae.maximum_pdu_size} bytes")
    logger.info(f"  Storage Dir:    {storage_dir}")
    logger.info("------------------------------------")

    # Start the server
    try:
        ae.start_server(
            (bind_address, listen_port),
            block=True,
            evt_handlers=handlers,
        )
        logger.info("DICOM C-STORE SCP listener stopped normally.")
    except OSError as e:
        logger.critical(f"Failed to start server on {bind_address}:{listen_port}. Error: {e}", exc_info=True)
        logger.critical("Ensure the port is not already in use and the bind address is valid.")
        raise
    except Exception as e:
        logger.critical(f"An unexpected error occurred while running the server: {e}", exc_info=True)
        raise


# --- Main execution block (for running this script directly) ---
if __name__ == "__main__":
    try:
        start_dicom_listener()
    except Exception as e:
        logger.critical(f"C-STORE SCP failed to start or crashed: {e}", exc_info=True)
        import sys
        sys.exit(1) # Exit with a non-zero status code to indicate failure
