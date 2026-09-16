const User = require('../models/UserModel');

const authAdmin = async (req, res, next) => {
    try {
        const user = await User.findById({ _id: req.user.id })
        if(user.role !== 1) return res.status(400).json({ message: 'Admin resources access denied!' })
        next()
    } catch (err) {
        return res.status(500).json({ message: err.message })
    }
}

module.exports = authAdmin