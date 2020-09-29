
const facemesh = require('@tensorflow-models/facemesh'),
  tf = require('@tensorflow/tfjs-core'),
  pixels = require('image-pixels'),
  sharp = require('sharp'),
  http = require('http'),
  urllib = require('url');

// WebAssembly backend seems fastest for the mobile/web focused code.
require("@tensorflow/tfjs-backend-wasm");

// Need CUDA 10 drivers for GPU backend.
// This may not work at all - some functions used in facemesh may
// not have an implementation in the node GPU backend.
// require("@tensorflow/tfjs-node-gpu");

// Simple webserver to receive image data and return keypoint result as JSON.
async function serve() {

  // Needs to match the loaded backend.
  await tf.setBackend('wasm');

  console.log("Loading FaceMesh model ...");
  const model = await facemesh.load();
  console.log("FaceMesh model loaded. Serving on port 8080.");

  http.createServer((request, response) => {
    const { headers, method, url } = request;
    let body = [];
    request.on('error', (err) => {
      console.error(err);
    }).on('data', (chunk) => {
      // Body content of POST should be image data interpretable
      // by sharp/image-pixels.
      body.push(chunk);
    }).on('end', async () => {
      var predictions;
      try {
        var hrstart = process.hrtime();
        const stream = Buffer.concat(body);
        const queryObject = urllib.parse(request.url,true).query;
        console.log(queryObject);
        const resizeWidth = parseInt(queryObject.resizeWidth);
        // const data = await sharp(stream)
        //   .resize({ width: resizeWidth })
        //   .toBuffer();
        const img = await pixels(stream, {shape: [640, 480]});
        predictions = await model.estimateFaces(img);
        hrend = process.hrtime(hrstart);
        console.info('Execution time: %ds %dms', hrend[0], hrend[1] / 1000000);
      } catch (err) {
        console.error(err);
        response.statusCode = 400;
        response.setHeader('Content-Type', 'application/json');
        response.write("");
        response.end();
        return;
      }

      // Log errors.
      // Is this needed?? What's the difference between error callback and try-catch?
      response.on('error', (err) => {
        console.error(err);
      });

      // Formulate a good response if no errors.
      // Response is just a json encoded model result.
      response.statusCode = 200;
      response.setHeader('Content-Type', 'application/json');
      response.write(JSON.stringify(predictions));
      response.end();

    });
  }).listen(8080);
}

serve();
