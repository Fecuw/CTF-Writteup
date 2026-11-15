var proxy = require('express-http-proxy');
var app = require('express')();

app.use('/', proxy('http5', {
    userResDecorator: function(proxyRes, proxyResData, userReq, userRes) {
        // Replace html contents to censor flags!
        return String(proxyResData).replaceAll(/katagaitai-CTF\{.*\}/g, "[censored]");
    }})
);

app.listen(80)