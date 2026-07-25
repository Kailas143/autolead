const http = require('http');
const req = http.request('http://localhost:8081/instance/connect/supermarket_campaign', {
  method: 'GET',
  headers: {
    'apikey': '429683C4C977415CAAFCCE10F7D57E11'
  }
}, (res) => {
  let data = '';
  res.on('data', chunk => data += chunk);
  res.on('end', () => {
    const json = JSON.parse(data);
    if (json.base64) {
      const fs = require('fs');
      fs.writeFileSync('qr.html', `<img src="${json.base64}" />`);
      console.log('Saved QR code to qr.html. Open it in your browser to scan.');
    } else {
      console.log('Response:', json);
    }
  });
});
req.end();
