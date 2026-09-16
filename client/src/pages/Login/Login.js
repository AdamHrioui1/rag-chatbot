import { useState } from 'react'
import axios from 'axios'
import Cookies from 'universal-cookie'
import { Link, useNavigate } from 'react-router-dom'
import orb2 from '../../assets/orb2.gif'
import './Login.css'

function Login() {
    const [Error, setError] = useState('')
    const [Email, setEmail] = useState('')
    const [Password, setPassword] = useState('')
    const [Loading, setLoading] = useState(false)
    const navigate = useNavigate();

    let submitHandler = async e => {
        e.preventDefault()
        setLoading(true)

        try {
            let res = await axios.post('http://localhost:5000/api/v1/user/login', {
                email: Email,
                password: Password
            })
            
            const cookies = new Cookies(null, { path: '/', maxAge: 1*60*60*24*3 })
            cookies.set('accesstoken', res.data.accesstoken)
            
            setLoading(false)
            navigate('/new', { state: { from: '/login' } })
        } catch (error) {
            setLoading(false)
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
                    <h1>Sign In Account</h1>
                    <p>Enter your personal data to create your account.</p>
                </div>

                <form onSubmit={submitHandler} className="inputs-container">
                    <div className='input-container'>
                        <label>Email</label>
                        <input type='email' placeholder='eg. adam@gmail.com' onChange={e => setEmail(e.target.value)} value={Email} />
                    </div>
                    <div className='input-container'>
                        <label>Password</label>
                        <input type='password' placeholder='Enter your password' onChange={e => setPassword(e.target.value)} value={Password} />
                        <Link to={'/forgotpassword'}>Forgot password?</Link>
                    </div>

                    {Error ? <span>{Error}</span> : null}
                    <button type='submit' style={{ opacity: !Loading ? 1 : 0.8 }} >{!Loading ? 'Sign In' : 'Loading...'}</button>
                    <p>I don't have an account? <Link to='/register'>Sign up</Link></p>
                </form>
            </div>
        </div>
    )
}

export default Login