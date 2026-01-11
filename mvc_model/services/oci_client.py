import oci
doc_client = None
def get_doc_client():# pragma: no cover
    global doc_client
    if doc_client is None:
        config = oci.config.from_file()
        doc_client = oci.ai_document.AIServiceDocumentClient(config)
    return doc_client