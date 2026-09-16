import React from 'react'
import { TbLayoutSidebarLeftExpandFilled } from "react-icons/tb";
import { CgProfile } from "react-icons/cg";
import orb2 from "../../../assets/orb2.gif";
import { useContextApi } from '../../../ContextApi';

function ChatHeader() {
    let state = useContextApi()
    let [HideSidebar] = state.HideSidebar
    let hideSidebarHandler = state.hideSidebarHandler

    return (
        <div className="chat-header">
            <button className={`show-sidebar-btn ${HideSidebar ? 'visible' : 'hidden'}`} onClick={hideSidebarHandler}>
                <TbLayoutSidebarLeftExpandFilled />
            </button>

            <div className={`jeremy-logo ${HideSidebar ? 'center' : 'left'}`}>
                <img width={40} src={orb2} alt="" className="" />
                <h2>RAG CHATBOT</h2>
            </div>
            
            <button className="profile-btn">
                <CgProfile />
            </button>
        </div>
    )
}

export default ChatHeader