const mongoose = require('mongoose');
const dns = require('dns');
dns.setServers(['8.8.8.8', '8.8.4.4']);

const connection = async () => {
    try {
        const con = await mongoose.connect(process.env.MONGO_URI)
        console.log(`mongo connect: ${con.connection.host}`)
    } catch (err) {
        console.log(err.message)
    }
}

module.exports = connection