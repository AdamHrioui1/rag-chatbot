import React from 'react'
import orb2 from '../../assets/orb2.gif'

function CheckForPassword() {
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

                    <p>Check your email to reset your password.</p>
                </div>
            </div>
        </div>
    )
}

export default CheckForPassword