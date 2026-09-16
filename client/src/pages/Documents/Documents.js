import React, { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { IoMdTrash } from "react-icons/io";
import { useContextApi } from '../../ContextApi';
import { listDocuments, uploadDocuments, deleteDocument } from '../../services/ragApi';
import './Documents.css'

const STATUS_LABEL = {
    processing: 'Processing...',
    ready: 'Ready',
    failed: 'Failed'
}

const formatSize = bytes => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

const formatDate = dateString => {
    return new Date(dateString).toLocaleDateString(undefined, {
        month: 'short', day: 'numeric', year: 'numeric'
    })
}

function Documents() {
    const state = useContextApi()
    const [UserCookie] = state.UserCookie
    const [DocumentsList, setDocumentsList] = useState([])
    const [Loading, setLoading] = useState(true)
    const [Uploading, setUploading] = useState(false)
    const [UploadMessages, setUploadMessages] = useState([])
    const fileInputRef = useRef(null)

    const fetchDocuments = async () => {
        if (!UserCookie) return
        try {
            const res = await listDocuments(UserCookie)
            setDocumentsList(res?.data || [])
        } catch (error) {
            console.log(error)
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        fetchDocuments()
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [UserCookie])

    // A document uploaded a moment ago may still be "processing" -
    // poll until every document has settled into "ready" or "failed",
    // so the status updates without the user needing to refresh.
    useEffect(() => {
        const hasProcessing = DocumentsList.some(doc => doc.status === 'processing')
        if (!hasProcessing) return

        const interval = setInterval(fetchDocuments, 3000)
        return () => clearInterval(interval)
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [DocumentsList])

    const handleFileChange = async e => {
        const files = Array.from(e.target.files || [])
        if (files.length === 0) return

        setUploading(true)
        setUploadMessages([])

        try {
            const res = await uploadDocuments(UserCookie, files)
            const results = res?.data?.results || []

            setUploadMessages(results.map(r => ({
                filename: r.filename,
                success: r.success,
                text: r.success ? (r.message || 'Uploaded successfully.') : r.error
            })))

            fetchDocuments()
        } catch (error) {
            setUploadMessages([{
                filename: '',
                success: false,
                text: error?.response?.data?.detail || 'Upload failed. Please try again.'
            }])
        } finally {
            setUploading(false)
            if (fileInputRef.current) fileInputRef.current.value = ''
        }
    }

    const handleDelete = async (id, filename) => {
        if (!window.confirm(`Delete "${filename}"? This cannot be undone.`)) return

        try {
            await deleteDocument(UserCookie, id)
            setDocumentsList(prev => prev.filter(doc => doc.id !== id))
        } catch (error) {
            console.log(error)
        }
    }

    return (
        <div className="documents-page">
            <div className="documents-header">
                <h2>My Documents</h2>
                <Link to="/new" className="back-to-chat-btn">Back to Chat</Link>
            </div>

            <p className="documents-subtitle">
                Upload PDF, DOCX or TXT files (or a ZIP containing them). The
                chatbot only answers questions using documents you've uploaded here.
            </p>

            <div className="upload-section">
                <label className={`upload-btn ${Uploading ? 'disabled' : ''}`}>
                    {Uploading ? 'Uploading...' : 'Upload Documents'}
                    <input
                        ref={fileInputRef}
                        type="file"
                        multiple
                        accept=".pdf,.docx,.txt,.zip"
                        hidden
                        disabled={Uploading}
                        onChange={handleFileChange}
                    />
                </label>

                {
                    UploadMessages.length > 0 &&
                    <div className="upload-results">
                        {UploadMessages.map((msg, i) => (
                            <div key={i} className={`upload-result ${msg.success ? 'success' : 'error'}`}>
                                {msg.filename ? <strong>{msg.filename}: </strong> : null}
                                {msg.text}
                            </div>
                        ))}
                    </div>
                }
            </div>

            <div className="documents-table">
                <div className="documents-table-head">
                    <span>Filename</span>
                    <span>Size</span>
                    <span>Uploaded</span>
                    <span>Status</span>
                    <span></span>
                </div>

                {
                    Loading ?
                    <div className="documents-empty">Loading...</div> :
                    DocumentsList.length === 0 ?
                    <div className="documents-empty">You haven't uploaded any documents yet.</div> :
                    DocumentsList.map(doc => (
                        <div className="documents-table-row" key={doc.id}>
                            <span className="doc-filename">{doc.filename}</span>
                            <span>{formatSize(doc.size_bytes)}</span>
                            <span>{formatDate(doc.created_at)}</span>
                            <span className={`doc-status ${doc.status}`}>
                                {STATUS_LABEL[doc.status] || doc.status}
                                {
                                    doc.status === 'failed' && doc.error_message ?
                                    <span className="doc-error" title={doc.error_message}> - {doc.error_message}</span> :
                                    null
                                }
                            </span>
                            <button className="doc-delete-btn" onClick={() => handleDelete(doc.id, doc.filename)}>
                                <IoMdTrash />
                            </button>
                        </div>
                    ))
                }
            </div>
        </div>
    )
}

export default Documents
