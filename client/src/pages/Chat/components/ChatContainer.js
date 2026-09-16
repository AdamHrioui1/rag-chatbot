import React, { useState } from 'react'
import ColorfulBg from './ColorfulBg';
import ChatHeader from './ChatHeader';
import ChatMessages from './ChatMessages';
import ChatInput from './ChatInput';

function ChatContainer(props) {
    const { newChat } = props
    const [Messages, setMessages] = useState([])
    const [Thinking, setThinking] = useState(false)
    
    return (
        <div className="chat-container">
            <div className="chat-wrapper">
                <ColorfulBg />

                <div className="chat-content">
                    <ChatHeader />
                    <ChatMessages newChat={newChat} Messages={Messages} setMessages={setMessages} Thinking={Thinking} setThinking={setThinking} />
                    <ChatInput newChat={newChat} Messages={Messages} setMessages={setMessages} Thinking={Thinking} setThinking={setThinking} />
                </div>
            </div>
        </div>
    )
}

export default ChatContainer