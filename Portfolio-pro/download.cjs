const https = require('https');
const fs = require('fs');

function download(url, dest) {
  return new Promise((resolve, reject) => {
    const file = fs.createWriteStream(dest);
    https.get(url, (response) => {
      if (response.statusCode === 301 || response.statusCode === 302) {
        return download(response.headers.location, dest).then(resolve).catch(reject);
      }
      response.pipe(file);
      file.on('finish', () => {
        file.close(resolve);
      });
    }).on('error', (err) => {
      fs.unlink(dest, () => {});
      reject(err);
    });
  });
}

async function main() {
  await download('https://picsum.photos/seed/10/1000/600', 'public/img1.jpg');
  await download('https://picsum.photos/seed/20/1000/600', 'public/img2.jpg');
  await download('https://picsum.photos/seed/30/1000/600', 'public/img3.jpg');
}

main();
