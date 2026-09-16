const UserCtrl = require('../controllers/UserCtrl')
const router = require('express').Router()
const auth = require('../middleware/auth')

router.post('/register', UserCtrl.register)
router.post('/activate', UserCtrl.activateEmail)
router.post('/login', UserCtrl.login)
router.get('/refreshtoken', UserCtrl.getAccessToken)
router.get('/info', auth, UserCtrl.userInfo)
router.post('/forgot', UserCtrl.forgotPassword)
router.post('/reset', auth, UserCtrl.resetPassword)
router.get('/logout', UserCtrl.logout)

module.exports = router