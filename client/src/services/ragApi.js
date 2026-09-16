import axios from "axios";

// The FastAPI RAG service lives on its own host/port and is called
// directly from the browser for document management, the same way
// axios already calls the Node server directly for chat/auth.
const RAG_API_URL = process.env.REACT_APP_RAG_API_URL || "http://localhost:8000";

export const listDocuments = (userCookie) => {
    return axios.get(`${RAG_API_URL}/documents`, {
        headers: { Authorization: userCookie }
    });
};

export const uploadDocuments = (userCookie, files) => {
    const formData = new FormData();
    for (const file of files) {
        formData.append("files", file);
    }

    return axios.post(`${RAG_API_URL}/documents/upload`, formData, {
        headers: {
            Authorization: userCookie,
            "Content-Type": "multipart/form-data"
        }
    });
};

export const deleteDocument = (userCookie, documentId) => {
    return axios.delete(`${RAG_API_URL}/documents/${documentId}`, {
        headers: { Authorization: userCookie }
    });
};
