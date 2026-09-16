import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { LuMessageCirclePlus } from "react-icons/lu";
import { HiOutlineDocumentText } from "react-icons/hi";
import { FiSearch } from "react-icons/fi";
import { TbLayoutSidebarLeftCollapseFilled } from "react-icons/tb";
import { HiOutlineLogout } from "react-icons/hi";
import orb2 from "../../../assets/orb2.gif";
import { useContextApi } from '../../../ContextApi';
import Cookies from 'universal-cookie';
import axios from 'axios';
import { IoMdTrash } from "react-icons/io";

function ChatsSidebar() {
    let state = useContextApi()
    let [HideSidebar, setHideSidebar] = state.HideSidebar
    let [UserCookie] = state.UserCookie
    let hideSidebarHandler = state.hideSidebarHandler
    let [User] = state.User
    const [Chats, setChats] = state.Chats
    const [CallBack, setCallBack] = state.CallBack
    const [windowWidth, setWindowWidth] = useState(window.innerWidth);

    const cookies = new Cookies(null, { path: '/' })

    let deleteChatHandler = async id => {
        if(window.confirm('Are you sure you want to delete this chat?')) {
            try {
                let res = await axios.delete(`http://localhost:5000/api/v1/chat/${id}`, {
                    headers: {
                        'Authorization': UserCookie,
                        'Content-Type': 'application/json'
                    }
                })
                
                setCallBack(!CallBack)
            } catch (error) {
                console.log(error);
            }
        }
    }
    
    let logout = () => {
        cookies.remove('accesstoken')
        window.location.href = '/login'
    }

    useEffect(() => {
        let timeoutId = null;

        const handleResize = () => {
            clearTimeout(timeoutId)
            timeoutId = setTimeout(() => {
                window.innerWidth < 768 ? setHideSidebar(true) : setHideSidebar(false)
            }, 150);
        };
        
        handleResize()

        window.addEventListener('resize', handleResize);
        return () => {
            window.removeEventListener('resize', handleResize);
            clearTimeout(timeoutId);
        };
    }, []);

    return (
        <div className={`sidebar ${HideSidebar ? 'inactive' : 'active'}`}>
            <div className="sidebar-top">
                <img src={orb2} alt="" />
                <span className="logo-name">RAG CHATBOT</span>
                {/* <button className="search-btn">
                    <FiSearch />
                </button> */}
                <button className="hide-sidebar-btn" onClick={hideSidebarHandler}>
                    <TbLayoutSidebarLeftCollapseFilled />
                </button>
            </div>

            <div className="new-chat-btn-container">
                <Link to={'/new'} className="new-chat-btn">
                    <LuMessageCirclePlus />
                    New Chat
                </Link>
                <div className="white-bg"></div>
            </div>

            <div className="new-chat-btn-container">
                <Link to={'/documents'} className="new-chat-btn">
                    <HiOutlineDocumentText />
                    My Documents
                </Link>
            </div>

            <span>YOUR CHATS</span>

            <div className="chats-history">
                {
                    Chats?.map(chat => {
                        return (
                            <div className="chat-link" key={chat?._id}>
                                <Link to={`/chat/${chat?._id}`} className="chat-link">
                                    {
                                        chat?.history[0]?.parts?.[0]?.text.length >= 20 ?
                                        chat?.history[0]?.parts?.[0]?.text.slice(0, 20) + '...' :
                                        chat?.history[0]?.parts?.[0]?.text
                                    }
                                </Link>
                                <button onClick={() => deleteChatHandler(chat?._id)}>
                                    <IoMdTrash />
                                </button>
                            </div>
                        )
                    })
                }
            </div>

            <button className="profile-btn" onClick={logout}>
                <HiOutlineLogout />
                <span>Logout</span>
            </button>
        </div>
    )
}

export default ChatsSidebar