import React, { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom';
import axios from 'axios';
import { RiSendPlaneFill } from "react-icons/ri";
import { FaSquare } from "react-icons/fa6";
import { useContextApi } from '../../../ContextApi';
import { SERVER_API_URL } from '../../../config';

function ChatInput(props) {
    const { newChat, setMessages, Thinking, setThinking } = props
    const state = useContextApi()
    const [UserCookie] = state.UserCookie
    const [CallBack, setCallBack] = state.CallBack
    const [Prompt, setPrompt] = useState('')
    const [File] = useState('')
    const [Mimetype] = useState('')
    const navigate = useNavigate();
    const params = useParams()

    const submitHandler = async e => {
        e.preventDefault()
        
        const userMessage = {
            role:  'user',
            parts: [
                {
                    text: Prompt
                }
            ]
        }
        
        setMessages(prev => [...prev, userMessage])

        if(newChat) {
            if(UserCookie) {
                try {
                    setThinking(true)
                    const res = await axios.post(`${SERVER_API_URL}/api/v1/chat/new`, {
                        prompt: Prompt, 
                        file: File, 
                        mimetype: Mimetype
                    }, {
                        headers: {
                            'Authorization': UserCookie,
                            'Content-Type': 'application/json'
                        }
                    })
                    
                    const userPayload = res?.data?.data
                    setThinking(false)
                    setPrompt('')
                    setCallBack(!CallBack)
    
                    navigate(`/chat/${res?.data?.data?.chat?._id}`, { 
                        state: { 
                            from: '/new',
                            payload: userPayload
                        } 
                    });
                } catch (error) {
                    console.log(error)
                }
            }
        }
        else {
            const prompt = Prompt
            setPrompt('')

            if(params.id && UserCookie) {
                try {
                    setThinking(true)
                    const res = await axios.put(`${SERVER_API_URL}/api/v1/chat/${params?.id}`, {
                        prompt: prompt,
                        file: '', 
                        mimetype: ''
                    }, {
                        headers: {
                            'Authorization': UserCookie,
                            'Content-Type': 'application/json'
                        }
                    })
                    
                    setThinking(false)
    
                    if(res?.data?.success) {
                        setMessages(prev => [...prev, res?.data?.data?.messages[1]])
                    }
                } catch (error) {
                    console.log(error)
                }
            }
        }
    }

    return (
        <div className="chat-input">
            {/* <div className='uploaded-img'>
                <button className='delete-img-btn'>
                    <TiDelete />
                </button>
                <img src={img} alt='' />
            </div> */}

            <form className='chat-input-items' onSubmit={submitHandler}>
                {/* <div className="attach-file">
                    <label htmlFor="attachment">
                        <RiAttachment2 />
                    </label>
                    <input type="file" hidden name="attachment" id="attachment" />
                </div> */}

                <input onChange={e => setPrompt(e.target.value)} value={Prompt} type="text" placeholder="Ask me anything..." />

                <button className="send-btn" type='submit' disabled={Thinking ? true : false}>
                    {
                        Thinking ?
                        <div className='square'>
                            <FaSquare />
                        </div> :
                        <RiSendPlaneFill />
                    }
                </button>
            </form>
        </div>
    )
}

export default ChatInput