require('dotenv').config({ quiet: true }) // suppress dotenv's promotional console "tips"
const express = require('express');
const cors = require('cors');
const cookieParser = require('cookie-parser');
const connection = require('./database/connection');

const app = express()
app.use(express.json())
app.use(express.urlencoded({ extended: true }));
app.use(cors())
app.use(cookieParser())

app.use('/api/v1/user', require('./routes/UserRoutes'))
app.use('/api/v1/chat', require('./routes/ChatRoutes'))
app.use('/api/v1/file', require('./routes/Cloudinary'))

connection()

let PORT = process.env.PORT || 8080
app.listen(PORT, () => console.log(`Server is listening on port: http://localhost:${PORT}`))