import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import axios from 'axios'
import { useNavigate, useParams } from 'react-router-dom'
import orb2 from '../../assets/orb2.gif'

function ResetPassword() {
    const { accesstoken } = useParams()
    const navigate = useNavigate()

    const [Password, setPassword] = useState('')
    const [ConfirmPassword, setConfirmPassword] = useState('')
    const [Error, setError] = useState('')
    const [Loading, setLoading] = useState(false)
    
    const submitHandler = async e => {
        e.preventDefault()
        setLoading(true)
        try {
            if(!Password) {
                setError('Please enter your new password!')
                return setLoading(false)
            }
            if(!ConfirmPassword) {
                setError('Please confirm your password!')
                return setLoading(false)
            }
            if(Password !== ConfirmPassword) {
                setError('Password and confirm password should be the same.')
                return setLoading(false)
            }
            if(!Password || !ConfirmPassword) {
                setError('Please fill the form.')
                return setLoading(false)
            }

            await axios.post('http://localhost:5000/api/v1/user/reset', { 
                password: Password, 
                confirmPassword: ConfirmPassword 
            }, {
                headers: {
                    'Authorization': accesstoken
                }
            })
            setLoading(false)
            navigate('/login')

        } catch (err) {
            setLoading(false)
            setError(err?.response?.data?.message)
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
                    <h1>Reset Password</h1>
                    <p>Enter your new password.</p>
                </div>

                <form onSubmit={submitHandler} className="inputs-container">
                    <div className='input-container'>                        
                        <label htmlFor="password">Password</label>
                        <input name='password' id='password' type="password" placeholder='Enter new password...' value={Password} onChange={e => setPassword(e.target.value)} />
                    </div>
                    <div className='input-container'>
                        <label htmlFor="ConfirmPassword">Confirm password</label>
                        <input name='ConfirmPassword' id='ConfirmPassword' type="password" placeholder='Confirm password...' value={ConfirmPassword} onChange={e => setConfirmPassword(e.target.value)} />
                    </div>

                    {Error ? <span>{Error}</span> : null}
                    <button type='submit' style={{ opacity: !Loading ? 1 : 0.8 }} >{!Loading ? 'Reset Password' : 'Loading...'}</button>
                    <p>I don't have an account? <Link to='/register'>Sign up</Link></p>
                </form>
            </div>
        </div>
    )
}

export default ResetPassword