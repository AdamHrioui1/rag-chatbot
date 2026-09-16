const { GoogleGenAI } = require("@google/genai");
const Chat = require("../models/ChatModel");
const User = require("../models/UserModel");

const ChatCtrl = {
    newChat: async (req, res) => {
        try {
            let { prompt, file, mimetype } = req.body
            if(!prompt) return res.status(400).json({ success: false, message: 'Please write your propmt!' })

            const userId = req.user.id
            const chat = new Chat({ 
                user_id: userId,
                firstPrompt: {
                    prompt,
                    file,
                    mimetype
                }
            })
            await chat.save()

            let user = await User.findByIdAndUpdate({ _id: userId },
                {
                    $addToSet: {
                        chats: chat._id
                    }
                },
                { returnDocument: 'after' }
            )

            return res.status(200).json({ success: true, data: { chat, user, prompt, file, mimetype }})
        } catch (error) {
            return res.status(500).json({ success: false, message: error.message })
        }
    },
    getChat: async (req, res) => {
        try {
            let { id } = req.params
            let chat = await Chat.findById({ _id: id })
            return res.status(200).json({ success: true, data: chat })
        } catch (error) {
            return res.status(500).json({ success: false, message: error.message })
        }
    },
    updateChat: async (req, res) => {
        try {
            let { id } = req.params
            let { prompt, file = '', mimetype = '' } = req.body
            
            if(file !== undefined) file = ''
            if(mimetype !== undefined) mimetype = ''

            let currentChat = await Chat.findById({ _id: id })

            if(!currentChat) return res.status(404).json({ success: false, message: 'Chat not found!' })
            if(!prompt || prompt.length === 0) return res.status(400).json({ success: false, message: 'You can send empty message!' })
            
            // NEW: Call RAG API instead of DeepSeek directly
            async function callRAGAPI(userPrompt) {
                try {
                    // Get the access token from request headers
                    const token = req.header('Authorization');
                    
                    if (!token) {
                        throw new Error('No authorization token found');
                    }

                    // Make sure token has proper format
                    // Some libraries expect "Bearer " prefix, others don't
                    const tokenToSend = token.startsWith('Bearer ') ? token : `Bearer ${token}`;

                    // Call your RAG API. AbortSignal.timeout stops this from
                    // hanging forever (and leaving the frontend stuck on
                    // "Thinking...") if the RAG service is down or stuck.
                    //
                    // RAG_API_URL is configurable because "localhost" means
                    // something different depending on how this runs:
                    // - running directly on your machine: RAG really is at
                    //   localhost:8000, so the default below is correct.
                    // - inside Docker Compose: this container's "localhost"
                    //   is itself, not the RAG container - Compose sets
                    //   RAG_API_URL to http://rag:8000/chat instead, using
                    //   the RAG service's Compose name as its hostname.
                    const ragApiUrl = process.env.RAG_API_URL || 'http://localhost:8000/chat';
                    const response = await fetch(ragApiUrl, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': tokenToSend, // Send with Bearer prefix
                        },
                        body: JSON.stringify({
                            question: userPrompt
                        }),
                        signal: AbortSignal.timeout(45000)
                    });

                    // Debug: Log response status
                    // console.log('RAG API Response Status:', response.status);

                    if (!response.ok) {
                        const errorText = await response.text();
                        console.error('RAG API Error Response:', errorText);
                        
                        let errorMessage = 'RAG API request failed';
                        try {
                            const errorData = JSON.parse(errorText);
                            errorMessage = errorData.error?.message || errorData.detail || errorMessage;
                        } catch (e) {
                            errorMessage = errorText || errorMessage;
                        }
                        throw new Error(errorMessage);
                    }

                    const data = await response.json();
                    return data;
                } catch (error) {
                    console.error('RAG API Error:', error);
                    throw error;
                }
            }

            let ragResponse = await callRAGAPI(prompt)
            
            // Format messages to match your existing chat structure
            let messages = [
                {
                    role: "user",
                    parts: [
                        {
                            text: prompt
                        }
                    ]
                },
                {
                    role: "model",
                    parts: [
                        {
                            text: ragResponse.answer
                        }
                    ],
                    sources: ragResponse.sources || []
                }
            ]

            // Update chat with new messages
            await Chat.findOneAndUpdate({ _id: id },
                {
                    $push: {
                        history: {
                            $each: messages
                        }
                    }
                },
                {
                    returnDocument: 'after',
                }
            )

            return res.status(200).json({ 
                success: true, 
                data: { 
                    currentChat, 
                    messages,
                    sources: ragResponse.sources // Optionally return sources to frontend
                }
            })
            
        } catch (error) {
            return res.status(500).json({ success: false, message: error.message })
        }
    },
    deleteChat: async (req, res) => {
        try {
            let { id } = req.params
            const userId = req.user.id // Get the user ID from the authenticated request
            
            // Delete the chat document
            const deletedChat = await Chat.findByIdAndDelete({ _id: id })
            
            if (!deletedChat) {
                return res.status(404).json({ 
                    success: false, 
                    message: 'Chat not found!' 
                })
            }
            
            // Remove the chat reference from user's chats array
            await User.findByIdAndUpdate(
                { _id: userId },
                {
                    $pull: { chats: id } // $pull removes the chat ID from the array
                },
                { new: true } // Return the updated document (optional)
            )
            
            return res.status(200).json({ 
                success: true, 
                data: 'Chat deleted successfully!' 
            })
        } catch (error) {
            return res.status(500).json({ 
                success: false, 
                message: error.message 
            })
        }
    }
}

module.exports = ChatCtrl