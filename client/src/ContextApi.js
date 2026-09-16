import axios from "axios";
import { createContext, useContext, useEffect, useState } from "react";
import Cookies from "universal-cookie";

export let ContextApi = createContext()

export let ContextProvider = ({ children }) => {
    const [HideSidebar, setHideSidebar] = useState(false)
    const [UserCookie, setUserCookie] = useState('')
    const [User, setUser] = useState('')
    const [Chats, setChats] = useState([])
    const [CallBack, setCallBack] = useState(false)

    const cookies = new Cookies(null, { path: '/' })

    useEffect(() => {
        let cookie = cookies.get('accesstoken')
        if(cookie && cookie.length > 170) {
            setUserCookie(cookie)

            let getUser = async () => {
                try {
                    let res = await axios.get('http://localhost:5000/api/v1/user/info', {
                        headers: {
                            'Authorization': cookie
                        }
                    })
                    setUser(res?.data?.data)
                    setChats(res?.data?.data?.chats?.reverse())
                } catch (error) {
                    console.log(error)
                }
            }
            getUser()
        }
        // `cookies` is a new instance every render (not memoized), so
        // adding it here would re-run this effect on every render
        // instead of only when CallBack changes - intentional omission.
    }, [CallBack]) // eslint-disable-line react-hooks/exhaustive-deps

    let hideSidebarHandler = () => setHideSidebar(!HideSidebar)
    
    let state = {
        HideSidebar: [HideSidebar, setHideSidebar],
        hideSidebarHandler: hideSidebarHandler,
        UserCookie: [UserCookie, setUserCookie],
        User: [User, setUser],
        Chats: [Chats, setChats],
        CallBack: [CallBack, setCallBack]
    }

    return (
        <ContextApi.Provider value={state}>
            {children}
        </ContextApi.Provider>
    )
}

export let useContextApi = () => useContext(ContextApi)