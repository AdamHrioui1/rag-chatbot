const nodemailer = require('nodemailer');

const SendMail = async (type, to, url, name) => {
    try {
        const transport = nodemailer.createTransport({
            service: "gmail",
            auth: {
                user: process.env.SMTP_USER,
                pass: process.env.SMTP_PASS,
            },
        });

        const mailOptions = {
            from: 'user one <oneoneoneuser@gmail.com>',
            to: to,
            subject:  type === 'activate' ? 'Verify Your Email' : 'Reset Password',
            html: `${ type === 'activate' ? 
                `
                <div>
                    <h1>Verify Your Email</h1>
                    <p style="margin-bottom: 20px;">
                        Hey <strong>${name}</strong>,
                        You’re almost ready to start enjoying our website.
                        Simply click the big blue button below to verify your email address.
                    </p>
                    <a href=${url} style="padding: 10px 20px; margin: 20px 0; text-decoration: none; color: #fff; background-color: blue; border-radius: 5px;">Activate Email</a>
                    <p style="margin-top: 20px;">Or copy this url: ${url}</p>
                    <p>Once again – thank you for joining our family!</p>
                </div>`
                :
                `
                <h1>Reset Your Password</h1>
                <p style="margin-bottom: 20px;">
                    Hey <strong>${name}</strong>,
                    this is the link where you can reset your password, click the big blue button below to reset your password.
                </p>
                <a href=${url} style="padding: 10px 20px; margin: 20px 0px; text-decoration: none; color: #fff; background-color: blue; border-radius: 5px;" >Reset your password</a>
                <p style="margin-top: 20px;">Or copy this url: ${url}</p>
                <p>Once again – thank you for joining our family!</p>`
            }`
        };

        const result = await transport.sendMail(mailOptions);
        return result;
    } 
    catch (err) {
        return console.log(err.message);
    }
}

module.exports = SendMail