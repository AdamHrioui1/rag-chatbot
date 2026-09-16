import React, { useEffect, useRef, useState } from 'react'
import { useLocation, useNavigate, useParams } from 'react-router-dom';
import axios from 'axios';
import Markdown from 'react-markdown'
import { BiSolidFilePdf } from "react-icons/bi";
import { RiFileWord2Fill } from "react-icons/ri";
import { RiFileExcel2Fill } from "react-icons/ri";
import { PiMicrosoftPowerpointLogoFill } from "react-icons/pi";
import { useContextApi } from '../../../ContextApi';
import orb2 from "../../../assets/orb2.gif";

function ChatMessages(props) {
    const { newChat, Messages, setMessages, Thinking, setThinking } = props
    const state = useContextApi()
    const [UserCookie] = state.UserCookie
    const location = useLocation()
    const navigate = useNavigate()
    const params = useParams()
    const bottomRef = useRef(null)
    const [Key, setKey] = useState('')

    const fileIcon = (mimetype) => {
        if(mimetype === 'application/pdf') return <BiSolidFilePdf />
        else if(mimetype === 'application/msword' || mimetype === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document') return <RiFileWord2Fill />
        else if(mimetype === 'application/vnd.ms-excel' || mimetype === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet') return <RiFileExcel2Fill />
        else if(mimetype === 'application/vnd.ms-powerpoint' || mimetype === 'application/vnd.openxmlformats-officedocument.presentationml.presentation') return <PiMicrosoftPowerpointLogoFill />
    }

    let sendAndGetMessages = async () => {
        if(!newChat) {
            const previousPath = location.state?.from || '/'
            const userData = location.state?.payload

            if(previousPath === '/new' && UserCookie) {
                let userMessage = {
                    role:  'user',
                    parts: [
                        {
                            text: userData?.prompt,
                            file: userData?.file || '',
                            mimetype: userData?.mimetype || '',
                        }
                    ]
                }
                
                setMessages([userMessage])
                try {
                    setThinking(true)
                    let res = await axios.put(`http://localhost:5000/api/v1/chat/${params?.id}`, {
                        prompt: userData?.prompt, 
                        file: userData?.file || '', 
                        mimetype: userData?.mimetype || ''
                    }, {
                        headers: {
                            'Authorization': UserCookie,
                            'Content-Type': 'application/json'
                        }
                    })
                    
                    let firstMessages = res?.data?.data?.messages
                    setThinking(false)
                    setMessages(prev => [...firstMessages])

                    navigate(location.pathname, {
                        replace: true, 
                        state: { 
                            from: `/chat/${params.id}`, 
                            payload: null 
                        }
                    });
                } catch (error) {
                    setThinking(false)
                    console.log(error)
                }
            } 
            else {
                if(params?.id && UserCookie) {
                    try {
                        let res = await axios.get(`http://localhost:5000/api/v1/chat/${params?.id}`, {
                            headers: {
                                'Authorization': UserCookie,
                                'Content-Type': 'application/json'
                            }
                        })
                        
                        if(res?.data?.data?.history) {
                            let messages = res?.data?.data?.history
                            setMessages(prev => [...prev, ...messages])
                        }
                    } catch (error) {
                        console.log(error?.message)
                    }
                }
            }
        }
    }

    useEffect(() => {
        setMessages([])
        if(params.id && UserCookie) sendAndGetMessages()
    }, [params.id, UserCookie])
    
    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: "smooth" })
    }, [Messages]);

    return (
        <div className="chat-messages">
            {
                newChat ?
                <div className="welcome-message">
                    <img src={orb2} alt="" className="welcome-bg" />
                    <h3>WELCOME BACK!</h3>
                    <p>Ask me anything, and I'll do my best to help you.</p>
                </div> :
                null
            }

            {
                !newChat ?
                Messages?.map((message, index) => {
                    return (
                        <div className={`${message?.role === 'user' ? 'user' : 'bot'}-message`} key={message?.parts[0]?._id || index}>
                            {
                                message?.parts[0]?.file?.mimetype?.includes('image') ?
                                <img src={message?.parts[0]?.file?.url} alt='' /> :
                                null
                            }

                            {
                                message?.parts[0]?.file?.mimetype?.includes('application') ?
                                <div className='uploded-file'>
                                    {fileIcon(message?.parts[0]?.file?.mimetype)}
                                    <span>{message?.parts[0]?.file?.name}</span>
                                </div> :
                                null
                            }
                            
                            {
                                message?.role === 'user' ?
                                <p>{message?.parts[0]?.text}</p> :
                                <Markdown>
                                    { message?.parts[0]?.text }
                                </Markdown>
                            }

                            {
                                message?.role !== 'user' && message?.sources?.length > 0 ?
                                <details className="chat-sources">
                                    <summary>Sources ({message.sources.length})</summary>
                                    {
                                        message.sources.map((source, sourceIndex) => (
                                            <div className="chat-source" key={source?.id || sourceIndex}>
                                                <span className="chat-source-title">{source?.title}</span>
                                                <span className="chat-source-confidence">{source?.confidence}% match</span>
                                                <p className="chat-source-snippet">{source?.snippets}</p>
                                            </div>
                                        ))
                                    }
                                </details> :
                                null
                            }
                        </div>
                    )
                }) :
                null
            }

            {
                Thinking ?
                <div className="bot-message thinking" >
                    <img className='thinking-img' src={orb2} alt='' />
                    <p className='thinking'>Thinking...</p>
                </div> :
                null
            }

            <div ref={bottomRef}></div>
        </div>
    )
}

export default ChatMessages