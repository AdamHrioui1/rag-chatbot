import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Login from './pages/Login/Login'
import Register from './pages/Register/Register'
import CheckYourEmail from './pages/CheckYourEmail/CheckYourEmail'
import Activate from './pages/Activate/Activate'
import ForgotPassword from './pages/ForgotPassword/ForgotPassword'
import CheckForPassword from './pages/CheckForPassword/CheckForPassword'
import ResetPassword from './pages/ResetPassword/ResetPassword'
import Chat from './pages/Chat/Chat'
import Documents from './pages/Documents/Documents'

function Routers() {
    return (
        <Router>
            <Routes>
                <Route path="/" element={<Login />} />
                <Route path="/new" element={<Chat newChat={true} />} />
                <Route path="/chat/:id" element={<Chat newChat={false} />} />
                <Route path="/documents" element={<Documents />} />
                <Route path="/Register" element={<Register />} />
                <Route path="/login" element={<Login />} />

                <Route path='/register' exact element={<Register />} />
                <Route path='/check' exact element={<CheckYourEmail />} />
                <Route path='/user/activate/:activationToken' exact element={<Activate />} />
                <Route path='/login' exact element={<Login />} />
                <Route path='/forgotpassword' exact element={<ForgotPassword />} />
                <Route path='/checkforpassword' exact element={<CheckForPassword />} />
                <Route path='/user/reset/:accesstoken' exact element={<ResetPassword />} />
            </Routes>
        </Router>
    )
}

export default Routers