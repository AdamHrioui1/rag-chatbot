import React from 'react'
import './Chat.css'
import ChatsSidebar from './components/ChatsSidebar';
import ChatContainer from './components/ChatContainer';
import { useContextApi } from '../../ContextApi';

function Chat(props) {
    const { newChat } = props
    let state = useContextApi()
    let [HideSidebar] = state.HideSidebar

    return (
        <div className={`home-container  ${HideSidebar ? 'full' : null}`} >
            <ChatsSidebar />
            <ChatContainer newChat={newChat} />
        </div>
    )
}

export default Chat