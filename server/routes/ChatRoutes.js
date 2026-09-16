const ChatCtrl = require('../controllers/ChatCtrl')
const auth = require('../middleware/auth')

let router = require('express').Router()

router.post('/new', auth, ChatCtrl.newChat)
router.get('/:id', auth, ChatCtrl.getChat)
router.put('/:id', auth, ChatCtrl.updateChat)
router.delete('/:id', auth, ChatCtrl.deleteChat)

module.exports = router