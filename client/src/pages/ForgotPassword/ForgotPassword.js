import axios from 'axios'
import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import orb2 from '../../assets/orb2.gif'

function ForgotPassword() {
    let navigate = useNavigate()
    const [Email, setEmail] = useState('')
    const [Error, setError] = useState('')

    const handleSubmit = async e => {
        e.preventDefault()

        try {
            if(!Email) return setError('Please enter your Email!')

            await axios.post('http://localhost:5000/api/v1/user/forgot', {
                email: Email
            })
            navigate('/checkforpassword')

        } catch (err) {
            setError(err?.response?.data.message)
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
                    <h1>Reset Your Password</h1>
                    <p>Enter your Email to reset your password.</p>
                </div>

                <form onSubmit={handleSubmit} className="inputs-container">
                    <div className='input-container'>
                        <label>Email</label>
                        <input type='Email' onChange={e => setEmail(e.target.value)} value={Email} pattern="[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$" placeholder='eg. adam@gmail.com' />
                    </div>

                    {Error ? <span>{Error}</span> : null}

                    <button type='submit'>Reset Password</button>
                </form>
            </div>
        </div>
    )
}

export default ForgotPassword