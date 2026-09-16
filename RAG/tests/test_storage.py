from unittest.mock import patch

import pytest

from app.services import storage

USER_ID = "user123"


@patch("app.services.storage._s3_client")
def test_save_file_uploads_to_s3_under_generated_key(mock_s3, ):
    key = storage.save_file(USER_ID, "resume.pdf", b"file content")

    assert key.startswith(f"{USER_ID}/")
    assert key.endswith(".pdf")
    # the original filename must never appear in the stored key - only
    # its extension does
    assert "resume" not in key

    mock_s3.put_object.assert_called_once()
    _, kwargs = mock_s3.put_object.call_args
    assert kwargs["Key"] == key
    assert kwargs["Body"] == b"file content"


@patch("app.services.storage._s3_client")
def test_save_file_rejects_invalid_user_id(mock_s3):
    with pytest.raises(ValueError):
        storage.save_file("../escape", "resume.pdf", b"content")

    mock_s3.put_object.assert_not_called()


@patch("app.services.storage._s3_client")
def test_delete_file_calls_s3_delete_object(mock_s3):
    storage.delete_file("user123/abcd1234.pdf")

    mock_s3.delete_object.assert_called_once()
    _, kwargs = mock_s3.delete_object.call_args
    assert kwargs["Key"] == "user123/abcd1234.pdf"


@patch("app.services.storage._s3_client")
def test_delete_file_does_not_raise_on_s3_error(mock_s3):
    from botocore.exceptions import ClientError

    mock_s3.delete_object.side_effect = ClientError(
        {"Error": {"Code": "InternalError", "Message": "boom"}}, "DeleteObject"
    )

    # Should log and swallow the error, not propagate it - a delete
    # failure here shouldn't block the rest of document cleanup.
    storage.delete_file("user123/abcd1234.pdf")
