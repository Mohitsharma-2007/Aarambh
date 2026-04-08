"""routers/documents.py — Document parsing endpoints"""
from fastapi import APIRouter, Query, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from parsers.document_parser import parse_from_url, parse_bytes, classify_document
from typing import Optional

router = APIRouter()

@router.get("/parse", summary="Parse document from URL (PDF, Excel, CSV, JSON, XML, HTML)")
async def parse_url(
    url: str = Query(..., description="Document URL to fetch and parse"),
    ai_analyze: bool = Query(False, description="Run AI analysis on parsed content"),
):
    """
    Fetch and parse any document from a URL.
    Supports: PDF, XLSX/XLS, CSV, JSON, XML, DOCX, PPTX, HTML
    Also handles: Circulars, Notices, Press Releases, Reports, Datasets
    """
    result = await parse_from_url(url)
    if ai_analyze and result.get("status") == "parsed":
        from scrapers.ai_engine import analyze_document
        result["ai_analysis"] = await analyze_document(result)
    return result


@router.post("/upload", summary="Upload and parse a document file")
async def upload_file(
    file: UploadFile = File(...),
    ai_analyze: bool = Query(False, description="Run AI analysis"),
):
    """
    Upload and parse a document.
    Supported formats: PDF, XLSX, XLS, CSV, JSON, XML, DOCX, DOC, PPTX, HTML, TXT
    """
    data     = await file.read()
    filename = file.filename or "upload"
    result   = parse_bytes(data, filename, source=filename)

    if ai_analyze and result.get("status") == "parsed":
        from scrapers.ai_engine import analyze_document
        result["ai_analysis"] = await analyze_document(result)
    return result


@router.post("/upload-batch", summary="Upload multiple documents at once")
async def upload_batch(files: list[UploadFile] = File(...)):
    """Parse multiple documents in one request."""
    results = []
    for file in files[:10]:   # cap at 10
        data   = await file.read()
        result = parse_bytes(data, file.filename or "upload", source=file.filename)
        results.append({"filename": file.filename, **result})
    return {"count": len(results), "documents": results}


@router.get("/pib-doc", summary="Fetch and parse a PIB press release")
async def pib_doc(
    url: str = Query(..., description="PIB document URL"),
    ai_analyze: bool = Query(True),
):
    """Fetch and parse a PIB document with optional AI analysis."""
    from scrapers.pib_scraper import get_document
    doc = await get_document(url)
    if ai_analyze:
        from scrapers.ai_engine import analyze_document
        # Wrap PIB doc into document parser format
        fake_doc = {
            "text":   doc.get("body",""),
            "title":  doc.get("title",""),
            "type":   "HTML",
            "source": url,
            "status": "parsed",
        }
        doc["ai_analysis"] = await analyze_document(fake_doc)
    return doc


@router.get("/rbi-circular", summary="Fetch and parse an RBI circular/notification")
async def rbi_circular(
    url: str = Query(..., description="RBI document URL"),
    ai_analyze: bool = Query(True),
):
    """Parse an RBI circular or notification from URL."""
    result = await parse_from_url(url)
    if ai_analyze and result.get("status") == "parsed":
        from scrapers.ai_engine import analyze_document
        result["ai_analysis"] = await analyze_document(result, focus="monetary policy, banking regulation")
    return result


@router.get("/types", summary="All supported document types")
async def doc_types():
    return {
        "structured_formats": {
            "CSV":  "Comma-separated data → rows + columns extracted",
            "JSON": "JSON data → flattened + schema detected",
            "XML":  "XML feeds → element tree extracted",
            "XLSX": "Excel spreadsheets → all sheets as tables",
            "XLS":  "Legacy Excel → all sheets as tables",
        },
        "unstructured_formats": {
            "PDF":  "Full text extraction + table detection (PyMuPDF)",
            "DOCX": "Word documents → paragraphs + tables",
            "DOC":  "Legacy Word → text extraction",
            "PPTX": "PowerPoint → slide-by-slide text",
            "HTML": "Web pages → cleaned text + tables",
            "TXT":  "Plain text files",
        },
        "document_classes": {
            "Press Release":    "PIB / ministry announcements",
            "Circular":         "RBI / SEBI / ministry circulars",
            "Notice":           "Public notices, tender notices",
            "Scheme":           "Government scheme notifications",
            "Policy":           "Policy documents and white papers",
            "Report":           "Annual reports, survey reports",
            "Budget":           "Budget documents and statements",
            "MoU/Agreement":    "International agreements",
            "Data/Statistics":  "Statistical releases",
        },
        "ai_capabilities": {
            "document_analysis":  "Summarize + classify + extract key facts",
            "data_insights":      "Trend detection + risk + opportunity identification",
            "comparison":         "Compare two indicators or documents",
            "custom_analysis":    "Any task: summarize / classify / sentiment / translate",
        }
    }
