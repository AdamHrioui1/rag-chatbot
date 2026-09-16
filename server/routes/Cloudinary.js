const router = require('express').Router()
const cloudinary = require('cloudinary');
const fs = require('fs');
const auth = require('../middleware/auth');
const adminAuth = require('../middleware/adminAuth');

cloudinary.config({
    cloud_name: process.env.CLOUD_NAME,
    api_key: process.env.CLOUD_API_KEY,
    api_secret: process.env.CLOUD_API_SECRET 
})

router.post('/upload', auth, adminAuth, async (req, res) => {
    try {
        const { files } = req.files

        console.log('req.files: ', req.files)

        if(!req.files || files.length === 0 || Object.keys(files).length === 0 || files === null)
            return res.status(400).json({ message: "No file uploaded!" })

        var filesSize = 0
        if(files.length === undefined && Object.keys(files).length !== 0) {
            if(files.size > 1 * 1024 * 1024) {
                removeTempFile(files.tempFilePath)
                return res.status(400).json({ message: 'File is too large!' })
            }
            
            if(files.mimetype !== 'image/png' && files.mimetype !== 'image/jpeg' && files.mimetype !== 'image/webp' && files.mimetype !== 'image/svg+xml') {
                removeTempFile(files.tempFilePath)
                return res.status(400).json({ message: 'File type not supported!' })
            }

            cloudinary.v2.uploader.upload(files.tempFilePath, { folder: 'ecommerce_Shoes'}, (err, result) => {
                removeTempFile(files.tempFilePath)
                if(err) throw err

                return res.status(200).json({
                    public_id: result.public_id,
                    secure_url: result.secure_url
                })
            })
        }
        else {
            console.log('files: ', files)
            files.forEach(f => {
                filesSize += f.size
            });
    
            if(filesSize > 10 * 1024 * 1024)
                return res.status(400).json({ message: "Files size is too big" })
    
            var matchedFiles = []
            matchedFiles.forEach(f => {
                tempfilesPaths.push(f.tempFilePath)
                // removeTempFile(f.tempFilePath)
            })
    
            files.forEach(f => {
                if(f.mimetype === 'image/png' || f.mimetype === 'image/jpeg' || f.mimetype === 'image/webp' || f.mimetype === 'image/svg+xml') {
                    matchedFiles.push(f)
                }
                // removeTempFile(f.tempFilePath)
            })
    
            var uploadedFiles = [] 
            const uploader = async (path) => await cloudinary.v2.uploader.upload(path, { folder: "ecommerce_Shoes" });
    
            for (const file of matchedFiles) {
                const respons = await uploader(file.tempFilePath)
                uploadedFiles.push({
                    public_id: respons.public_id,
                    secure_url: respons.secure_url
                })
            }
    
            files.forEach(f => {
                removeTempFile(f.tempFilePath)
            })
    
            return res.json({ uploadedFiles: uploadedFiles })    
        }
    } catch (err) {
        console.log(err)
        return res.status(500).json({ message: err.message })
    }
})

router.post('/destroy', auth, adminAuth, (req, res) => {
    try {
        const { public_id } = req.body

        if(!public_id) return res.status(400).json({ message: "No file selected!" })

        cloudinary.v2.uploader.destroy(public_id, (err, result) => {
            if(err) throw err

            return res.status(200).json({ message: "File deleted successfuly!" })
        })
        
    } catch (err) {
        return res.status(500).json({ message: err.message })
    }
})

const removeTempFile = (path) => {
    fs.unlink(path, err => {
        if(err) throw err
    })
}

module.exports = router