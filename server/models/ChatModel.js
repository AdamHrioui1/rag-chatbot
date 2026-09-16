const mongoose = require('mongoose')

const ChatSchema = new mongoose.Schema({
    user_id: {
        type: String,
        required: true
    },
    firstPrompt: {
        type: Object
    },
    history: [{
        _id: Number,
        role: String,
        parts: [{
            text: String,
            file: {
                url: String,
                mimetype: String
            }
        }],
        sources: [{
            id: String,
            title: String,
            snippets: String,
            confidence: Number
        }]
    }]
}, {
    timestamps: true
})

const Chat = mongoose.model('Chat', ChatSchema)

module.exports = Chat