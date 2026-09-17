import axios from 'axios'
import React from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import orb2 from '../../assets/orb2.gif'
import { SERVER_API_URL } from '../../config'

function Activate() {
    let navigate = useNavigate()
    const { activationToken } = useParams()

    const handleActivate = async () => {
        try {
        const res = await axios.post(`${SERVER_API_URL}/api/v1/user/activate`, {
            activationToken: activationToken
        })

        if(res?.data?.success) return navigate('/login')

        } catch (err) {
            if(err.response.data.msg.toLowerCase() === 'jwt expired') {
                alert('Your activation key is expired! Please register again!')
            }
            console.log(err)
        }
    }

    return (
        <div className='login-container'>
            <div className="circle"></div>
            <div className="white-circle"></div>

            <div className="login-content">
                <div className="login-header">
                    <div className="logo">
                        <img width={150} src={orb2} alt="" />
                        <h2>RAG CHATBOT</h2>
                    </div>

                    <p>Click to the button bellow to activate you email</p>
                    <button onClick={handleActivate}>Activate</button>
                </div>
            </div>
        </div>
    )
}

export default Activate