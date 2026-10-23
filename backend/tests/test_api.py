import io
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_evaluation_metrics_and_live_comparison():
    response = client.get("/api/evaluation/metrics")
    assert response.status_code == 200
    payload = response.json()
    assert payload["comparison"]["status"] == "smoke_test_only"
    assert payload["comparison"]["sample_count"] == 6
    assert len(payload["comparison"]["models"]) == 2
    for model in payload["comparison"]["models"]:
        assert 0 <= model["classification"]["macro_f1"] <= 100
        assert 0 <= model["risk"]["macro_f1"] <= 100
    assert "not an independent or held-out benchmark" in payload["comparison"]["description"]

SAMPLE_CONTRACT_TXT = """
1. Definitions
Capitalized terms used in this Agreement shall have the meanings ascribed to them in Schedule A.

2. Payment Terms
Client shall remit payment within thirty (30) days of invoice date via wire transfer or ACH.

3. Limitation of Liability
In no event shall either party's liability be limited, and each party shall be fully liable for any and all direct, indirect, incidental, or consequential damages arising from this Agreement.

4. Termination for Convenience
Either party may terminate this Agreement for convenience upon fifteen (15) days written notice, without further obligation.

5. Automatic Renewal
This Agreement shall automatically renew for successive one-year terms unless either party provides written notice of non-renewal at least ninety (90) days prior to the end of the then-current term.

6. Indemnification
Contractor shall indemnify, defend, and hold harmless Client from and against any and all claims, losses, damages, liabilities, and expenses, including reasonable attorneys' fees, arising out of or related to Contractor's performance under this Agreement.
"""

def test_upload_and_analyze_workflow():
    # 1. Upload TXT contract
    file_bytes = SAMPLE_CONTRACT_TXT.encode("utf-8")
    response = client.post(
        "/api/documents/upload",
        files={"file": ("Vendor_Services_Agreement.txt", io.BytesIO(file_bytes), "text/plain")}
    )
    assert response.status_code == 201
    upload_data = response.json()
    doc_id = upload_data["document_id"]
    assert doc_id is not None
    assert upload_data["filename"] == "Vendor_Services_Agreement.txt"

    # 2. Get document metadata
    meta_resp = client.get(f"/api/documents/{doc_id}")
    assert meta_resp.status_code == 200
    assert meta_resp.json()["file_type"] == "txt"

    # 3. Start analysis
    start_resp = client.post(f"/api/analysis/{doc_id}/start?target_language=English")
    assert start_resp.status_code == 200

    # 4. Check status
    status_resp = client.get(f"/api/analysis/{doc_id}/status")
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data["status"] in ("pending", "processing", "completed")

    # If completed or once pipeline completes, fetch results
    # To test synchronously, execute pipeline directly
    from app.database.connection import SessionLocal
    from app.services.document_service import DocumentService
    db = SessionLocal()
    try:
        job = DocumentService.execute_pipeline(
            document_id=doc_id,
            target_language="English",
            source_language_pref="English",
            db=db
        )
        assert job.status == "completed"
        assert job.high_risk_count >= 1
    finally:
        db.close()

    # 5. Fetch full results
    res_resp = client.get(f"/api/analysis/{doc_id}/results")
    assert res_resp.status_code == 200
    res_data = res_resp.json()
    assert res_data["total_clauses"] >= 5
    assert len(res_data["clauses"]) >= 5
    assert res_data["overall_risk_level"] in ("medium", "high")
    assert "disclaimer" in res_data

    # 6. Fetch clauses with filter
    clauses_resp = client.get(f"/api/analysis/{res_data['analysis_id']}/clauses?risk=high")
    assert clauses_resp.status_code == 200
    high_clauses = clauses_resp.json()
    assert len(high_clauses) >= 1

    # 7. Test clause explain endpoint
    first_clause_id = res_data["clauses"][0]["id"]
    explain_resp = client.post(
        f"/api/analysis/{res_data['analysis_id']}/clauses/{first_clause_id}/explain",
        json={"preferred_language": "English", "force_llm": True}
    )
    assert explain_resp.status_code == 200
    assert "slm_explanation" in explain_resp.json()

    # 8. Test JSON export
    json_resp = client.get(f"/api/reports/{doc_id}/json")
    assert json_resp.status_code == 200
    assert "CLAUSENT_CONTRACT_ANALYSIS" in json_resp.text

    # 9. Test CSV export
    csv_resp = client.get(f"/api/reports/{doc_id}/csv")
    assert csv_resp.status_code == 200
    assert "clause_number" in csv_resp.text

    # 10. Test PDF export
    pdf_resp = client.get(f"/api/reports/{doc_id}/pdf")
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["content-type"] == "application/pdf"

    # 11. Test Document listing
    list_resp = client.get("/api/documents")
    assert list_resp.status_code == 200
    docs = list_resp.json()
    assert any(d["id"] == doc_id for d in docs)

    # 12. Clean up
    del_resp = client.delete(f"/api/documents/{doc_id}")
    assert del_resp.status_code == 200
