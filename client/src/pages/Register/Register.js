import { useState } from 'react'
import { Link } from 'react-router-dom'
import orb2 from '../../assets/orb2.gif'
import axios from 'axios'
import { SERVER_API_URL } from '../../config'

function Register() {
    const [Error, setError] = useState('')
    const [Username, setUsername] = useState('')
    const [Email, setEmail] = useState('')
    const [Password, setPassword] = useState('')

    let submitHandler = async e => {
        e.preventDefault()
        try {
            let res = await axios.post(`${SERVER_API_URL}/api/v1/user/register`, {
                username: Username,
                email: Email, 
                password: Password,
            })
            
            if(res.data.success) window.location.href = '/check'
        } catch (error) {
            console.log(error?.response?.data?.message)
            setError(error?.response?.data?.message)
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
                    <h1>Sign Up Account</h1>
                    <p>Enter your personal data to create your account.</p>
                </div>

                <form onSubmit={submitHandler} className="inputs-container">
                    <div className='input-container'>
                        <label>Username</label>
                        <input onChange={e => setUsername(e.target.value)} value={Username} type='text' placeholder='eg. Adam' />
                    </div>
                    <div className='input-container'>
                        <label>Email</label>
                        <input onChange={e => setEmail(e.target.value)} value={Email} type='email' placeholder='eg. adam@gmail.com' />
                    </div>
                    <div className='input-container'>
                        <label>Password</label>
                        <input onChange={e => setPassword(e.target.value)} value={Password} type='password' placeholder='Enter your password' />
                    </div>

                    {Error ? <span>{Error}</span> : null}
                    <button>Sign in</button>
                    <p>I already have an account? <Link to='/login'>Sign in</Link></p>
                </form>
            </div>
        </div>
    )
}

export default Register