const User = require('../models/UserModel')
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
const sendMail = require('./SendMail');
const { isEmail } = require('validator');
const fetch = require('node-fetch');

const UserCtrl = {
    register: async (req, res) => {
        try {
            const { username, email, password } = req.body

            if(!username) return res.status(400).json({ success: false, message: 'Please enter a username!' })
            if(!email) return res.status(400).json({ success: false, message: 'Please enter a email!' })
            if(!isEmail(email)) return res.status(400).json({ success: false, message: 'Please enter a valid email!' })
            if(!password) return res.status(400).json({ success: false, message: 'Please enter a password!' })

            const user = await User.findOne({ email })
            if(user) return res.status(400).json({ success: false, message: 'This email is already exist!' })

            if(password.length < 6) return res.status(400).json({ success: false, message: 'The password must be at least 6 caracters!' })
            
            const salt = 12
            const hashedPassword = await bcrypt.hash(password, salt)

            const newUser = {
                username, email, password: hashedPassword
            }

            const activationToken = createActivationToken(newUser)
            const url = `${process.env.CLIENT_URL}/user/activate/${activationToken}`
            sendMail('activate', email, url, username)

            return res.status(200).json({ success: true, message: 'Please check your email to complet your registration!' })
        } catch (err) {
            return res.status(500).json({ success: false, message: err.message })
        }
    },
    activateEmail: async (req, res) => {
        try {
            const { activationToken } = req.body
            const user = jwt.verify(activationToken, process.env.ACTIVATION_TOKEN_SECRET)
            const { username, email, password } = user

            const check = await User.findOne({ email })
            if(check) return res.status(400).json({ success: false, message: 'This email is already exist!' })

            const newUser = new User({
                username, email, password
            })
            await newUser.save()

            return res.status(200).json({ success: true, data: newUser, message: 'You account has been activated successfully!'})
        } catch (err) {
            return res.status(500).json({ success: false, message: err.message })            
        }
    },
    login: async (req, res) => {
        try {
            const { email, password } = req.body
            if(!email) return res.status(400).json({ success: false, message: 'Please enter an email!' })
            if(!isEmail(email)) return res.status(400).json({ success: false, message: 'Please enter a valid email!' })
            if(!password) return res.status(400).json({ success: false, message: 'Please enter an password!' })

            const user = await User.findOne({ email })
            console.log('user: ', user)
            if(!user) return res.status(400).json({ success: false, message: 'This email does not exist!' })

            const isMatch = await bcrypt.compare(password, user.password)
            if(!isMatch) return res.status(400).json({ success: false, message: 'Incorrect password!' })

            const refreshtoken = createRefreshToken({ id: user._id })
            res.cookie('refreshtoken', refreshtoken, {
                httpOnly: true,
                path: '/api/v1/user/refreshtoken',
                maxAge: 1000*60*60*24*7 // 7days
            })

            const accesstoken = createAccessToken({ id: user._id })

            return res.status(200).json({ success: true, data: user, accesstoken: accesstoken, message: 'login successfully!'})
        } catch (err) {
            return res.status(500).json({ success: false, message: err.message })
        }
    },
    getAccessToken: (req, res) => {
        try {
            const { refreshtoken } = req.cookies
                if(!refreshtoken) return res.status(400).json({ success: false, message: 'Invalid authentication' })

            jwt.verify(refreshtoken, process.env.REFRESH_TOKEN_SECRET, (err, user) => {
                if(err) return res.status(400).json({ success: false, message: 'Invalid authentication' })

                const accesstoken = createAccessToken({ id: user.id })
                return res.status(200).json({ success: true, data: accesstoken })
            })
        } catch (err) {
            return res.status(500).json({ message: err.message })
        }
    },
    userInfo: async (req, res) => {
        try {
            const user = await User.findById(req.user.id).select('-password').populate('chats')
            return res.json({ success: true, data: user })
        } catch (err) {
            return res.status(500).json({ success: false, message: err.message })
        }
    },
    forgotPassword: async (req, res) => {
        try {
            const { email } = req.body

            if(!email) return res.status(400).json({ success: false, message: 'Please enter your email!' })
            if(!isEmail(email)) return res.status(400).json({ success: false, message: 'Please enter a valid email!' })
            const user = await User.findOne({ email })
            if(!user) return res.status(400).json({ success: false, message: 'This email does not exist!' })

            const accesstoken = createAccessToken({ id: user._id })
            const url = `${process.env.CLIENT_URL}/user/reset/${accesstoken}`
            
            sendMail('reset', email, url, user.username)

            return res.status(200).json({ success: true, message: 'Re-send the password. Please check your email!' })
        } catch (err) {
            return res.status(500).json({ success: false, message: err.message })
        }
    },
    resetPassword: async (req, res) => {
        try {
            const { password, confirmPassword } = req.body

            if(!password) return res.status(400).json({ success: false, message: 'Please enter a password!' })
            if(password.length < 6) return res.status(400).json({ success: false, message: 'The password should be at least 6 caracters!' })
            if(!confirmPassword) return res.status(400).json({ success: false, message: 'Please confirm your password!' })
            if(password !== confirmPassword) return res.status(400).json({ success: false, message: 'confirm password incorrect!' })
            
            const salt = 12
            const hashedPassword = await bcrypt.hash(password, salt)
            const updatedUser = await User.findByIdAndUpdate({ _id: req.user.id }, {
                password: hashedPassword
            })

            return res.json({ success: true, message: 'Your password is updated successfully!' })
        } catch (err) {
            return res.status(500).json({ success: false, message: err.message })
        }
    },
    logout: (req, res) => {
        try {
            res.clearCookie('refreshtoken', { path: '/api/v1/user/refreshtoken' })
            return res.json({ success: true, message: 'Logged out successfully!' })
        } catch (err) {
            return res.status(500).json({ success: false, message: err.message })
        }
    },
}

const createActivationToken = (payload) => {
    return jwt.sign(payload, process.env.ACTIVATION_TOKEN_SECRET, { expiresIn: '30m' })
}

const createAccessToken = (id) => {
    return jwt.sign(id, process.env.ACCESS_TOKEN_SECRET, { expiresIn: '3d' })
}

const createRefreshToken = (id) => {
    return jwt.sign(id, process.env.REFRESH_TOKEN_SECRET, { expiresIn: '7d' })
}

module.exports = UserCtrl